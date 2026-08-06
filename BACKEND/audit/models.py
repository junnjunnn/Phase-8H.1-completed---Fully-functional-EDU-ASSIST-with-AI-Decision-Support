from django.db import models
from django.contrib.auth import get_user_model


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'CREATE'),
        ('UPDATE', 'UPDATE'),
        ('DELETE', 'DELETE'),
        ('LOGIN_SUCCESS', 'LOGIN_SUCCESS'),
        ('LOGIN_FAILED', 'LOGIN_FAILED'),
        ('LOGOUT', 'LOGOUT'),
        ('ACCOUNT_ACTIVATED', 'ACCOUNT_ACTIVATED'),
        ('ACCOUNT_DEACTIVATED', 'ACCOUNT_DEACTIVATED'),
        ('PASSWORD_CHANGED', 'PASSWORD_CHANGED'),
        ('USER_CREATED', 'USER_CREATED'),
        ('VIEW_SENSITIVE_RECORD', 'VIEW_SENSITIVE_RECORD'),
        ('EXPORT_REPORT', 'EXPORT_REPORT'),
        ('PREDICTION_GENERATED', 'PREDICTION_GENERATED'),
        ('INTERVENTION_CREATED', 'INTERVENTION_CREATED'),
    ]
    user = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.SET_NULL, related_name='audit_logs')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    module = models.CharField(max_length=100)
    object_type = models.CharField(max_length=100, blank=True, default='')
    object_id = models.CharField(max_length=100, blank=True, default='')
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [models.Index(fields=['user', 'timestamp']), models.Index(fields=['module', 'action'])]

    def __str__(self):
        return f"{self.action} - {self.module}"