from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('SUPER_ADMIN', 'Super Administrator'),
        ('SCHOOL_ADMIN', 'School Administrator'),
        ('REGISTRAR', 'Registrar'),
        ('TEACHER', 'Teacher'),
        ('GUIDANCE', 'Guidance Personnel'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='profile', on_delete=models.CASCADE)
    role_name = models.CharField(max_length=30, choices=ROLE_CHOICES, default='TEACHER')
    employee_id = models.CharField(max_length=50, blank=True, default='')
    department = models.CharField(max_length=100, blank=True, default='')
    phone_number = models.CharField(max_length=30, blank=True, default='')
    assigned_sections = models.ManyToManyField('academics.Section', blank=True, related_name='authorized_personnel')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} ({self.role_name})"

    @property
    def role(self):
        return self.role_name

    def has_role(self, *roles):
        return self.role_name in roles
