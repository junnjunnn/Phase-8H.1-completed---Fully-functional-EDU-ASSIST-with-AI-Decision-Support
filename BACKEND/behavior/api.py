from rest_framework import mixins, permissions, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from audit.models import AuditLog
from accounts.permissions import IsAuthorizedStaff
from accounts.utils import get_authorized_enrollment_queryset
from .models import CoreValue, BehaviorIndicator, BehavioralRating, BehavioralAssessment
from .serializers import (
    CoreValueSerializer,
    BehaviorIndicatorSerializer,
    BehavioralRatingSerializer,
    BehavioralAssessmentSerializer,
)


class CoreValueViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = CoreValue.objects.all()
    serializer_class = CoreValueSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorizedStaff]


class BehaviorIndicatorViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = BehaviorIndicator.objects.select_related('core_value').all()
    serializer_class = BehaviorIndicatorSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorizedStaff]


class BehavioralRatingViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = BehavioralRating.objects.all()
    serializer_class = BehavioralRatingSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorizedStaff]


class BehavioralAssessmentViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = BehavioralAssessment.objects.select_related('enrollment', 'academic_year', 'core_value', 'behavior_indicator', 'rating', 'assessed_by').all()
    serializer_class = BehavioralAssessmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorizedStaff]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['enrollment', 'enrollment__student', 'academic_year', 'grading_period_type', 'quarter', 'semester', 'core_value', 'behavior_indicator', 'rating']
    search_fields = ['enrollment__student__first_name', 'enrollment__student__last_name', 'core_value__name', 'behavior_indicator__name']
    ordering_fields = ['assessment_date', 'created_at']
    ordering = ['-assessment_date']

    def get_queryset(self):
        return get_authorized_enrollment_queryset(self.request.user, super().get_queryset(), enrollment_field='enrollment')

    def perform_create(self, serializer):
        instance = serializer.save(assessed_by=self.request.user if self.request.user.is_authenticated else None)
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='CREATE',
            module=self.serializer_class.Meta.model._meta.app_label,
            object_type=self.serializer_class.Meta.model.__name__,
            object_id=str(instance.pk),
        )

    def perform_update(self, serializer):
        instance = serializer.save(assessed_by=self.request.user if self.request.user.is_authenticated else None)
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='UPDATE',
            module=self.serializer_class.Meta.model._meta.app_label,
            object_type=self.serializer_class.Meta.model.__name__,
            object_id=str(instance.pk),
        )
