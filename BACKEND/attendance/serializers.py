from rest_framework import serializers

from .models import AttendanceRecord


class AttendanceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceRecord
        fields = ['id', 'enrollment', 'month', 'school_days', 'days_present', 'absences', 'times_tardy', 'encoded_by', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
