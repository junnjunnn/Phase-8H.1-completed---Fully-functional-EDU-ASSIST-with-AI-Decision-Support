from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import IntegrityError
import uuid
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
        if self.start_date and self.end_date:
            if self.start_date == self.end_date:
                raise ValidationError({'end_date': 'End date must be different from start date.'})
            if self.start_date > self.end_date:
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
    strand = models.ForeignKey('Strand', on_delete=models.SET_NULL, related_name='sections', null=True, blank=True)
    specialization = models.ForeignKey('Specialization', on_delete=models.SET_NULL, related_name='sections', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('grade_level', 'academic_year', 'name')
        ordering = ['grade_level__order', 'name']
        indexes = [models.Index(fields=['academic_year', 'grade_level', 'is_active']), models.Index(fields=['strand', 'is_active'])]

    def clean(self):
        from django.core.exceptions import ValidationError

        # Validate that grade level and academic year are active (not archived)
        if self.grade_level and not self.grade_level.is_active:
            raise ValidationError({'grade_level': 'Cannot create section with an archived grade level.'})

        if self.academic_year and not self.academic_year.is_active:
            raise ValidationError({'academic_year': 'Cannot create section in an archived academic year.'})

        # Validate strand/grade level compatibility
        if not self.grade_level:
            return

        school_level = self.grade_level.school_level

        # Rule: Elementary sections cannot have a strand
        if school_level == 'Elementary' and self.strand:
            raise ValidationError({'strand': 'Elementary sections cannot have a strand.'})

        if school_level == 'Elementary' and self.specialization:
            raise ValidationError({'specialization': 'Elementary sections cannot have a specialization.'})

        # Rule: Junior High School sections cannot have a strand
        if school_level == 'Junior High School' and self.strand:
            raise ValidationError({'strand': 'Junior High School sections cannot have a strand.'})

        if school_level == 'Junior High School' and self.specialization:
            raise ValidationError({'specialization': 'Junior High School sections cannot have a specialization.'})

        # Rule: Senior High School sections require a strand
        if school_level == 'Senior High School' and not self.strand:
            raise ValidationError({'strand': 'Senior High School sections must have a strand.'})

        if self.strand and self.strand.code == 'TVL' and not self.specialization:
            raise ValidationError({'specialization': 'TVL sections must have a specialization.'})

        if self.specialization and self.specialization.strand_id != self.strand_id:
            raise ValidationError({'specialization': 'The selected specialization does not belong to the selected strand.'})

        # Rule: Strand must be active
        if self.strand and not self.strand.is_active:
            raise ValidationError({'strand': 'The selected strand is not active.'})

    def __str__(self):
        strand_info = f" - {self.strand.code}" if self.strand else ""
        return f"{self.grade_level}{strand_info} - {self.name}"


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


class Specialization(models.Model):
    strand = models.ForeignKey(Strand, on_delete=models.CASCADE, related_name='specializations')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        constraints = [models.UniqueConstraint(fields=['strand', 'name'], name='unique_specialization_per_strand')]
        indexes = [models.Index(fields=['strand', 'is_active'])]

    def __str__(self):
        return f'{self.strand.name} - {self.name}'


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
    grade_levels = models.ManyToManyField(GradeLevel, related_name='applicable_subjects', blank=True)
    strand = models.ForeignKey(Strand, on_delete=models.SET_NULL, related_name='subjects', null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        indexes = [models.Index(fields=['grade_level', 'is_active']), models.Index(fields=['strand', 'is_active'])]

    @property
    def educational_level(self):
        """Derive educational level from grade_level."""
        grade = self.grade_level or self.grade_levels.order_by('order', 'name').first()
        if not grade:
            return None
        return grade.school_level

    def clean(self):
        from django.core.exceptions import ValidationError

        # Validate that grade level is active (not archived)
        if self.grade_level and not self.grade_level.is_active:
            raise ValidationError({'grade_level': 'Cannot create subject with an archived grade level.'})

        if not self.grade_level:
            return

        school_level = self.grade_level.school_level

        # Rule: Elementary subjects cannot have a strand
        if school_level == 'Elementary' and self.strand:
            raise ValidationError({'strand': 'Elementary subjects cannot have a strand.'})

        # Rule: Junior High School subjects cannot have a strand
        if school_level == 'Junior High School' and self.strand:
            raise ValidationError({'strand': 'Junior High School subjects cannot have a strand.'})

        # Rule: Senior High School subjects can have optional strand
        # Rule: SHS subjects with inactive strand should be rejected
        if school_level == 'Senior High School' and self.strand and not self.strand.is_active:
            raise ValidationError({'strand': 'The selected strand is not active.'})

        # Rule: Category validation - SHS categories should only be used for SHS
        shs_categories = {'Core', 'Applied', 'Specialized'}
        if school_level != 'Senior High School' and self.category in shs_categories:
            raise ValidationError({'category': f'Category "{self.category}" is only available for Senior High School subjects.'})

        # Rule: Elementary and JHS should use "Learning Area" category
        if school_level in ['Elementary', 'Junior High School'] and self.category != 'Learning Area':
            raise ValidationError({'category': f'Elementary and Junior High School subjects must use "Learning Area" category.'})

    def __str__(self):
        return f"{self.code} - {self.name}"

    def save(self, *args, **kwargs):
        if self.code and self.code.strip():
            return super().save(*args, **kwargs)

        for _ in range(5):
            self.code = f'SUBJ-{uuid.uuid4().hex[:12].upper()}'
            try:
                return super().save(*args, **kwargs)
            except IntegrityError:
                self.code = ''
        raise IntegrityError('Could not generate a unique subject identifier.')


class TeacherAssignment(models.Model):
    ASSIGNMENT_TYPE_CHOICES = [
        ('SUBJECT', 'Subject Teacher'),
        ('ADVISER', 'Class Adviser'),
    ]
    teacher = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='teacher_assignments')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='teacher_assignments')
    grade_level = models.ForeignKey(GradeLevel, on_delete=models.CASCADE, related_name='teacher_assignments')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='teacher_assignments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='teacher_assignments', null=True, blank=True)
    assignment_type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPE_CHOICES, default='SUBJECT')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['teacher', 'academic_year', 'grade_level', 'section', 'subject'],
                condition=models.Q(is_active=True),
                name='unique_active_subject_teacher_assignment',
            ),
            models.UniqueConstraint(
                fields=['academic_year', 'section'],
                condition=models.Q(is_active=True, assignment_type='ADVISER'),
                name='unique_active_section_adviser_assignment',
            ),
            models.CheckConstraint(
                condition=(models.Q(assignment_type='ADVISER', subject__isnull=True) | models.Q(assignment_type='SUBJECT', subject__isnull=False)),
                name='assignment_subject_matches_type',
            ),
        ]
        indexes = [models.Index(fields=['teacher', 'is_active', 'assignment_type']), models.Index(fields=['academic_year', 'grade_level'])]

    def __str__(self):
        role = 'Class Adviser' if self.assignment_type == 'ADVISER' else str(self.subject)
        return f"{self.teacher} - {self.section} - {role}"


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
    enrollment_date = models.DateField(default=timezone.localdate)
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

        # Validate that academic year and grade level are active (not archived)
        if self.academic_year and not self.academic_year.is_active:
            raise ValidationError({'academic_year': 'Cannot create enrollment in an archived academic year.'})

        if self.grade_level and not self.grade_level.is_active:
            raise ValidationError({'grade_level': 'Cannot enroll student in an archived grade level.'})

        # Validate that section and strand are active
        if self.section and not self.section.is_active:
            raise ValidationError({'section': 'Cannot enroll student in an archived section.'})

        if self.strand and not self.strand.is_active:
            raise ValidationError({'strand': 'Cannot use an archived strand for enrollment.'})

        # Existing validations
        if self.section and self.section.grade_level_id != self.grade_level_id:
            raise ValidationError({'section': 'The selected section does not belong to the selected grade level.'})

        # Validate strand consistency with section
        if self.section and self.section.strand and self.strand and self.section.strand.id != self.strand.id:
            raise ValidationError({'strand': 'The selected strand does not match the section\'s strand.'})

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

        # Validate that academic year is active (not archived)
        if self.academic_year and not self.academic_year.is_active:
            raise ValidationError({'academic_year': 'Cannot encode grades for an archived academic year.'})

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
