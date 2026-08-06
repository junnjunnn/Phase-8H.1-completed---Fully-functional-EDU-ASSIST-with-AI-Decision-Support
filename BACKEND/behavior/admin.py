from django.contrib import admin
from .models import CoreValue, BehaviorIndicator, BehavioralRating, BehavioralAssessment


@admin.register(CoreValue)
class CoreValueAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(BehaviorIndicator)
class BehaviorIndicatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'core_value', 'is_active')
    list_filter = ('core_value', 'is_active')
    search_fields = ('name',)


@admin.register(BehavioralRating)
class BehavioralRatingAdmin(admin.ModelAdmin):
    list_display = ('code', 'label', 'numeric_value', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'label')


@admin.register(BehavioralAssessment)
class BehavioralAssessmentAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'academic_year', 'core_value', 'behavior_indicator', 'rating', 'numeric_score')
    list_filter = ('academic_year', 'core_value')
    search_fields = ('enrollment__student__first_name', 'enrollment__student__last_name')
