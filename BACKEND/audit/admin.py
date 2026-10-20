from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'module', 'object_type', 'object_id', 'object_name', 'previous_status', 'new_status')
    list_filter = ('action', 'module', 'previous_status', 'new_status')
    search_fields = ('module', 'object_type', 'object_id', 'object_name', 'reason')
    ordering = ('-timestamp',)
