from django.conf import settings
from django.db import models


class UserProfileManager(models.Manager):
    def create(self, **kwargs):
        user = kwargs.get('user')
        if user is not None:
            existing = self.filter(user=user).first()
            if existing is not None:
                changed_fields = []
                for field_name in ('role_name', 'employee_id', 'department', 'phone_number'):
                    if field_name in kwargs and getattr(existing, field_name) != kwargs[field_name]:
                        setattr(existing, field_name, kwargs[field_name])
                        changed_fields.append(field_name)
                if changed_fields:
                    existing.save(update_fields=changed_fields)
                user._profile_cache = existing
                return existing
        profile = super().create(**kwargs)
        if user is not None:
            user._profile_cache = profile
        return profile


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

    objects = UserProfileManager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} ({self.role_name})"

    @property
    def role(self):
        return self.role_name

    def has_role(self, *roles):
        return self.role_name in roles
