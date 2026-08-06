from django.contrib import admin
from .models import RiskPrediction, PredictionFactor


@admin.register(RiskPrediction)
class RiskPredictionAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'prediction_type', 'risk_level', 'probability', 'review_status', 'prediction_date')
    list_filter = ('prediction_type', 'risk_level', 'review_status')
    search_fields = ('enrollment__student__first_name', 'enrollment__student__last_name')


@admin.register(PredictionFactor)
class PredictionFactorAdmin(admin.ModelAdmin):
    list_display = ('prediction', 'feature_name', 'contribution', 'direction')
    search_fields = ('feature_name', 'explanation_text')
