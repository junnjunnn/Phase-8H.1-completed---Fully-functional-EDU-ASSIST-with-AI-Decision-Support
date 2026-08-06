from django.contrib import admin
from .models import Intervention


@admin.register(Intervention)
class InterventionAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'intervention_type', 'status', 'priority', 'start_date', 'end_date')
    list_filter = ('status', 'priority', 'intervention_type')
    search_fields = ('enrollment__student__first_name', 'enrollment__student__last_name', 'recommendation')
