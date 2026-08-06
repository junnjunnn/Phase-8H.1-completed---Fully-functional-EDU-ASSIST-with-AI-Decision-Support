from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role_name', 'department', 'employee_id', 'created_at')
    list_filter = ('role_name', 'department')
    search_fields = ('user__username', 'employee_id', 'department')
    ordering = ('-created_at',)
