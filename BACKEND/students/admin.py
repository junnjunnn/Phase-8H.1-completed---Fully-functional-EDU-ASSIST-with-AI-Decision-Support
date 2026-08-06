from django.contrib import admin
from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'lrn', 'student_status', 'created_at')
    search_fields = ('lrn', 'first_name', 'last_name')
    list_filter = ('student_status',)
    ordering = ('last_name', 'first_name')

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
    full_name.short_description = 'Name'
