from rest_framework import mixins, permissions, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import IsAuthorizedStaff
from .models import Intervention
from .serializers import InterventionSerializer
from common.audit import AuditMixin
from common.drf_filters import RoleScopedViewsetMixin


class InterventionViewSet(RoleScopedViewsetMixin, AuditMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    scope_field = 'enrollment'
    queryset = Intervention.objects.select_related('enrollment', 'assigned_personnel').all()
    serializer_class = InterventionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorizedStaff]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['enrollment', 'enrollment__student', 'risk_type', 'intervention_type', 'assigned_personnel', 'status', 'priority']
    search_fields = ['enrollment__student__first_name', 'enrollment__student__last_name', 'risk_type', 'intervention_type', 'notes']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-created_at']
