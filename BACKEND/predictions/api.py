from django.db.models import Case, Count, IntegerField, Q, When
from rest_framework import mixins, permissions, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import IsAuthorizedStaff
from common.audit import AuditMixin
from common.drf_filters import RoleScopedViewsetMixin
from common.authorization import authorized_students_queryset, authorized_enrollment_queryset
from academics.models import AcademicRecord
from behavior.models import BehavioralAssessment
from interventions.models import Intervention
from students.models import Student
from .models import PredictionFactor, RiskPrediction
from .serializers import PredictionFactorSerializer, RiskPredictionSerializer


class RiskPredictionViewSet(RoleScopedViewsetMixin, AuditMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    scope_field = 'enrollment'
    queryset = RiskPrediction.objects.select_related('enrollment', 'reviewed_by').all()
    serializer_class = RiskPredictionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorizedStaff]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['enrollment__student', 'prediction_type', 'risk_level', 'review_status', 'reviewed_by']
    search_fields = ['enrollment__student__first_name', 'enrollment__student__last_name', 'model_name', 'model_version']
    ordering_fields = ['prediction_date', 'probability']
    ordering = ['-prediction_date']


class PredictionFactorViewSet(RoleScopedViewsetMixin, AuditMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    scope_field = 'prediction__enrollment'
    queryset = PredictionFactor.objects.select_related('prediction').all()
    serializer_class = PredictionFactorSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorizedStaff]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['prediction', 'prediction__enrollment__student', 'feature_name']
    search_fields = ['feature_name', 'feature_value', 'direction', 'explanation_text']
    ordering_fields = ['feature_name']
    ordering = ['feature_name']


class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, IsAuthorizedStaff]

    def list(self, request):
        student_qs = authorized_students_queryset(request.user, Student.objects.all())
        prediction_qs = authorized_enrollment_queryset(request.user, RiskPrediction.objects.select_related('enrollment__student', 'enrollment__grade_level').all(), enrollment_field='enrollment')
        intervention_qs = authorized_enrollment_queryset(request.user, Intervention.objects.select_related('enrollment__student', 'enrollment__grade_level').all(), enrollment_field='enrollment')
        behavior_qs = authorized_enrollment_queryset(request.user, BehavioralAssessment.objects.select_related('enrollment__student', 'rating').all(), enrollment_field='enrollment')

        total_students = student_qs.count()
        total_predictions = prediction_qs.count()
        high_risk_students = prediction_qs.filter(risk_level='High').values('enrollment__student').distinct().count()
        moderate_risk_students = prediction_qs.filter(risk_level='Moderate').values('enrollment__student').distinct().count()
        low_risk_students = prediction_qs.filter(risk_level='Low').values('enrollment__student').distinct().count()
        at_risk_students = prediction_qs.filter(risk_level__in=['High', 'Moderate']).values('enrollment__student').distinct().count()
        not_at_risk_students = prediction_qs.filter(risk_level='Low').values('enrollment__student').distinct().count()

        risk_counts = {item['risk_level']: item['count'] for item in prediction_qs.values('risk_level').annotate(count=Count('id'))}

        intervention_status_distribution = {
            item['status']: item['count']
            for item in intervention_qs.values('status').annotate(count=Count('id'))
        }

        behavior_rating_distribution = {
            item['rating__label'] or item['rating__code']: item['count']
            for item in behavior_qs.values('rating__label', 'rating__code').annotate(count=Count('id'))
        }

        academic_performance_distribution = {
            'Failing': 0,
            'Passing': 0,
            'Good': 0,
            'Excellent': 0,
        }
        for record in AcademicRecord.objects.filter(
            enrollment__in=prediction_qs.values('enrollment')
        ).values_list('final_grade', flat=True):
            if record is None:
                continue
            if record < 75:
                academic_performance_distribution['Failing'] += 1
            elif record < 85:
                academic_performance_distribution['Passing'] += 1
            elif record < 95:
                academic_performance_distribution['Good'] += 1
            else:
                academic_performance_distribution['Excellent'] += 1

        recent_predictions = list(
            prediction_qs.order_by('-prediction_date')[:10].values(
                'id',
                'enrollment__student__first_name',
                'enrollment__student__last_name',
                'enrollment__grade_level__name',
                'risk_level',
                'probability',
                'prediction_date',
                'explanation',
            )
        )

        risk_priority = Case(
            When(risk_level='High', then=3),
            When(risk_level='Moderate', then=2),
            When(risk_level='Low', then=1),
            default=0,
            output_field=IntegerField(),
        )

        attention_students = list(
            prediction_qs.annotate(risk_priority=risk_priority).order_by('-risk_priority', '-probability', '-prediction_date')[:10].values(
                'id',
                'enrollment__student__first_name',
                'enrollment__student__last_name',
                'enrollment__grade_level__name',
                'risk_level',
                'probability',
                'prediction_date',
            )
        )

        recent_completed_interventions = list(
            intervention_qs.filter(status='completed').order_by('-updated_at')[:5].values(
                'id',
                'enrollment__student__first_name',
                'enrollment__student__last_name',
                'intervention_type',
                'status',
                'priority',
                'updated_at',
            )
        )

        recent_prediction_activity = list(
            prediction_qs.order_by('-prediction_date')[:5].values(
                'id',
                'enrollment__student__first_name',
                'enrollment__student__last_name',
                'risk_level',
                'probability',
                'prediction_date',
            )
        )

        return Response({
            'total_students': total_students,
            'total_predictions': total_predictions,
            'at_risk_students': at_risk_students,
            'not_at_risk_students': not_at_risk_students,
            'high_risk_students': high_risk_students,
            'moderate_risk_students': moderate_risk_students,
            'low_risk_students': low_risk_students,
            'risk_distribution': risk_counts,
            'intervention_status_distribution': intervention_status_distribution,
            'behavior_rating_distribution': behavior_rating_distribution,
            'academic_performance_distribution': academic_performance_distribution,
            'recent_predictions': recent_predictions,
            'attention_students': attention_students,
            'recent_completed_interventions': recent_completed_interventions,
            'recent_prediction_activity': recent_prediction_activity,
        })
