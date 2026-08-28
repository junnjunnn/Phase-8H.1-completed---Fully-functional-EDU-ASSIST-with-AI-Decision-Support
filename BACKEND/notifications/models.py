from django.conf import settings
from django.db import models


class Notification(models.Model):
    TYPE_CHOICES = [
        ('APPROVAL_PENDING', 'Pending approval'),
        ('CALENDAR_EVENT', 'Calendar event'),
        ('EXAMINATION', 'Examination'),
        ('ENROLLMENT_DEADLINE', 'Enrollment deadline'),
        ('ACADEMIC_DEADLINE', 'Academic deadline'),
        ('SUSPENSION', 'Suspension or event'),
    ]

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    calendar_entry = models.ForeignKey('attendance.SchoolCalendarDay', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    recurring_event = models.ForeignKey('attendance.RecurringSchoolCalendarEvent', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    scheduled_for = models.DateTimeField()
    read_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    idempotency_key = models.CharField(max_length=180, unique=True)

    class Meta:
        ordering = ['read_at', '-scheduled_for', '-created_at']
        indexes = [
            models.Index(fields=['recipient', 'read_at']),
            models.Index(fields=['scheduled_for']),
        ]

    def __str__(self):
        return f'{self.recipient} - {self.title}'