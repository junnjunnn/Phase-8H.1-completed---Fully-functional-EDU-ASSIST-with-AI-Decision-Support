from django.utils import timezone
from rest_framework import serializers

from common.authorization import active_enrollment_queryset, authorized_enrollment_queryset
from academics.models import Enrollment
from .models import AttendanceRecord, RecurringSchoolCalendarEvent, SchoolCalendarDay
from .conflicts import detect_conflicts, serialize_conflicts


class SchoolCalendarDaySerializer(serializers.ModelSerializer):
    attendance_expected_display = serializers.SerializerMethodField()
    conflict_warning = serializers.SerializerMethodField()
    conflicts = serializers.SerializerMethodField()

    class Meta:
        model = SchoolCalendarDay
        fields = [
            'id', 'academic_year', 'calendar_date', 'end_date', 'day_type', 'event_type', 'title', 'remarks',
            'attendance_expected', 'classes_suspended', 'scope_type', 'holiday_category',
            'holiday_source', 'section', 'created_by', 'created_at', 'updated_at',
            'affected_grade_level', 'affected_department', 'start_time', 'end_time',
            'reason', 'suspension_type', 'announcement', 'authorized_by', 'published_at',
            'submitted_by', 'submitted_at', 'approved_by', 'approved_at', 'rejected_by', 'rejected_at',
            'rejection_reason', 'approval_notes', 'location', 'organizer', 'target_participants', 'status', 'cancellation_reason', 'recurrence',
            'examination_type', 'examination_period', 'subject', 'instructor',
            'attendance_expected_display', 'conflict_warning', 'conflicts'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'authorized_by', 'published_at', 'submitted_by', 'submitted_at', 'approved_by', 'approved_at', 'rejected_by', 'rejected_at']

    def _normalize_material_value(self, value):
        if value is None or value == '':
            return None
        if hasattr(value, 'isoformat'):
            return value.isoformat()
        if hasattr(value, 'id'):
            return value.id
        return value

    def get_attendance_expected_display(self, obj):
        return 'Yes' if obj.attendance_expected else 'No'

    def get_conflict_warning(self, obj):
        return 'Potential scheduling conflict detected.' if detect_conflicts(obj) else ''

    def get_conflicts(self, obj):
        return serialize_conflicts(detect_conflicts(obj))

    def validate(self, attrs):
        instance = self.instance or SchoolCalendarDay(**attrs)
        if self.instance and self.instance.status in {'APPROVED', 'PUBLISHED'}:
            material_fields = {'calendar_date', 'end_date', 'day_type', 'event_type', 'title', 'location', 'scope_type', 'section', 'affected_grade_level', 'affected_department', 'start_time', 'end_time', 'attendance_expected', 'classes_suspended', 'reason', 'announcement', 'organizer', 'target_participants', 'examination_type', 'examination_period', 'subject', 'instructor'}
            changed = False
            for field in material_fields:
                current_value = self._normalize_material_value(getattr(self.instance, field))
                updated_value = self._normalize_material_value(attrs.get(field, getattr(self.instance, field)))
                if current_value != updated_value:
                    changed = True
                    break
            if changed:
                attrs['status'] = 'PENDING_APPROVAL'
        if self.instance and 'status' in attrs and attrs['status'] != self.instance.status:
            allowed_transitions = {
                'DRAFT': {'PENDING_APPROVAL'},
                'PENDING_APPROVAL': {'APPROVED', 'REJECTED'},
                'APPROVED': {'PUBLISHED', 'CANCELLED', 'PENDING_APPROVAL'},
                'PUBLISHED': {'CANCELLED', 'ARCHIVED', 'PENDING_APPROVAL'},
                'REJECTED': {'DRAFT'},
                'CANCELLED': {'ARCHIVED'},
                'ARCHIVED': set(),
            }
            if attrs['status'] not in allowed_transitions.get(self.instance.status, set()):
                raise serializers.ValidationError({'status': 'Invalid calendar status transition.'})
        if not self.instance and attrs.get('status') == 'PUBLISHED' and attrs.get('approved_by') is None:
            attrs['status'] = 'APPROVED'
        instance.academic_year = attrs.get('academic_year', instance.academic_year)
        instance.calendar_date = attrs.get('calendar_date', instance.calendar_date)
        instance.day_type = attrs.get('day_type', instance.day_type)
        instance.section = attrs.get('section', instance.section)
        instance.scope_type = attrs.get('scope_type', instance.scope_type)
        instance.holiday_category = attrs.get('holiday_category', instance.holiday_category)
        instance.holiday_source = attrs.get('holiday_source', instance.holiday_source)
        instance.classes_suspended = attrs.get('classes_suspended', instance.classes_suspended)
        instance.attendance_expected = attrs.get('attendance_expected', instance.attendance_expected)
        for field in ('end_date', 'event_type', 'affected_grade_level', 'affected_department', 'start_time', 'end_time', 'reason', 'suspension_type', 'announcement', 'location', 'organizer', 'target_participants', 'examination_type', 'examination_period', 'subject', 'instructor', 'status', 'cancellation_reason', 'rejection_reason', 'approval_notes'):
            setattr(instance, field, attrs.get(field, getattr(instance, field)))
        instance.clean()
        self._calendar_candidate = instance
        conflicts = detect_conflicts(instance)
        if conflicts and not self.context.get('skip_conflict_validation'):
            blocking = [conflict for conflict in conflicts if conflict['severity'] == 'ERROR']
            if blocking:
                raise serializers.ValidationError({'conflicts': serialize_conflicts(blocking)})
        if instance.day_type in {'ENROLLMENT', 'ACADEMIC_DEADLINE'}:
            attrs['attendance_expected'] = False
            attrs['classes_suspended'] = False
        if instance.day_type == 'EXAMINATION' and instance.instructor:
            profile = getattr(instance.instructor, 'profile', None)
            if not profile or profile.role_name != 'TEACHER':
                raise serializers.ValidationError({'instructor': 'Instructor must be an active teacher.'})
        if instance.status == 'PUBLISHED' and not instance.published_at:
            instance.published_at = timezone.now()
        return attrs


