from rest_framework import mixins, permissions, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import IsAuthorizedStaff
from common.audit import AuditMixin
from common.drf_filters import RoleScopedViewsetMixin
from .models import AttendanceRecord
from .serializers import AttendanceRecordSerializer


class AttendanceRecordViewSet(RoleScopedViewsetMixin, AuditMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    scope_field = 'enrollment'
    queryset = AttendanceRecord.objects.select_related('enrollment', 'encoded_by').all()
    serializer_class = AttendanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorizedStaff]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['month', 'enrollment', 'enrollment__student', 'encoded_by']
    search_fields = ['enrollment__student__first_name', 'enrollment__student__last_name', 'month']
    ordering_fields = ['created_at', 'school_days', 'days_present', 'absences']
    ordering = ['-created_at']
