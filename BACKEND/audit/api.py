from rest_framework import permissions, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import AuditLog
from .serializers import AuditLogSerializer
from accounts.permissions import IsSchoolAdmin


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.select_related('user').all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsSchoolAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['action', 'module', 'object_type', 'object_id', 'user__username', 'ip_address']
    search_fields = ['action', 'module', 'object_type', 'object_id', 'user__username', 'ip_address']
    ordering_fields = ['timestamp', 'action', 'module']
    ordering = ['-timestamp']
