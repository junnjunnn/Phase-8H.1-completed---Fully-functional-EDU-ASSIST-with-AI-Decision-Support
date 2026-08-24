from rest_framework import serializers

from common.authorization import authorized_enrollment_queryset
from academics.models import Enrollment
from .models import CoreValue, BehaviorIndicator, BehavioralRating, BehavioralAssessment
from .reference_data import DEPED_RATINGS


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

    def validate_core_value(self, value):
        """Ensure that only active (canonical) core values can be used for new behavioral assessments."""
        if not value.is_active:
            raise serializers.ValidationError(
                f'Core value "{value.name}" is not active and cannot be used for new behavioral assessments. '
                f'Select a canonical DepEd core value: Maka-Diyos, Makatao, Maka-Kalikasan, or Makabansa.'
            )
        return value

    def validate_behavior_indicator(self, value):
        """Ensure that only active behavior indicators can be used for new behavioral assessments."""
        if not value.is_active:
            raise serializers.ValidationError(
                f'Behavior indicator "{value.name}" is not active and cannot be used for new behavioral assessments.'
            )
        return value

    def validate(self, attrs):
        enrollment = attrs.get('enrollment') or getattr(self.instance, 'enrollment', None)
        academic_year = attrs.get('academic_year') or getattr(self.instance, 'academic_year', None)
        core_value = attrs.get('core_value') or getattr(self.instance, 'core_value', None)
        behavior_indicator = attrs.get('behavior_indicator') or getattr(self.instance, 'behavior_indicator', None)
        rating = attrs.get('rating') or getattr(self.instance, 'rating', None)
        grading_period_type = attrs.get('grading_period_type') or getattr(self.instance, 'grading_period_type', None)
        quarter = attrs.get('quarter') if 'quarter' in attrs else getattr(self.instance, 'quarter', None)
        semester = attrs.get('semester') if 'semester' in attrs else getattr(self.instance, 'semester', None)

        if academic_year and not academic_year.is_active:
            raise serializers.ValidationError({'academic_year': 'Cannot save behavior assessments for an archived academic year.'})

        if core_value and behavior_indicator and behavior_indicator.core_value_id != core_value.id:
            raise serializers.ValidationError({'behavior_indicator': 'The behavior indicator must belong to the selected Core Value.'})

        allowed_codes = {item['code'] for item in DEPED_RATINGS}
        if rating and rating.code not in allowed_codes:
            raise serializers.ValidationError({'rating': 'Select a valid DepEd observed-values rating.'})
        if rating and not rating.is_active:
            raise serializers.ValidationError({'rating': 'The selected rating is inactive.'})

        if grading_period_type == 'Quarter':
            if quarter is None:
                raise serializers.ValidationError({'quarter': 'Quarter is required when grading_period_type is Quarter.'})
            if semester is not None:
                raise serializers.ValidationError({'semester': 'Semester must be blank when grading_period_type is Quarter.'})
        elif grading_period_type == 'Semester':
            if semester is None:
                raise serializers.ValidationError({'semester': 'Semester is required when grading_period_type is Semester.'})
            if quarter is not None:
                raise serializers.ValidationError({'quarter': 'Quarter must be blank when grading_period_type is Semester.'})

        if enrollment and academic_year and enrollment.academic_year_id != academic_year.id:
            raise serializers.ValidationError({'academic_year': 'The academic year must match the enrollment.'})

        return attrs
