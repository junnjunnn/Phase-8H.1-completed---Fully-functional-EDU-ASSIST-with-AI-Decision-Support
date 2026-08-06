from rest_framework import serializers

from .models import PredictionFactor, RiskPrediction


class RiskPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskPrediction
        fields = ['id', 'enrollment', 'prediction_type', 'risk_level', 'probability', 'model_name', 'model_version', 'prediction_date', 'explanation', 'review_status', 'reviewed_by', 'reviewed_at']
        read_only_fields = ['prediction_date']


class PredictionFactorSerializer(serializers.ModelSerializer):
    class Meta:
        model = PredictionFactor
        fields = ['id', 'prediction', 'feature_name', 'feature_value', 'contribution', 'direction', 'explanation_text']
