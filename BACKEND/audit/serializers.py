from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_username = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'user_username', 'action', 'module', 'object_type', 'object_id', 'timestamp', 'ip_address']
        read_only_fields = ['id', 'user', 'user_username', 'timestamp']

    def get_user_username(self, obj):
        return obj.user.username if obj.user else None
