from rest_framework import serializers

from common.authorization import active_enrollment_queryset, authorized_enrollment_queryset
from academics.models import Enrollment
from .models import PredictionFactor, RiskPrediction


class RiskPredictionSerializer(serializers.ModelSerializer):
    student_id = serializers.IntegerField(source='enrollment.student_id', read_only=True)
    student_name = serializers.SerializerMethodField()
    grade_level_name = serializers.CharField(source='enrollment.grade_level.name', read_only=True)
    section_name = serializers.CharField(source='enrollment.section.name', read_only=True)
    academic_year_name = serializers.CharField(source='enrollment.academic_year.name', read_only=True)

    class Meta:
        model = RiskPrediction
        fields = ['id', 'enrollment', 'student_id', 'student_name', 'grade_level_name', 'section_name', 'academic_year_name', 'prediction_type', 'risk_level', 'probability', 'model_name', 'model_version', 'prediction_date', 'explanation', 'review_status', 'reviewed_by', 'reviewed_at']
        read_only_fields = ['prediction_date']

    def get_student_name(self, instance):
        student = instance.enrollment.student
        return f'{student.first_name} {student.last_name}'.strip()

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

        if not active_enrollment_queryset(Enrollment.objects.filter(pk=value.pk)).exists():
            raise serializers.ValidationError(
                'Predictions can only be created for active students with a current academic context.'
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
