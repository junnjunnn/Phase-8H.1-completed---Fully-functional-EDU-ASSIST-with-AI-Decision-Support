from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from academics.models import Enrollment


class CoreValue(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class BehaviorIndicator(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, default='')
    core_value = models.ForeignKey(CoreValue, on_delete=models.CASCADE, related_name='indicators')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        unique_together = ('name', 'core_value')

    def __str__(self):
        return self.name


class BehavioralRating(models.Model):
    code = models.CharField(max_length=10, unique=True)
    label = models.CharField(max_length=50)
    numeric_value = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.label}"


class BehavioralAssessment(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='behavioral_assessments')
    academic_year = models.ForeignKey('academics.AcademicYear', on_delete=models.CASCADE, related_name='behavioral_assessments')
    grading_period_type = models.CharField(max_length=20, default='Quarter')
    quarter = models.PositiveIntegerField(null=True, blank=True)
    semester = models.PositiveIntegerField(null=True, blank=True)
    core_value = models.ForeignKey(CoreValue, on_delete=models.CASCADE, related_name='assessments')
    behavior_indicator = models.ForeignKey(BehaviorIndicator, on_delete=models.CASCADE, related_name='assessments')
    rating = models.ForeignKey(BehavioralRating, on_delete=models.SET_NULL, null=True, blank=True, related_name='assessments')
    numeric_score = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(5)], null=True, blank=True)
    assessed_by = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.SET_NULL, related_name='assessed_behavioral_records')
    assessment_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('enrollment', 'academic_year', 'core_value', 'behavior_indicator', 'grading_period_type', 'quarter', 'semester')
        ordering = ['-assessment_date', '-created_at']
        indexes = [models.Index(fields=['academic_year', 'grading_period_type', 'quarter', 'semester'])]

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.grading_period_type == 'Quarter':
            if self.quarter is None:
                raise ValidationError({'quarter': 'Quarter is required when grading_period_type is Quarter.'})
            if self.semester is not None:
                raise ValidationError({'semester': 'Semester must be blank when grading_period_type is Quarter.'})
        elif self.grading_period_type == 'Semester':
            if self.semester is None:
                raise ValidationError({'semester': 'Semester is required when grading_period_type is Semester.'})
            if self.quarter is not None:
                raise ValidationError({'quarter': 'Quarter must be blank when grading_period_type is Semester.'})

        if self.numeric_score is not None and (self.numeric_score < 0 or self.numeric_score > 5):
            raise ValidationError({'numeric_score': 'Numeric score must be between 0 and 5.'})

    def __str__(self):
        return f"{self.enrollment} - {self.core_value}"
