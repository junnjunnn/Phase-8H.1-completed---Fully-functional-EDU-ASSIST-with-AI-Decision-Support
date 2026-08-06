"""
URL configuration for config project.
"""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.db import connection
from django.views.decorators.http import require_GET
from rest_framework.routers import DefaultRouter

from students.api import StudentViewSet
from academics.api import (
    AcademicYearViewSet,
    GradeLevelViewSet,
    SectionViewSet,
    StrandViewSet,
    SubjectViewSet,
    EnrollmentViewSet,
    AcademicRecordViewSet,
)
from attendance.api import AttendanceRecordViewSet
from predictions.api import DashboardViewSet
from reports.api import ReportsViewSet
from behavior.api import (
    CoreValueViewSet,
    BehaviorIndicatorViewSet,
    BehavioralRatingViewSet,
    BehavioralAssessmentViewSet,
)
from interventions.api import InterventionViewSet
from predictions.api import RiskPredictionViewSet, PredictionFactorViewSet
from predictions.views import predict_student_view

router = DefaultRouter()
router.register('students', StudentViewSet, basename='student')
router.register('academic-years', AcademicYearViewSet, basename='academic-year')
router.register('grade-levels', GradeLevelViewSet, basename='grade-level')
router.register('sections', SectionViewSet, basename='section')
router.register('strands', StrandViewSet, basename='strand')
router.register('subjects', SubjectViewSet, basename='subject')
router.register('enrollments', EnrollmentViewSet, basename='enrollment')
router.register('academic-records', AcademicRecordViewSet, basename='academic-record')
router.register('attendance-records', AttendanceRecordViewSet, basename='attendance-record')
router.register('core-values', CoreValueViewSet, basename='core-value')
router.register('behavior-indicators', BehaviorIndicatorViewSet, basename='behavior-indicator')
router.register('behavioral-ratings', BehavioralRatingViewSet, basename='behavioral-rating')
router.register('behavioral-assessments', BehavioralAssessmentViewSet, basename='behavioral-assessment')
router.register('interventions', InterventionViewSet, basename='intervention')
router.register('risk-predictions', RiskPredictionViewSet, basename='risk-prediction')
router.register('prediction-factors', PredictionFactorViewSet, basename='prediction-factor')
router.register('dashboard-summary', DashboardViewSet, basename='dashboard-summary')
router.register('reports', ReportsViewSet, basename='report')


@require_GET
def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        return JsonResponse({
            'status': 'ok',
            'service': 'EDU ASSIST Backend',
            'database': 'connected',
        }, status=200)
    except Exception:
        return JsonResponse({
            'status': 'error',
            'service': 'EDU ASSIST Backend',
            'database': 'unavailable',
        }, status=503)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health-check'),
    path('api/auth/', include('accounts.urls')),
    path('api/predictions/predict/<int:student_id>/', predict_student_view, name='predict-student'),
    path('api/', include(router.urls)),
]
