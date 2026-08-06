from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'module', 'object_type', 'object_id')
    list_filter = ('action', 'module')
    search_fields = ('module', 'object_type', 'object_id')
    ordering = ('-timestamp',)
