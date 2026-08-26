from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from django.utils import timezone
from audit.models import AuditLog
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import IsAuthorizedStaff, IsSchoolAdmin
from academics.models import AcademicYear
from common.audit import AuditMixin
from common.drf_filters import RoleScopedViewsetMixin
from .holiday_import import PhilippineHolidayImportService
from .models import AttendanceRecord, RecurringSchoolCalendarEvent, SchoolCalendarDay
from .recurrence import generate_occurrences
from .serializers import AttendanceRecordSerializer, RecurringSchoolCalendarEventSerializer, SchoolCalendarDaySerializer


class AttendanceRecordViewSet(RoleScopedViewsetMixin, AuditMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    scope_field = 'enrollment'
    queryset = AttendanceRecord.objects.select_related('enrollment', 'encoded_by').all()
    serializer_class = AttendanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorizedStaff]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['month', 'enrollment', 'enrollment__student', 'encoded_by', 'attendance_date']
    search_fields = ['enrollment__student__first_name', 'enrollment__student__last_name', 'month', 'attendance_date']
    ordering_fields = ['created_at', 'school_days', 'days_present', 'absences', 'attendance_date']
    ordering = ['-created_at']


class SchoolCalendarDayViewSet(AuditMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = SchoolCalendarDay.objects.select_related('academic_year', 'section', 'affected_grade_level', 'created_by', 'authorized_by').all()
    serializer_class = SchoolCalendarDaySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['academic_year', 'day_type', 'attendance_expected', 'classes_suspended', 'scope_type', 'section', 'calendar_date']
    search_fields = ['title', 'remarks', 'reason', 'day_type', 'status', 'location']
    ordering_fields = ['calendar_date', 'day_type', 'created_at']
    ordering = ['calendar_date']

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return [permissions.IsAuthenticated(), IsSchoolAdmin()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        self._audit('CREATE', instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self._audit('UPDATE', instance)

    def _audit(self, action, instance):
        AuditLog.objects.create(
            user=self.request.user, action=action, module='attendance',
            object_type='SchoolCalendarDay', object_id=str(instance.pk),
        )

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        instance = self.get_object()
        if instance.status == 'CANCELLED':
            return Response({'detail': 'Cancelled entries cannot be published.'}, status=400)
        instance.status = 'PUBLISHED'
        instance.published_at = timezone.now()
        instance.authorized_by = request.user
        instance.save(update_fields=['status', 'published_at', 'authorized_by', 'updated_at'])
        self._audit('PUBLISHED', instance)
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        instance = self.get_object()
        reason = str(request.data.get('cancellation_reason') or '').strip()
        if not reason:
            return Response({'cancellation_reason': ['Cancellation reason is required.']}, status=400)
        instance.status = 'CANCELLED'
        instance.cancellation_reason = reason
        instance.save(update_fields=['status', 'cancellation_reason', 'updated_at'])
        self._audit('CANCELLED', instance)
        return Response(self.get_serializer(instance).data)

    @action(detail=False, methods=['post'], url_path='import-philippine-holidays')
    def import_philippine_holidays(self, request):
        if not request.user or not getattr(request.user, 'is_authenticated', False):
            return Response({'detail': 'Authentication required.'}, status=401)

        if not IsSchoolAdmin().has_permission(request, self):
            return Response({'detail': 'Only school administrators can import Philippine holidays.'}, status=403)

        academic_year_id = request.data.get('academic_year')
        try:
            academic_year = AcademicYear.objects.get(pk=academic_year_id)
        except (AcademicYear.DoesNotExist, TypeError, ValueError):
            return Response({'detail': 'A valid academic year is required.'}, status=400)

        service = PhilippineHolidayImportService()
        result = service.import_holidays(academic_year, user=request.user)
        return Response(result, status=200)


class RecurringSchoolCalendarEventViewSet(AuditMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = RecurringSchoolCalendarEvent.objects.select_related('academic_year', 'section', 'affected_grade_level', 'created_by').all()
    serializer_class = RecurringSchoolCalendarEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['academic_year', 'active', 'frequency']
    ordering_fields = ['start_date', 'created_at']
    ordering = ['start_date']

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return [permissions.IsAuthenticated(), IsSchoolAdmin()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        instance.full_clean()
        count = generate_occurrences(instance)
        self._audit('CREATE', instance)
        self._generated_count = count

    def perform_update(self, serializer):
        instance = serializer.save()
        instance.full_clean()
        generate_occurrences(instance)
        self._audit('UPDATE', instance)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.data['generated_occurrences'] = getattr(self, '_generated_count', 0)
        return response

    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        instance = self.get_object()
        count = generate_occurrences(instance)
        return Response({'generated_occurrences': count, 'event': self.get_serializer(instance).data})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        instance = self.get_object()
        instance.active = False
        instance.save(update_fields=['active', 'updated_at'])
        self._audit('CANCELLED', instance)
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=['post'], url_path='cancel-future')
    def cancel_future(self, request, pk=None):
        instance = self.get_object()
        reason = str(request.data.get('cancellation_reason') or '').strip()
        if not reason:
            return Response({'cancellation_reason': ['Cancellation reason is required.']}, status=400)
        cutoff = timezone.localdate()
        updated = instance.occurrences.filter(calendar_date__gte=cutoff, status__in=['DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'PUBLISHED']).update(status='CANCELLED', cancellation_reason=reason)
        instance.active = False
        instance.save(update_fields=['active', 'updated_at'])
        self._audit('CANCELLED', instance)
        return Response({'cancelled_occurrences': updated, 'event': self.get_serializer(instance).data})

    def _audit(self, action, instance):
        AuditLog.objects.create(
            user=self.request.user, action=action, module='attendance',
            object_type='RecurringSchoolCalendarEvent', object_id=str(instance.pk),
        )
