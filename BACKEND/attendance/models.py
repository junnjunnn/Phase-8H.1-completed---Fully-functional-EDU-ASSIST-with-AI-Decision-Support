from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from academics.models import Enrollment


class AttendanceRecord(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='attendance_records')
    month = models.CharField(max_length=20)
    school_days = models.PositiveIntegerField(default=0)
    days_present = models.PositiveIntegerField(default=0)
    absences = models.PositiveIntegerField(default=0)
    times_tardy = models.PositiveIntegerField(default=0)
    encoded_by = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.SET_NULL, related_name='encoded_attendance_records')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('enrollment', 'month')
        ordering = ['-created_at']
        indexes = [models.Index(fields=['enrollment', 'month'])]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.days_present > self.school_days:
            raise ValidationError({'days_present': 'Days present cannot exceed school days.'})
        if self.absences < 0:
            raise ValidationError({'absences': 'Absences cannot be negative.'})
        if self.times_tardy < 0:
            raise ValidationError({'times_tardy': 'Tardiness cannot be negative.'})

    def __str__(self):
        return f"{self.enrollment} - {self.month}"
