from django.conf import settings
from django.db import models
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from academics.models import AcademicYear, Enrollment, GradeLevel, Section


class SchoolCalendarDay(models.Model):
    SUSPENSION_TYPE_CHOICES = [
        ('WEATHER_RELATED', 'Weather-related'),
        ('NATURAL_DISASTER', 'Natural Disaster'),
        ('LOCAL_GOVERNMENT', 'Local Government Announcement'),
        ('SCHOOL_ADMINISTRATION', 'School Administration'),
        ('EMERGENCY', 'Emergency'),
        ('OTHER', 'Other'),
    ]
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'), ('PENDING_APPROVAL', 'Pending Approval'),
        ('APPROVED', 'Approved'), ('PUBLISHED', 'Published'),
        ('REJECTED', 'Rejected'), ('CANCELLED', 'Cancelled'), ('ARCHIVED', 'Archived'),
    ]
    DAY_TYPE_CHOICES = [
        ('SCHOOL_DAY', 'School Day'),
        ('WEEKEND', 'Weekend'),
        ('HOLIDAY', 'Holiday'),
        ('SUSPENSION', 'Suspension'),
        ('SCHOOL_EVENT', 'School Event'),
        ('ACTIVITY', 'Activity'),
        ('EXAMINATION', 'Examination'),
        ('SPECIAL_NON_CLASS_DAY', 'Special Non-Class Day'),
    ]
    EXAMINATION_TYPE_CHOICES = [
        ('PRELIMINARY', 'Preliminary Examination'),
        ('MIDTERM', 'Midterm Examination'),
        ('SEMI_FINAL', 'Semi-Final Examination'),
        ('FINAL', 'Final Examination'),
        ('ENTRANCE', 'Entrance Examination'),
        ('ADMISSION_TEST', 'Admission Test'),
        ('QUALIFYING', 'Qualifying Examination'),
        ('OTHER', 'Other Examination'),
    ]
    EXAMINATION_PERIOD_CHOICES = [
        ('PRELIMINARY', 'Preliminary'),
        ('MIDTERM', 'Midterm'),
        ('SEMI_FINAL', 'Semi-Final'),
        ('FINAL', 'Final'),
        ('OTHER', 'Other'),
    ]
    SCOPE_TYPE_CHOICES = [
        ('SCHOOL_WIDE', 'School-wide'),
        ('GRADE_LEVEL', 'Specific grade level'),
        ('DEPARTMENT', 'Specific department'),
        ('SECTION_SPECIFIC', 'Specific section'),
        ('TIME_SPECIFIC', 'Specific time'),
    ]
    HOLIDAY_CATEGORY_CHOICES = [
        ('REGULAR_HOLIDAY', 'Regular Holiday'),
        ('SPECIAL_NON_WORKING_HOLIDAY', 'Special Non-Working Holiday'),
        ('LOCAL_HOLIDAY', 'Local Holiday'),
        ('SCHOOL_HOLIDAY', 'School Holiday'),
    ]
    HOLIDAY_SOURCE_CHOICES = [
        ('MANUAL', 'Manual'),
        ('PHILIPPINE_IMPORT', 'Philippine Holiday Import'),
    ]

    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='school_calendar_days')
    calendar_date = models.DateField()
    day_type = models.CharField(max_length=30, choices=DAY_TYPE_CHOICES, default='SCHOOL_DAY')
    title = models.CharField(max_length=150)
    remarks = models.TextField(blank=True, default='')
    attendance_expected = models.BooleanField(default=True)
    classes_suspended = models.BooleanField(default=False)
    scope_type = models.CharField(max_length=30, choices=SCOPE_TYPE_CHOICES, default='SCHOOL_WIDE')
    holiday_category = models.CharField(max_length=35, choices=HOLIDAY_CATEGORY_CHOICES, blank=True, default='')
    holiday_source = models.CharField(max_length=25, choices=HOLIDAY_SOURCE_CHOICES, default='MANUAL')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='school_calendar_days', null=True, blank=True)
    affected_grade_level = models.ForeignKey(GradeLevel, on_delete=models.SET_NULL, related_name='school_calendar_days', null=True, blank=True)
    affected_department = models.CharField(max_length=150, blank=True, default='')
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    reason = models.TextField(blank=True, default='')
    suspension_type = models.CharField(max_length=40, choices=SUSPENSION_TYPE_CHOICES, blank=True, default='OTHER')
    announcement = models.TextField(blank=True, default='')
    authorized_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='authorized_school_calendar_days', null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True, default='')
    organizer = models.CharField(max_length=150, blank=True, default='')
    target_participants = models.CharField(max_length=200, blank=True, default='')
    examination_type = models.CharField(max_length=30, choices=EXAMINATION_TYPE_CHOICES, blank=True, default='')
    examination_period = models.CharField(max_length=20, choices=EXAMINATION_PERIOD_CHOICES, blank=True, default='')
    subject = models.ForeignKey('academics.Subject', on_delete=models.SET_NULL, related_name='examination_calendar_days', null=True, blank=True)
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='examination_calendar_days', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    cancellation_reason = models.TextField(blank=True, default='')
    recurrence = models.ForeignKey('RecurringSchoolCalendarEvent', on_delete=models.SET_NULL, related_name='occurrences', null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='school_calendar_days', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['calendar_date']
        indexes = [
            models.Index(fields=['academic_year', 'calendar_date']),
            models.Index(fields=['attendance_expected', 'calendar_date']),
            models.Index(fields=['day_type', 'calendar_date']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['recurrence', 'calendar_date'], name='unique_recurrence_calendar_date'),
        ]

    def clean(self):
        if self.scope_type == 'SECTION_SPECIFIC' and not self.section:
            raise ValidationError({'section': 'A section-specific calendar entry must include a section.'})
        if self.scope_type != 'SECTION_SPECIFIC' and self.section:
            raise ValidationError({'section': 'Section can only be set for a section-specific entry.'})
        if self.scope_type == 'GRADE_LEVEL' and not self.affected_grade_level:
            raise ValidationError({'affected_grade_level': 'A grade level is required for grade-level scope.'})
        if self.scope_type != 'GRADE_LEVEL' and self.affected_grade_level:
            raise ValidationError({'affected_grade_level': 'Grade level can only be set for grade-level scope.'})
        if self.scope_type == 'DEPARTMENT' and not self.affected_department.strip():
            raise ValidationError({'affected_department': 'A department is required for department scope.'})
        if self.scope_type != 'DEPARTMENT' and self.affected_department:
            raise ValidationError({'affected_department': 'Department can only be set for department scope.'})
        if self.start_time and self.end_time and self.end_time < self.start_time:
            raise ValidationError({'end_time': 'End time cannot be before start time.'})
        if self.status == 'CANCELLED' and not self.cancellation_reason.strip():
            raise ValidationError({'cancellation_reason': 'Cancellation reason is required.'})
        if self.day_type == 'SUSPENSION' and not self.suspension_type:
            raise ValidationError({'suspension_type': 'Suspension type is required.'})
        if self.day_type == 'EXAMINATION' and not self.examination_type:
            raise ValidationError({'examination_type': 'Examination type is required for examination entries.'})
        if self.day_type != 'EXAMINATION' and (self.examination_type or self.examination_period or self.subject or self.instructor):
            raise ValidationError({'day_type': 'Examination details can only be set for examination entries.'})
        if self.section and self.academic_year and self.section.academic_year_id != self.academic_year_id:
            raise ValidationError({'section': 'Section must belong to the selected academic year.'})
        if self.subject and self.section:
            subject_grade_ids = set(self.subject.grade_levels.values_list('id', flat=True))
            if self.subject.grade_level_id:
                subject_grade_ids.add(self.subject.grade_level_id)
            if subject_grade_ids and self.section.grade_level_id not in subject_grade_ids:
                raise ValidationError({'subject': 'Subject must belong to the selected section grade level.'})
        if self.day_type == 'SUSPENSION' and not self.classes_suspended:
            self.classes_suspended = True
        if self.day_type in {'HOLIDAY', 'SUSPENSION', 'SPECIAL_NON_CLASS_DAY', 'WEEKEND'}:
            self.attendance_expected = False
        if self.day_type == 'SCHOOL_DAY':
            self.attendance_expected = True
        if self.holiday_category and self.day_type != 'HOLIDAY':
            self.holiday_category = ''
        if self.academic_year and self.calendar_date:
            if self.calendar_date < self.academic_year.start_date or self.calendar_date > self.academic_year.end_date:
                raise ValidationError({'calendar_date': 'The calendar date must fall within the selected academic year.'})

    def is_attendance_expected(self):
        return bool(self.attendance_expected)

    @classmethod
    def get_expected_school_days(cls, academic_year, start_date=None, end_date=None):
        if not academic_year:
            return 0
        queryset = cls.objects.filter(academic_year=academic_year, attendance_expected=True)
        if start_date:
            queryset = queryset.filter(calendar_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(calendar_date__lte=end_date)
        return queryset.values('calendar_date').distinct().count()

    @classmethod
    def get_expected_school_day_dates(cls, academic_year, start_date=None, end_date=None):
        queryset = cls.objects.filter(academic_year=academic_year, attendance_expected=True)
        if start_date:
            queryset = queryset.filter(calendar_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(calendar_date__lte=end_date)
        return list(queryset.values_list('calendar_date', flat=True).distinct())

    @classmethod
    def get_day_status_for_date(cls, academic_year, calendar_date):
        if not academic_year or not calendar_date:
            return None
        return cls.objects.filter(
            academic_year=academic_year, calendar_date=calendar_date,
        ).order_by('attendance_expected', 'id').first()

    def __str__(self):
        return f"{self.academic_year.name} - {self.calendar_date} - {self.day_type}"


class RecurringSchoolCalendarEvent(models.Model):
    FREQUENCY_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('YEARLY', 'Yearly'),
        ('CUSTOM', 'Custom'),
    ]

    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='recurring_school_calendar_events')
    title = models.CharField(max_length=150)
    day_type = models.CharField(max_length=30, choices=SchoolCalendarDay.DAY_TYPE_CHOICES, default='SCHOOL_EVENT')
    remarks = models.TextField(blank=True, default='')
    attendance_expected = models.BooleanField(default=False)
    classes_suspended = models.BooleanField(default=False)
    scope_type = models.CharField(max_length=30, choices=SchoolCalendarDay.SCOPE_TYPE_CHOICES, default='SCHOOL_WIDE')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='recurring_school_calendar_events', null=True, blank=True)
    affected_grade_level = models.ForeignKey(GradeLevel, on_delete=models.SET_NULL, related_name='recurring_school_calendar_events', null=True, blank=True)
    affected_department = models.CharField(max_length=150, blank=True, default='')
    start_date = models.DateField()
    recurrence_end_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True, default='')
    organizer = models.CharField(max_length=150, blank=True, default='')
    target_participants = models.CharField(max_length=200, blank=True, default='')
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    recurrence_interval = models.PositiveIntegerField(default=1)
    recurrence_weekday = models.PositiveSmallIntegerField(null=True, blank=True)
    recurrence_month_day = models.PositiveSmallIntegerField(null=True, blank=True)
    recurrence_month = models.PositiveSmallIntegerField(null=True, blank=True)
    recurrence_week = models.SmallIntegerField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='recurring_school_calendar_events', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_date', 'id']

    def clean(self):
        if self.start_date < self.academic_year.start_date or self.start_date > self.academic_year.end_date:
            raise ValidationError({'start_date': 'The recurrence start date must fall within the selected academic year.'})
        if self.recurrence_end_date < self.start_date or self.recurrence_end_date > self.academic_year.end_date:
            raise ValidationError({'recurrence_end_date': 'The recurrence end date must be within the selected academic year and after the start date.'})
        if self.recurrence_interval < 1:
            raise ValidationError({'recurrence_interval': 'The recurrence interval must be at least 1.'})
        if self.start_time and self.end_time and self.end_time < self.start_time:
            raise ValidationError({'end_time': 'End time cannot be before start time.'})
        if self.scope_type == 'SECTION_SPECIFIC' and not self.section:
            raise ValidationError({'section': 'A section-specific recurrence must include a section.'})
        if self.scope_type != 'SECTION_SPECIFIC' and self.section:
            raise ValidationError({'section': 'Section can only be set for a section-specific recurrence.'})
        if self.scope_type == 'GRADE_LEVEL' and not self.affected_grade_level:
            raise ValidationError({'affected_grade_level': 'A grade level is required for grade-level scope.'})
        if self.scope_type != 'GRADE_LEVEL' and self.affected_grade_level:
            raise ValidationError({'affected_grade_level': 'Grade level can only be set for grade-level scope.'})
        if self.frequency in {'WEEKLY', 'MONTHLY'} and self.recurrence_weekday is None:
            raise ValidationError({'recurrence_weekday': 'A weekday is required for weekly and monthly recurrence.'})
        if self.recurrence_weekday is not None and not 0 <= self.recurrence_weekday <= 6:
            raise ValidationError({'recurrence_weekday': 'Weekday must be between 0 (Monday) and 6 (Sunday).'})
        if self.frequency == 'MONTHLY' and self.recurrence_week not in {1, 2, 3, 4, 5, -1}:
            raise ValidationError({'recurrence_week': 'Monthly recurrence requires week 1-5 or -1 for the last week.'})
        if self.frequency == 'YEARLY':
            if not self.recurrence_month or not 1 <= self.recurrence_month <= 12:
                raise ValidationError({'recurrence_month': 'Yearly recurrence requires a month from 1 to 12.'})
            if not self.recurrence_month_day or not 1 <= self.recurrence_month_day <= 31:
                raise ValidationError({'recurrence_month_day': 'Yearly recurrence requires a valid day of month.'})
        if self.frequency == 'CUSTOM' and not self.recurrence_interval:
            raise ValidationError({'recurrence_interval': 'Custom recurrence requires an interval.'})

    def __str__(self):
        return f"{self.title} ({self.frequency})"


