from rest_framework import serializers

from common.authorization import authorized_enrollment_queryset
from academics.models import Enrollment
from .models import Intervention


class InterventionSerializer(serializers.ModelSerializer):
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
        
        # Also disallow creating interventions for inactive enrollments (existing validation)
        if getattr(value, 'enrollment_status', None) != 'active':
            raise serializers.ValidationError('Selected enrollment is not active.')
        return value

    class Meta:
        model = Intervention
        fields = ['id', 'enrollment', 'risk_type', 'intervention_type', 'recommendation', 'assigned_personnel', 'status', 'priority', 'notes', 'start_date', 'end_date', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
