from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from django.db import transaction
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
from .conflicts import detect_conflicts, detect_recurring_conflicts, serialize_conflicts
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
        if self.action in {'publish', 'approve', 'reject', 'cancel', 'import_philippine_holidays'}:
            return [permissions.IsAuthenticated(), IsSchoolAdmin()]
        if self.action in {'submit_for_approval'}:
            return [permissions.IsAuthenticated()]
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return [permissions.IsAuthenticated(), IsAuthorizedStaff()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['post'], url_path='check-conflicts')
    def check_conflicts(self, request):
        serializer = self.get_serializer(data=request.data, context={**self.get_serializer_context(), 'skip_conflict_validation': True})
        serializer.is_valid(raise_exception=True)
        conflicts = detect_conflicts(serializer._calendar_candidate)
        return Response({'conflicts': serialize_conflicts(conflicts), 'has_conflicts': bool(conflicts)})

    def perform_create(self, serializer):
        status = serializer.validated_data.get('status')
        if not IsSchoolAdmin().has_permission(self.request, self):
            status = 'PENDING_APPROVAL'
        elif status is None:
            status = 'DRAFT'
        instance = serializer.save(created_by=self.request.user, status=status or 'DRAFT')
        self._audit('CREATE', instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self._audit('UPDATE', instance)

    def _audit(self, action, instance):
        AuditLog.objects.create(
            user=self.request.user, action=action, module='attendance',
            object_type='SchoolCalendarDay', object_id=str(instance.pk),
        )

    @action(detail=True, methods=['post'], url_path='submit-for-approval')
    def submit_for_approval(self, request, pk=None):
        instance = self.get_object()
        allowed = {'DRAFT', 'REJECTED'}
        if instance.status not in allowed:
            return Response({'detail': 'Only draft or rejected events can be submitted for approval.'}, status=400)
        if instance.created_by_id != request.user.id and not IsSchoolAdmin().has_permission(request, self):
            return Response({'detail': 'Only the creator or a school administrator can submit this event for approval.'}, status=403)
        instance.status = 'PENDING_APPROVAL'
        instance.submitted_by = request.user
        instance.submitted_at = timezone.now()
        instance.save(update_fields=['status', 'submitted_by', 'submitted_at', 'updated_at'])
        self._audit('SUBMITTED_FOR_APPROVAL', instance)
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        instance = self.get_object()
        if instance.created_by_id == request.user.id:
            return Response({'detail': 'A creator cannot approve their own event.'}, status=400)
        if not IsSchoolAdmin().has_permission(request, self):
            return Response({'detail': 'Only school administrators can approve calendar events.'}, status=403)
        if instance.status != 'PENDING_APPROVAL':
            return Response({'detail': 'Only pending approval events can be approved.'}, status=400)
        instance.status = 'APPROVED'
        instance.approved_by = request.user
        instance.approved_at = timezone.now()
        instance.approval_notes = str(request.data.get('approval_notes') or '').strip()
        instance.save(update_fields=['status', 'approved_by', 'approved_at', 'approval_notes', 'updated_at'])
        self._audit('APPROVED', instance)
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        instance = self.get_object()
        if instance.created_by_id == request.user.id:
            return Response({'detail': 'A creator cannot reject their own event.'}, status=400)
        if not IsSchoolAdmin().has_permission(request, self):
            return Response({'detail': 'Only school administrators can reject calendar events.'}, status=403)
        if instance.status != 'PENDING_APPROVAL':
            return Response({'detail': 'Only pending approval events can be rejected.'}, status=400)
        reason = str(request.data.get('rejection_reason') or '').strip()
        if not reason:
            return Response({'rejection_reason': ['Rejection reason is required.']}, status=400)
        instance.status = 'REJECTED'
        instance.rejected_by = request.user
        instance.rejected_at = timezone.now()
        instance.rejection_reason = reason
        instance.save(update_fields=['status', 'rejected_by', 'rejected_at', 'rejection_reason', 'updated_at'])
        self._audit('REJECTED', instance)
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        instance = self.get_object()
        if instance.status != 'APPROVED':
            return Response({'detail': 'Only approved events can be published.'}, status=400)
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

    @transaction.atomic
    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        instance.full_clean()
        conflicts = detect_recurring_conflicts(instance)
        if any(conflict['severity'] == 'ERROR' for conflict in conflicts):
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'conflicts': serialize_conflicts(conflicts)})
        count = generate_occurrences(instance)
        self._audit('CREATE', instance)
        self._generated_count = count

    @transaction.atomic
    def perform_update(self, serializer):
        instance = serializer.save()
        instance.full_clean()
        conflicts = detect_recurring_conflicts(instance)
        if any(conflict['severity'] == 'ERROR' for conflict in conflicts):
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'conflicts': serialize_conflicts(conflicts)})
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