class AttendanceRecord(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='attendance_records')
    attendance_date = models.DateField(null=True, blank=True)
    month = models.CharField(max_length=20)
    school_days = models.PositiveIntegerField(default=0)
    days_present = models.PositiveIntegerField(default=0)
    absences = models.PositiveIntegerField(default=0)
    times_tardy = models.PositiveIntegerField(default=0)
    encoded_by = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.SET_NULL, related_name='encoded_attendance_records')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('enrollment', 'month'), ('enrollment', 'attendance_date'))
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['enrollment', 'month']),
            models.Index(fields=['enrollment', 'attendance_date']),
        ]

    def clean(self):
        if self.days_present > self.school_days:
            raise ValidationError({'days_present': 'Days present cannot exceed school days.'})
        if self.absences < 0:
            raise ValidationError({'absences': 'Absences cannot be negative.'})
        if self.times_tardy < 0:
            raise ValidationError({'times_tardy': 'Tardiness cannot be negative.'})
        if self.attendance_date and self.enrollment and self.enrollment.academic_year:
            calendar_day = SchoolCalendarDay.objects.filter(
                academic_year=self.enrollment.academic_year,
                calendar_date=self.attendance_date,
            ).order_by('attendance_expected', 'id').first()
            if calendar_day and not calendar_day.attendance_expected:
                raise ValidationError({'attendance_date': 'Attendance cannot be encoded on a date marked as a holiday, weekend, suspension, or non-class day.'})

    @classmethod
    def get_calendar_aware_expected_days(cls, enrollment, start_date=None, end_date=None):
        if not enrollment or not enrollment.academic_year:
            return 0
        expected_days = SchoolCalendarDay.get_expected_school_days(enrollment.academic_year, start_date, end_date)
        if expected_days:
            return expected_days
        return int(cls.objects.filter(enrollment=enrollment, attendance_date__gte=start_date if start_date else None, attendance_date__lte=end_date if end_date else None).aggregate(total=models.Sum('school_days'))['total'] or 0)

    def save(self, *args, **kwargs):
        if self.attendance_date and not self.month:
            self.month = self.attendance_date.strftime('%Y-%m')
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        date_label = self.attendance_date or self.month
        return f"{self.enrollment} - {date_label}"
