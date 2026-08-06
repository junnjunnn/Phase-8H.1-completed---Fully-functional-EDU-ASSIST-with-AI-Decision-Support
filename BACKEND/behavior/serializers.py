from rest_framework import serializers

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
