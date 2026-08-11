from rest_framework import mixins, permissions, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from audit.models import AuditLog
from accounts.permissions import IsAuthorizedStaff
from accounts.utils import get_authorized_enrollment_queryset, get_user_scope
from academics.models import Enrollment
from .models import Intervention
from .serializers import InterventionSerializer


class InterventionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = Intervention.objects.select_related('enrollment', 'assigned_personnel').all()
    serializer_class = InterventionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorizedStaff]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['enrollment', 'enrollment__student', 'risk_type', 'intervention_type', 'assigned_personnel', 'status', 'priority']
    search_fields = ['enrollment__student__first_name', 'enrollment__student__last_name', 'risk_type', 'intervention_type', 'notes']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return get_authorized_enrollment_queryset(self.request.user, super().get_queryset(), enrollment_field='enrollment')

    def _authorize_enrollment(self, enrollment):
        if get_user_scope(self.request.user) != 'teacher':
            return

        authorized_enrollments = get_authorized_enrollment_queryset(self.request.user, Enrollment.objects.all())
        if not authorized_enrollments.filter(pk=enrollment.pk).exists():
            raise PermissionDenied('You are not authorized to create or modify interventions for this enrollment.')

    def perform_create(self, serializer):
        self._authorize_enrollment(serializer.validated_data['enrollment'])
        instance = serializer.save()
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='CREATE',
            module=self.serializer_class.Meta.model._meta.app_label,
            object_type=self.serializer_class.Meta.model.__name__,
            object_id=str(instance.pk),
        )

    def perform_update(self, serializer):
        enrollment = serializer.validated_data.get('enrollment', serializer.instance.enrollment)
        self._authorize_enrollment(enrollment)
        instance = serializer.save()
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='UPDATE',
            module=self.serializer_class.Meta.model._meta.app_label,
            object_type=self.serializer_class.Meta.model.__name__,
            object_id=str(instance.pk),
        )

    def perform_destroy(self, instance):
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='DELETE',
            module=self.serializer_class.Meta.model._meta.app_label,
            object_type=self.serializer_class.Meta.model.__name__,
            object_id=str(instance.pk),
        )
        instance.delete()
