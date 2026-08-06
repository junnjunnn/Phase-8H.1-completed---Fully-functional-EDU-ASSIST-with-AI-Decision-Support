from django.contrib import admin
from .models import AttendanceRecord


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'month', 'school_days', 'days_present', 'absences', 'times_tardy')
    list_filter = ('month',)
    search_fields = ('enrollment__student__first_name', 'enrollment__student__last_name')
