from django.db import models
from django.contrib.auth import get_user_model
from academics.models import Enrollment


class Intervention(models.Model):
    CATEGORY_CHOICES = [
        ('Academic Monitoring', 'Academic Monitoring'),
        ('Tutoring', 'Tutoring'),
        ('Counseling', 'Counseling'),
        ('Parent/Guardian Conference', 'Parent/Guardian Conference'),
        ('Attendance Monitoring', 'Attendance Monitoring'),
        ('Mentoring', 'Mentoring'),
        ('Guidance Referral', 'Guidance Referral'),
        ('Behavioral Monitoring', 'Behavioral Monitoring'),
    ]
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]
    PRIORITY_CHOICES = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High')]

    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='interventions')
    risk_type = models.CharField(max_length=50, default='Academic Risk')
    intervention_type = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    recommendation = models.TextField(blank=True, default='')
    assigned_personnel = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_interventions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    notes = models.TextField(blank=True, default='')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['status', 'priority'])]

    def __str__(self):
        return f"{self.enrollment} - {self.intervention_type}"
