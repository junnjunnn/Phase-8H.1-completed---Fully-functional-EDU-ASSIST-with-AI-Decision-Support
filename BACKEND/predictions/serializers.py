from rest_framework import serializers

from common.authorization import authorized_enrollment_queryset
from academics.models import Enrollment
from .models import PredictionFactor, RiskPrediction


class RiskPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskPrediction
        fields = ['id', 'enrollment', 'prediction_type', 'risk_level', 'probability', 'model_name', 'model_version', 'prediction_date', 'explanation', 'review_status', 'reviewed_by', 'reviewed_at']
        read_only_fields = ['prediction_date']

    def validate_enrollment(self, value):
        """Verify that the user has authorization to access this enrollment."""
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError('Authentication required.')
        
        # Check if the enrollment is in the user's authorized list
        authorized_qs = authorized_enrollment_queryset(
            request.user,
            Enrollment.objects.all(),
            enrollment_field='pk'  # Check the enrollment object itself
        )
        
        if not authorized_qs.filter(pk=value.pk).exists():
            raise serializers.ValidationError(
                'You do not have permission to create records for this enrollment.'
            )
        
        return value


class PredictionFactorSerializer(serializers.ModelSerializer):
    class Meta:
        model = PredictionFactor
        fields = ['id', 'prediction', 'feature_name', 'feature_value', 'contribution', 'direction', 'explanation_text']

    def validate_prediction(self, value):
        """Verify that the user has authorization to create factors for this prediction."""
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError('Authentication required.')
        
        # Check if the prediction's enrollment is in the user's authorized list
        authorized_qs = authorized_enrollment_queryset(
            request.user,
            RiskPrediction.objects.all(),
            enrollment_field='pk'
        )
        
        # Check if the prediction's enrollment is authorized
        if not authorized_qs.filter(pk=value.enrollment_id).exists():
            raise serializers.ValidationError(
                'You do not have permission to create factors for this prediction.'
            )
        
        return value
