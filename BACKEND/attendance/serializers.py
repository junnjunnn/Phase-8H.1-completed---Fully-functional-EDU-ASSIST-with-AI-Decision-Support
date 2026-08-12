from rest_framework import serializers

from common.authorization import authorized_enrollment_queryset
from academics.models import Enrollment
from .models import AttendanceRecord


class AttendanceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceRecord
        fields = ['id', 'enrollment', 'month', 'school_days', 'days_present', 'absences', 'times_tardy', 'encoded_by', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

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
