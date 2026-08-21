from django.db import transaction
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from audit.models import AuditLog
from accounts.permissions import IsAuthorizedStaff, IsSchoolAdmin
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
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active']

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return [permissions.IsAuthenticated(), IsSchoolAdmin()]
        return [permissions.IsAuthenticated(), IsAuthorizedStaff()]


class BehaviorIndicatorViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = BehaviorIndicator.objects.select_related('core_value').all()
    serializer_class = BehaviorIndicatorSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorizedStaff]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['core_value', 'is_active']

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return [permissions.IsAuthenticated(), IsSchoolAdmin()]
        return [permissions.IsAuthenticated(), IsAuthorizedStaff()]


class BehavioralRatingViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = BehavioralRating.objects.all()
    serializer_class = BehavioralRatingSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorizedStaff]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active']

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH']:
            return [permissions.IsAuthenticated(), IsSchoolAdmin()]
        return [permissions.IsAuthenticated(), IsAuthorizedStaff()]


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

    @action(detail=False, methods=['post'], url_path='bulk')
    def bulk_create_or_update(self, request):
        if not isinstance(request.data, list):
            raise ValidationError({'detail': 'Bulk behavior payload must be a list of records.'})

        results = []
        with transaction.atomic():
            for index, item in enumerate(request.data):
                if not isinstance(item, dict):
                    raise ValidationError({'detail': f'Record at index {index} must be an object.'})

                record_id = item.get('id')
                instance = None
                if record_id:
                    instance = self.get_queryset().filter(pk=record_id).first()
                    if instance is None:
                        raise ValidationError({'detail': f'Behavior assessment {record_id} was not found or is not authorized.'})
                else:
                    unique_fields = {
                        'enrollment_id': item.get('enrollment'),
                        'academic_year_id': item.get('academic_year'),
                        'core_value_id': item.get('core_value'),
                        'behavior_indicator_id': item.get('behavior_indicator'),
                        'grading_period_type': item.get('grading_period_type'),
                    }
                    period_value = item.get('quarter') if item.get('grading_period_type') == 'Quarter' else item.get('semester')
                    period_field = 'quarter' if item.get('grading_period_type') == 'Quarter' else 'semester'
                    if period_value is not None and all(value is not None for value in unique_fields.values()):
                        instance = BehavioralAssessment.objects.filter(**unique_fields, **{period_field: period_value}).first()

                serializer = self.get_serializer(instance, data=item, partial=bool(instance), context={'request': request})
                serializer.is_valid(raise_exception=True)
                saved = serializer.save(assessed_by=request.user if request.user.is_authenticated else None)
                AuditLog.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='UPDATE' if instance else 'CREATE',
                    module=self.serializer_class.Meta.model._meta.app_label,
                    object_type=self.serializer_class.Meta.model.__name__,
                    object_id=str(saved.pk),
                )
                results.append(saved)

        return Response({'results': self.get_serializer(results, many=True).data, 'count': len(results)}, status=201)
