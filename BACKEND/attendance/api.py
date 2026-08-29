from datetime import date

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

    MATERIAL_REAPPROVAL_FIELDS = {'calendar_date', 'end_date', 'day_type', 'event_type', 'title', 'location', 'scope_type', 'section', 'affected_grade_level', 'affected_department', 'start_time', 'end_time', 'attendance_expected', 'classes_suspended', 'reason', 'announcement', 'organizer', 'target_participants', 'examination_type', 'examination_period', 'subject', 'instructor'}

    def get_permissions(self):
        if self.action in {'publish', 'approve', 'reject', 'cancel', 'import_philippine_holidays'}:
            return [permissions.IsAuthenticated(), IsSchoolAdmin()]
        if self.action in {'submit_for_approval'}:
            return [permissions.IsAuthenticated()]
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return [permissions.IsAuthenticated(), IsAuthorizedStaff()]
        return [permissions.IsAuthenticated()]

    @staticmethod
    def _normalize_value(value):
        if value is None or value == '':
            return None
        if hasattr(value, 'isoformat'):
            return value.isoformat()
        if hasattr(value, 'id'):
            return value.id
        return value

    def _material_change_detected(self, instance, payload):
        if not instance or not payload:
            return False
        for field in self.MATERIAL_REAPPROVAL_FIELDS:
            current = self._normalize_value(getattr(instance, field, None))
            incoming = self._normalize_value(payload.get(field, getattr(instance, field, None)))
            if current != incoming:
                return True
        return False

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        material_change = self._material_change_detected(instance, request.data)
        kwargs['partial'] = partial
        response = super().update(request, *args, **kwargs)
        if material_change and instance.status in {'APPROVED', 'PUBLISHED'}:
            instance.refresh_from_db()
            if instance.status in {'APPROVED', 'PUBLISHED'}:
                instance.status = 'PENDING_APPROVAL'
                instance.approved_by = None
                instance.approved_at = None
                instance.authorized_by = None
                instance.published_at = None
                instance.save(update_fields=['status', 'approved_by', 'approved_at', 'authorized_by', 'published_at', 'updated_at'])
                self._audit('REAPPROVAL_REQUIRED', instance)
                response.data = self.get_serializer(instance).data
        return response

    @action(detail=False, methods=['post'], url_path='check-conflicts')
    def check_conflicts(self, request):
        serializer = self.get_serializer(data=request.data, context={**self.get_serializer_context(), 'skip_conflict_validation': True})
        serializer.is_valid(raise_exception=True)
        conflicts = detect_conflicts(serializer._calendar_candidate)
        return Response({'conflicts': serialize_conflicts(conflicts), 'has_conflicts': bool(conflicts)})

    @action(detail=False, methods=['post'], url_path='bulk-edit')
    @transaction.atomic
    def bulk_edit(self, request):
        if not request.user or not getattr(request.user, 'is_authenticated', False):
            return Response({'detail': 'Authentication required.'}, status=401)
        if not IsAuthorizedStaff().has_permission(request, self):
            return Response({'detail': 'Only authorized staff can apply bulk calendar edits.'}, status=403)

        academic_year_id = request.data.get('academic_year')
        if academic_year_id in (None, ''):
            return Response({'detail': 'A valid academic year is required.'}, status=400)

        try:
            academic_year = AcademicYear.objects.get(pk=academic_year_id)
        except (AcademicYear.DoesNotExist, TypeError, ValueError):
            return Response({'detail': 'A valid academic year is required.'}, status=400)

        selected_dates = request.data.get('selected_dates') or []
        if not isinstance(selected_dates, list) or not selected_dates:
            return Response({'detail': 'Select at least one date to apply the bulk action.'}, status=400)

        existing_behavior = str(request.data.get('existing_behavior', 'skip') or 'skip').lower()
        if existing_behavior not in {'skip', 'replace'}:
            return Response({'detail': 'existing_behavior must be either "skip" or "replace".'}, status=400)

        normalized_dates = []
        seen_dates = set()
        for raw_date in selected_dates:
            if not raw_date:
                continue
            try:
                parsed_date = date.fromisoformat(str(raw_date))
            except ValueError:
                return Response({'detail': f'Invalid date selected: {raw_date}'}, status=400)
            if parsed_date < academic_year.start_date or parsed_date > academic_year.end_date:
                return Response({'detail': f'The selected date {parsed_date.isoformat()} falls outside the academic year range.'}, status=400)
            iso_date = parsed_date.isoformat()
            if iso_date not in seen_dates:
                seen_dates.add(iso_date)
                normalized_dates.append(iso_date)

        bulk_payload = {key: value for key, value in request.data.items() if key not in {'selected_dates', 'existing_behavior', 'academic_year'}}
        bulk_payload.setdefault('status', 'DRAFT' if IsSchoolAdmin().has_permission(request, self) else 'PENDING_APPROVAL')

        existing_records = {
            record.calendar_date.isoformat(): record
            for record in SchoolCalendarDay.objects.filter(
                academic_year=academic_year,
                calendar_date__in=[date.fromisoformat(item) for item in normalized_dates],
            ).exclude(status__in={'CANCELLED', 'ARCHIVED', 'REJECTED'})
        }

        validation_errors = []
        created_dates = []
        updated_dates = []
        skipped_dates = []
        processed_records = []

        for date_str in normalized_dates:
            existing_record = existing_records.get(date_str)
            if existing_record and existing_behavior == 'skip':
                skipped_dates.append(date_str)
                continue

            payload = {
                **bulk_payload,
                'academic_year': academic_year.id,
                'calendar_date': date_str,
            }

            serializer = None
            if existing_record:
                serializer = SchoolCalendarDaySerializer(
                    existing_record,
                    data=payload,
                    partial=True,
                    context={**self.get_serializer_context(), 'request': request},
                )
            else:
                serializer = SchoolCalendarDaySerializer(
                    data=payload,
                    context={**self.get_serializer_context(), 'request': request},
                )

            if not serializer.is_valid():
                validation_errors.append({'date': date_str, 'errors': serializer.errors})
                continue

            saved = serializer.save(created_by=request.user) if not existing_record else serializer.save()
            processed_records.append(saved)
            if existing_record:
                updated_dates.append(date_str)
            else:
                created_dates.append(date_str)

        if validation_errors:
            return Response({
                'requested_dates': normalized_dates,
                'successfully_processed_dates': sorted(created_dates + updated_dates),
                'skipped_existing_dates': sorted(skipped_dates),
                'conflicting_dates': [item['date'] for item in validation_errors if 'conflicts' in item['errors']],
                'validation_errors': validation_errors,
                'message': 'Bulk calendar edit was blocked by validation conflicts or invalid payload values.',
            }, status=400)

        response_payload = {
            'requested_dates': normalized_dates,
            'successfully_processed_dates': sorted(created_dates + updated_dates),
            'created_dates': sorted(created_dates),
            'updated_dates': sorted(updated_dates),
            'skipped_existing_dates': sorted(skipped_dates),
            'conflicting_dates': [],
            'validation_errors': [],
            'records': [self.get_serializer(record).data for record in processed_records],
            'message': 'Bulk calendar edit applied to the selected dates.'
        }
        return Response(response_payload)

    def perform_create(self, serializer):
        status = serializer.validated_data.get('status')
        if status is None:
            status = 'PENDING_APPROVAL' if not IsSchoolAdmin().has_permission(self.request, self) else 'DRAFT'
        instance = serializer.save(created_by=self.request.user, status=status)
        self._audit('CREATE', instance, details={'created_fields': sorted(serializer.validated_data.keys())})

    def perform_update(self, serializer):
        instance = serializer.save()
        old_status = getattr(serializer.instance, 'status', '') if serializer.instance else ''
        changed_fields = []
        for field in serializer.validated_data:
            if field in {'updated_at'}:
                continue
            changed_fields.append(field)
        self._audit('UPDATE', instance, previous_status=old_status, details={'changed_fields': changed_fields, 'summary': f'Updated {len(changed_fields)} fields.'})

    def _audit(self, action, instance, previous_status=None, reason=None, details=None):
        audit_details = details or {}
        AuditLog.objects.create(
            user=self.request.user,
            action=action,
            module='attendance',
            object_type='SchoolCalendarDay',
            object_id=str(instance.pk),
            object_name=getattr(instance, 'title', ''),
            object_date=getattr(instance, 'calendar_date', None),
            previous_status=previous_status or '',
            new_status=getattr(instance, 'status', '') or '',
            reason=reason or '',
            details=audit_details,
        )

    @action(detail=True, methods=['post'], url_path='submit-for-approval')
    def submit_for_approval(self, request, pk=None):
        instance = self.get_object()
        allowed = {'DRAFT', 'REJECTED'}
        if instance.status not in allowed:
            return Response({'detail': 'Only draft or rejected events can be submitted for approval.'}, status=400)
        if instance.created_by_id != request.user.id and not IsSchoolAdmin().has_permission(request, self):
            return Response({'detail': 'Only the creator or a school administrator can submit this event for approval.'}, status=403)
        previous_status = instance.status
        instance.status = 'PENDING_APPROVAL'
        instance.submitted_by = request.user
        instance.submitted_at = timezone.now()
        instance.save(update_fields=['status', 'submitted_by', 'submitted_at', 'updated_at'])
        self._audit('SUBMITTED_FOR_APPROVAL', instance, previous_status=previous_status, details={'submitted_by': request.user.username})
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
        previous_status = instance.status
        instance.status = 'APPROVED'
        instance.approved_by = request.user
        instance.approved_at = timezone.now()
        instance.approval_notes = str(request.data.get('approval_notes') or '').strip()
        instance.save(update_fields=['status', 'approved_by', 'approved_at', 'approval_notes', 'updated_at'])
        self._audit('APPROVED', instance, previous_status=previous_status, reason=instance.approval_notes, details={'approved_by': request.user.username, 'approval_notes': instance.approval_notes})
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
        previous_status = instance.status
        instance.status = 'REJECTED'
        instance.rejected_by = request.user
        instance.rejected_at = timezone.now()
        instance.rejection_reason = reason
        instance.save(update_fields=['status', 'rejected_by', 'rejected_at', 'rejection_reason', 'updated_at'])
        self._audit('REJECTED', instance, previous_status=previous_status, reason=reason, details={'rejected_by': request.user.username})
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        instance = self.get_object()
        if instance.status != 'APPROVED':
            return Response({'detail': 'Only approved events can be published.'}, status=400)
        if instance.status == 'CANCELLED':
            return Response({'detail': 'Cancelled entries cannot be published.'}, status=400)
        previous_status = instance.status
        instance.status = 'PUBLISHED'
        instance.published_at = timezone.now()
        instance.authorized_by = request.user
        instance.save(update_fields=['status', 'published_at', 'authorized_by', 'updated_at'])
        self._audit('PUBLISHED', instance, previous_status=previous_status, details={'published_by': request.user.username})
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        instance = self.get_object()
        reason = str(request.data.get('cancellation_reason') or '').strip()
        if not reason:
            return Response({'cancellation_reason': ['Cancellation reason is required.']}, status=400)
        previous_status = instance.status
        instance.status = 'CANCELLED'
        instance.cancellation_reason = reason
        instance.save(update_fields=['status', 'cancellation_reason', 'updated_at'])
        self._audit('CANCELLED', instance, previous_status=previous_status, reason=reason, details={'cancelled_by': request.user.username})
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
