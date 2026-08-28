from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'title', 'message', 'calendar_entry', 'recurring_event', 'scheduled_for', 'read_at', 'expires_at', 'created_at']
        read_only_fields = fields