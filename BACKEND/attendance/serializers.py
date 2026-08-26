from django.utils import timezone
from rest_framework import serializers

from common.authorization import authorized_enrollment_queryset
from academics.models import Enrollment
from .models import AttendanceRecord, RecurringSchoolCalendarEvent, SchoolCalendarDay


class SchoolCalendarDaySerializer(serializers.ModelSerializer):
    attendance_expected_display = serializers.SerializerMethodField()
    conflict_warning = serializers.SerializerMethodField()

    class Meta:
        model = SchoolCalendarDay
        fields = [
            'id', 'academic_year', 'calendar_date', 'day_type', 'title', 'remarks',
            'attendance_expected', 'classes_suspended', 'scope_type', 'holiday_category',
            'holiday_source', 'section', 'created_by', 'created_at', 'updated_at',
            'affected_grade_level', 'affected_department', 'start_time', 'end_time',
            'reason', 'suspension_type', 'announcement', 'authorized_by', 'published_at',
            'location', 'organizer', 'target_participants', 'status', 'cancellation_reason', 'recurrence',
            'examination_type', 'examination_period', 'subject', 'instructor',
            'attendance_expected_display', 'conflict_warning'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'authorized_by', 'published_at']

    def get_attendance_expected_display(self, obj):
        return 'Yes' if obj.attendance_expected else 'No'

    def get_conflict_warning(self, obj):
        if not obj.location or not obj.start_time or not obj.end_time:
            return ''
        conflicts = SchoolCalendarDay.objects.filter(
            academic_year=obj.academic_year, calendar_date=obj.calendar_date,
            location__iexact=obj.location,
            start_time__lt=obj.end_time, end_time__gt=obj.start_time,
        ).exclude(pk=obj.pk)
        return 'Another calendar entry overlaps this location and time.' if conflicts.exists() else ''

    def validate(self, attrs):
        instance = self.instance or SchoolCalendarDay(**attrs)
        if self.instance and 'status' in attrs and attrs['status'] != self.instance.status:
            allowed_transitions = {
                'DRAFT': {'PENDING_APPROVAL', 'PUBLISHED', 'REJECTED', 'CANCELLED'},
                'PENDING_APPROVAL': {'APPROVED', 'REJECTED', 'CANCELLED'},
                'APPROVED': {'PUBLISHED', 'CANCELLED'},
                'PUBLISHED': {'CANCELLED', 'ARCHIVED'},
                'REJECTED': {'DRAFT', 'CANCELLED'},
                'CANCELLED': {'ARCHIVED'},
                'ARCHIVED': set(),
            }
            if attrs['status'] not in allowed_transitions.get(self.instance.status, set()):
                raise serializers.ValidationError({'status': 'Invalid calendar status transition.'})
        instance.academic_year = attrs.get('academic_year', instance.academic_year)
        instance.calendar_date = attrs.get('calendar_date', instance.calendar_date)
        instance.day_type = attrs.get('day_type', instance.day_type)
        instance.section = attrs.get('section', instance.section)
        instance.scope_type = attrs.get('scope_type', instance.scope_type)
        instance.holiday_category = attrs.get('holiday_category', instance.holiday_category)
        instance.holiday_source = attrs.get('holiday_source', instance.holiday_source)
        instance.classes_suspended = attrs.get('classes_suspended', instance.classes_suspended)
        instance.attendance_expected = attrs.get('attendance_expected', instance.attendance_expected)
        for field in ('affected_grade_level', 'affected_department', 'start_time', 'end_time', 'reason', 'suspension_type', 'announcement', 'location', 'organizer', 'target_participants', 'examination_type', 'examination_period', 'subject', 'instructor', 'status', 'cancellation_reason'):
            setattr(instance, field, attrs.get(field, getattr(instance, field)))
        instance.clean()
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
    class Meta:
        model = AttendanceRecord
        fields = ['id', 'enrollment', 'attendance_date', 'month', 'school_days', 'days_present', 'absences', 'times_tardy', 'encoded_by', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

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

        return value

    def validate(self, attrs):
        record = AttendanceRecord(**attrs)
        record.clean()
        return attrs
