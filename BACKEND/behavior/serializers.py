from rest_framework import serializers

from common.authorization import authorized_enrollment_queryset
from academics.models import Enrollment
from .models import CoreValue, BehaviorIndicator, BehavioralRating, BehavioralAssessment


class CoreValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoreValue
        fields = ['id', 'name', 'description', 'is_active']


class BehaviorIndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = BehaviorIndicator
        fields = ['id', 'name', 'description', 'core_value', 'is_active']


class BehavioralRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = BehavioralRating
        fields = ['id', 'code', 'label', 'numeric_value', 'description', 'is_active']


class BehavioralAssessmentSerializer(serializers.ModelSerializer):
    rating_code = serializers.CharField(source='rating.code', read_only=True)
    rating_label = serializers.CharField(source='rating.label', read_only=True)
    core_value_name = serializers.CharField(source='core_value.name', read_only=True)
    behavior_indicator_name = serializers.CharField(source='behavior_indicator.name', read_only=True)
    assessed_by_username = serializers.CharField(source='assessed_by.username', read_only=True)

    class Meta:
        model = BehavioralAssessment
        fields = [
            'id',
            'enrollment',
            'academic_year',
            'grading_period_type',
            'quarter',
            'semester',
            'core_value',
            'core_value_name',
            'behavior_indicator',
            'behavior_indicator_name',
            'rating',
            'rating_code',
            'rating_label',
            'numeric_score',
            'assessed_by',
            'assessed_by_username',
            'assessment_date',
            'remarks',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'rating_code', 'rating_label', 'core_value_name', 'behavior_indicator_name', 'assessed_by_username']

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
