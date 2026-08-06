from rest_framework import serializers

from .models import Intervention


class InterventionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Intervention
        fields = ['id', 'enrollment', 'risk_type', 'intervention_type', 'recommendation', 'assigned_personnel', 'status', 'priority', 'notes', 'start_date', 'end_date', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