class RecurringSchoolCalendarEventSerializer(serializers.ModelSerializer):
    occurrence_count = serializers.SerializerMethodField()

    class Meta:
        model = RecurringSchoolCalendarEvent
        fields = [
            'id', 'academic_year', 'title', 'day_type', 'remarks', 'attendance_expected',
            'classes_suspended', 'scope_type', 'section', 'affected_grade_level',
            'affected_department', 'start_date', 'recurrence_end_date', 'start_time',
            'end_time', 'location', 'organizer', 'target_participants', 'frequency',
            'recurrence_interval', 'recurrence_weekday', 'recurrence_month_day',
            'recurrence_month', 'recurrence_week', 'active', 'created_by', 'created_at',
            'updated_at', 'occurrence_count',
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'occurrence_count']

    def get_occurrence_count(self, obj):
        return obj.occurrences.count()

    def validate(self, attrs):
        instance = self.instance or RecurringSchoolCalendarEvent(**attrs)
        for field, value in attrs.items():
            setattr(instance, field, value)
        instance.full_clean()
        return attrs


class AttendanceRecordSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    academic_year_name = serializers.CharField(source='enrollment.academic_year.name', read_only=True)
    section_name = serializers.CharField(source='enrollment.section.name', read_only=True)
    class Meta:
        model = AttendanceRecord
        fields = ['id', 'enrollment', 'student_name', 'academic_year_name', 'section_name', 'attendance_date', 'month', 'school_days', 'days_present', 'absences', 'times_tardy', 'encoded_by', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_student_name(self, obj):
        return str(obj.enrollment.student)

    def validate_enrollment(self, value):
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError('Authentication required.')

        authorized_qs = authorized_enrollment_queryset(
            request.user,
            Enrollment.objects.all(),
            enrollment_field='pk'
        )

        if not authorized_qs.filter(pk=value.pk).exists():
            raise serializers.ValidationError(
                'You do not have permission to create records for this enrollment.'
            )

        if not active_enrollment_queryset(Enrollment.objects.filter(pk=value.pk)).exists():
            raise serializers.ValidationError(
                'Attendance can only be recorded for active students with a current academic context.'
            )

        return value

    def validate(self, attrs):
        record = AttendanceRecord(**attrs)
        record.clean()
        return attrs
