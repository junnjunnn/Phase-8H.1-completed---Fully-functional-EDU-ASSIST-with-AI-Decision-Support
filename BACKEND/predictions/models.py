from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from academics.models import Enrollment


class RiskPrediction(models.Model):
    PREDICTION_TYPE_CHOICES = [
        ('Academic Risk', 'Academic Risk'),
        ('Behavioral Risk', 'Behavioral Risk'),
        ('Combined Student Support Risk', 'Combined Student Support Risk'),
    ]
    RISK_LEVEL_CHOICES = [('Low', 'Low'), ('Moderate', 'Moderate'), ('High', 'High')]

    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='risk_predictions')
    prediction_type = models.CharField(max_length=50, choices=PREDICTION_TYPE_CHOICES)
    risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES)
    probability = models.DecimalField(max_digits=5, decimal_places=4, validators=[MinValueValidator(0), MaxValueValidator(1)])
    model_name = models.CharField(max_length=100, blank=True, default='')
    model_version = models.CharField(max_length=50, blank=True, default='')
    prediction_date = models.DateTimeField(auto_now_add=True)
    explanation = models.TextField(blank=True, default='')
    review_status = models.CharField(max_length=20, default='Pending')
    reviewed_by = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_predictions')
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-prediction_date']
        indexes = [models.Index(fields=['prediction_date', 'risk_level'])]

    def __str__(self):
        return f"{self.enrollment} - {self.risk_level}"


class PredictionFactor(models.Model):
    prediction = models.ForeignKey(RiskPrediction, on_delete=models.CASCADE, related_name='prediction_factors')
    feature_name = models.CharField(max_length=100)
    feature_value = models.CharField(max_length=200, blank=True, default='')
    contribution = models.DecimalField(max_digits=5, decimal_places=4, validators=[MinValueValidator(0), MaxValueValidator(1)], null=True, blank=True)
    direction = models.CharField(max_length=20, blank=True, default='')
    explanation_text = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['prediction', 'feature_name']
        indexes = [models.Index(fields=['prediction', 'feature_name'])]

    def __str__(self):
        return self.feature_name
