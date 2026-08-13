from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Student(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('graduated', 'Graduated'),
        ('transferred', 'Transferred'),
        ('archived', 'Archived'),
    ]

    lrn = models.CharField(max_length=12, unique=True, blank=True, null=True, db_index=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, default='')
    last_name = models.CharField(max_length=100)
    suffix = models.CharField(max_length=20, blank=True, default='')
    gender = models.CharField(max_length=20, blank=True, default='')
    birth_date = models.DateField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, default='')
    guardian_name = models.CharField(max_length=150, blank=True, default='')
    parent_contact = models.CharField(max_length=50, blank=True, default='')
    email = models.EmailField(max_length=255, blank=True, default='')
    student_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['student_status']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()
