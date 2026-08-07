from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.utils import timezone
from students.models import Student


class AcademicYear(models.Model):
    name = models.CharField(max_length=20, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        indexes = [models.Index(fields=['is_active'])]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError({'end_date': 'End date cannot be earlier than start date.'})
        if self.is_active:
            active_years = AcademicYear.objects.filter(is_active=True).exclude(pk=self.pk)
            if active_years.exists():
                raise ValidationError({'is_active': 'Only one academic year can be active at a time.'})

    def __str__(self):
        return self.name


class GradeLevel(models.Model):
    SCHOOL_LEVEL_CHOICES = [
        ('Elementary', 'Elementary'),
        ('Junior High School', 'Junior High School'),
        ('Senior High School', 'Senior High School'),
    ]
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=20, unique=True)
    school_level = models.CharField(max_length=30, choices=SCHOOL_LEVEL_CHOICES)
    order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']
        indexes = [models.Index(fields=['is_active', 'school_level'])]

    def __str__(self):
        return self.name


class Section(models.Model):
    grade_level = models.ForeignKey(GradeLevel, on_delete=models.CASCADE, related_name='sections')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='sections')
    name = models.CharField(max_length=50)
    capacity = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True, default='')
    adviser = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.SET_NULL, related_name='advised_sections')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('grade_level', 'academic_year', 'name')
        ordering = ['grade_level__order', 'name']
        indexes = [models.Index(fields=['academic_year', 'grade_level', 'is_active'])]

    def __str__(self):
        return f"{self.grade_level} - {self.name}"


class Strand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True, blank=True)
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        indexes = [models.Index(fields=['is_active'])]

    def __str__(self):
        return self.name


class Subject(models.Model):
    CATEGORY_CHOICES = [
        ('Learning Area', 'Learning Area'),
        ('Core', 'Core'),
        ('Applied', 'Applied'),
        ('Specialized', 'Specialized'),
    ]
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, default='')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    grade_level = models.ForeignKey(GradeLevel, on_delete=models.CASCADE, related_name='subjects', null=True, blank=True)
    strand = models.ForeignKey(Strand, on_delete=models.SET_NULL, related_name='subjects', null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        indexes = [models.Index(fields=['grade_level', 'is_active']), models.Index(fields=['strand', 'is_active'])]

    def __str__(self):
        return f"{self.code} - {self.name}"


class TeacherAssignment(models.Model):
    teacher = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='teacher_assignments')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='teacher_assignments')
    grade_level = models.ForeignKey(GradeLevel, on_delete=models.CASCADE, related_name='teacher_assignments')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='teacher_assignments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='teacher_assignments')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('teacher', 'academic_year', 'grade_level', 'section', 'subject')
        ordering = ['-created_at']
        indexes = [models.Index(fields=['teacher', 'is_active']), models.Index(fields=['academic_year', 'grade_level'])]

    def __str__(self):
        return f"{self.teacher} - {self.section} - {self.subject}"


class Enrollment(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('transferred', 'Transferred'),
        ('graduated', 'Graduated'),
        ('withdrawn', 'Withdrawn'),
        ('inactive', 'Inactive'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='enrollments')
    grade_level = models.ForeignKey(GradeLevel, on_delete=models.CASCADE, related_name='enrollments')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='enrollments', null=True, blank=True)
    strand = models.ForeignKey(Strand, on_delete=models.SET_NULL, related_name='enrollments', null=True, blank=True)
    enrollment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    enrollment_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'academic_year')
        ordering = ['-academic_year__start_date', 'student__last_name']
        indexes = [
            models.Index(fields=['academic_year', 'grade_level']),
            models.Index(fields=['enrollment_status']),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.section and self.section.grade_level_id != self.grade_level_id:
            raise ValidationError({'section': 'The selected section does not belong to the selected grade level.'})

    def __str__(self):
        return f"{self.student} - {self.academic_year}"


class AcademicRecord(models.Model):
    GRADING_PERIOD_CHOICES = [
        ('Quarter', 'Quarter'),
        ('Semester', 'Semester'),
    ]
    QUARTER_CHOICES = [(i, f'Quarter {i}') for i in range(1, 5)]
    SEMESTER_CHOICES = [(1, 'Semester 1'), (2, 'Semester 2')]

    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='academic_records')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='academic_records')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='academic_records')
    grading_period_type = models.CharField(max_length=20, choices=GRADING_PERIOD_CHOICES)
    quarter = models.PositiveIntegerField(null=True, blank=True, choices=QUARTER_CHOICES)
    semester = models.PositiveIntegerField(null=True, blank=True, choices=SEMESTER_CHOICES)
    grade = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    final_grade = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    remarks = models.TextField(blank=True, default='')
    encoded_by = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.SET_NULL, related_name='encoded_academic_records')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('enrollment', 'subject', 'academic_year', 'grading_period_type', 'quarter', 'semester')
        indexes = [models.Index(fields=['academic_year', 'grading_period_type', 'quarter', 'semester'])]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.grading_period_type == 'Quarter':
            if not self.quarter:
                raise ValidationError({'quarter': 'Quarter is required when using quarter-based grading.'})
            if self.semester:
                raise ValidationError({'semester': 'Semester must be blank when quarter grading is used.'})
        elif self.grading_period_type == 'Semester':
            if not self.semester:
                raise ValidationError({'semester': 'Semester is required when using semester-based grading.'})
            if self.quarter:
                raise ValidationError({'quarter': 'Quarter must be blank when semester grading is used.'})

    def __str__(self):
        return f"{self.enrollment} - {self.subject}"
