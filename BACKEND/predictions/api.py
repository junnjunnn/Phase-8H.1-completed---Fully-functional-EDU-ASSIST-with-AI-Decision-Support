from django.db.models import Avg, Case, Count, F, IntegerField, Q, Sum, When
from django.utils import timezone
from rest_framework import mixins, permissions, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from accounts.permissions import IsAuthorizedStaff, IsRegistrarOrSchoolAdmin
from common.audit import AuditMixin
from common.drf_filters import RoleScopedViewsetMixin
from common.authorization import active_enrollment_queryset, archived_enrollment_queryset, authorized_students_queryset, authorized_enrollment_queryset, get_adviser_sections, get_user_scope, requested_lifecycle_status, teacher_assignment_queryset
from academics.models import AcademicRecord, Enrollment, Section
from attendance.models import AttendanceRecord
from attendance.school_day_service import get_school_day_summary
from behavior.models import BehavioralAssessment
from interventions.models import Intervention
from students.models import Student
from .models import PredictionFactor, RiskPrediction
from .serializers import PredictionFactorSerializer, RiskPredictionSerializer


class RiskPredictionViewSet(RoleScopedViewsetMixin, AuditMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    scope_field = 'enrollment'
    queryset = RiskPrediction.objects.select_related('enrollment__student', 'enrollment__academic_year', 'enrollment__grade_level', 'enrollment__section', 'reviewed_by').all()
    serializer_class = RiskPredictionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorizedStaff]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['enrollment__student', 'prediction_type', 'risk_level', 'review_status', 'reviewed_by']
    search_fields = ['enrollment__student__first_name', 'enrollment__student__last_name', 'model_name', 'model_version']
    ordering_fields = ['prediction_date', 'probability']
    ordering = ['-prediction_date']

    def get_queryset(self):
        queryset = super().get_queryset()
        status = requested_lifecycle_status(self.request)
        if status == 'active':
            return queryset.filter(enrollment__in=active_enrollment_queryset(Enrollment.objects.all()))
        if status == 'archived':
            return queryset.filter(enrollment__in=archived_enrollment_queryset(Enrollment.objects.all()))
        return queryset


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

    def get_queryset(self):
        queryset = super().get_queryset()
        status = requested_lifecycle_status(self.request)
        enrollments = Enrollment.objects.all()
        if status == 'active':
            enrollments = active_enrollment_queryset(enrollments)
        elif status == 'archived':
            enrollments = archived_enrollment_queryset(enrollments)
        return queryset.filter(prediction__enrollment__in=enrollments)


class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, IsAuthorizedStaff]

    def list(self, request):
        school_day_summary = get_school_day_summary(
            academic_year_id=request.query_params.get('academic_year'),
            reporting_date=request.query_params.get('reporting_date'),
        )
        school_days = school_day_summary['school_days']
        student_qs = authorized_students_queryset(request.user, Student.objects.all())
        student_qs = student_qs.filter(
            student_status='active',
            enrollments__enrollment_status='active',
            enrollments__academic_year__is_active=True,
            enrollments__grade_level__is_active=True,
            enrollments__section__is_active=True,
            enrollments__section__academic_year__is_active=True,
        ).distinct()

        prediction_qs = authorized_enrollment_queryset(request.user, RiskPrediction.objects.select_related('enrollment__student', 'enrollment__grade_level').all(), enrollment_field='enrollment')
        prediction_qs = prediction_qs.filter(
            enrollment__student__student_status='active',
            enrollment__enrollment_status='active',
            enrollment__academic_year__is_active=True,
            enrollment__grade_level__is_active=True,
            enrollment__section__is_active=True,
            enrollment__section__academic_year__is_active=True,
        )

        intervention_qs = authorized_enrollment_queryset(request.user, Intervention.objects.select_related('enrollment__student', 'enrollment__grade_level').all(), enrollment_field='enrollment')
        intervention_qs = intervention_qs.filter(
            enrollment__student__student_status='active',
            enrollment__enrollment_status='active',
            enrollment__academic_year__is_active=True,
            enrollment__grade_level__is_active=True,
            enrollment__section__is_active=True,
            enrollment__section__academic_year__is_active=True,
        )

        behavior_qs = authorized_enrollment_queryset(request.user, BehavioralAssessment.objects.select_related('enrollment__student', 'rating').all(), enrollment_field='enrollment')
        behavior_qs = behavior_qs.filter(
            enrollment__student__student_status='active',
            enrollment__enrollment_status='active',
            enrollment__academic_year__is_active=True,
            academic_year__is_active=True,
            academic_year_id=F('enrollment__academic_year_id'),
            enrollment__grade_level__is_active=True,
            enrollment__section__is_active=True,
            enrollment__section__academic_year__is_active=True,
        )

        attendance_qs = authorized_enrollment_queryset(request.user, AttendanceRecord.objects.all(), enrollment_field='enrollment').filter(
            enrollment__student__student_status='active',
            enrollment__enrollment_status='active',
            enrollment__academic_year__is_active=True,
            enrollment__grade_level__is_active=True,
            enrollment__section__is_active=True,
            enrollment__section__academic_year__is_active=True,
        )

        total_students = student_qs.count()
        attendance_totals = attendance_qs.aggregate(
            present=Sum('days_present'),
            absent=Sum('absences'),
            late=Sum('times_tardy'),
        )
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
            enrollment__in=prediction_qs.values('enrollment'),
            academic_year__is_active=True,
            academic_year_id=F('enrollment__academic_year_id'),
            enrollment__student__student_status='active',
            enrollment__enrollment_status='active',
            enrollment__grade_level__is_active=True,
            enrollment__section__is_active=True,
            enrollment__section__academic_year__is_active=True,
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
            'attendance_summary': {
                'record_count': attendance_qs.count(),
                'present': int(attendance_totals['present'] or 0),
                'absent': int(attendance_totals['absent'] or 0),
                'late': int(attendance_totals['late'] or 0),
                'school_days': school_days,
                'attendance_percentage': round((int(attendance_totals['present'] or 0) / school_days) * 100, 2) if school_days else 0,
            },
            'school_days': school_days,
            'academic_year': school_day_summary['academic_year'].name if school_day_summary['academic_year'] else None,
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


class RegistrarDashboardViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, IsRegistrarOrSchoolAdmin]

    def list(self, request):
        school_day_summary = get_school_day_summary(
            reporting_date=request.query_params.get('reporting_date'),
        )
        academic_year = school_day_summary['academic_year']
        enrollments = active_enrollment_queryset(
            Enrollment.objects.select_related('student', 'grade_level', 'section', 'academic_year')
        )
        if academic_year:
            enrollments = enrollments.filter(academic_year=academic_year)
        else:
            enrollments = enrollments.none()

        distribution = list(
            enrollments.values('grade_level_id', 'grade_level__name')
            .annotate(count=Count('id'))
            .order_by('grade_level__order', 'grade_level__name')
        )
        recent_enrollments = list(
            enrollments.order_by('-enrollment_date', '-created_at')[:10].values(
                'id',
                'enrollment_date',
                'created_at',
                'student__first_name',
                'student__last_name',
                'grade_level__name',
                'section__name',
            )
        )

        return Response({
            'total_active_students': enrollments.values('student_id').distinct().count(),
            'total_active_enrollments': enrollments.count(),
            'total_active_sections': Section.objects.filter(
                academic_year=academic_year,
                is_active=True,
                grade_level__is_active=True,
            ).count() if academic_year else 0,
            'current_academic_year': academic_year.name if academic_year else None,
            'school_days': school_day_summary['school_days'],
            'enrollment_distribution': distribution,
            'recent_enrollments': recent_enrollments,
        })


class AdviserDashboardViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, IsAuthorizedStaff]

    def list(self, request):
        school_day_summary = get_school_day_summary(
            academic_year_id=request.query_params.get('academic_year'),
            reporting_date=request.query_params.get('reporting_date'),
        )
        school_days = school_day_summary['school_days']
        sections = get_adviser_sections(request.user)
        selected_section = request.query_params.get('section')
        search = request.query_params.get('search', '').strip()
        if selected_section:
            sections = sections.filter(pk=selected_section)
            if not sections.exists():
                return Response({'detail': 'The selected section is not assigned to this adviser.'}, status=404)
        if not sections.exists():
            if get_user_scope(request.user) != 'teacher' or teacher_assignment_queryset(request.user).filter(assignment_type='SUBJECT').exists():
                return Response({'detail': 'This dashboard is available only to advisers.'}, status=403)
            return Response({
                'sections': [],
                'summary': {
                    'total_students': 0,
                    'active_students': 0,
                    'academic_concerns': 0,
                    'active_interventions': 0,
                    'follow_up_required': 0,
                    'students_requiring_attention': 0,
                    'school_days': school_days,
                },
                'school_days': school_days,
                'academic_year': school_day_summary['academic_year'].name if school_day_summary['academic_year'] else None,
                'risk_distribution': {},
                'students_requiring_attention': [],
                'students': [],
                'disclaimer': 'AI-generated risk information is a decision-support indicator and should be interpreted using professional judgment.',
            })

        enrollments = (
            active_enrollment_queryset(Enrollment.objects.filter(section__in=sections))
            .filter(
                Q(student__first_name__icontains=search)
                | Q(student__middle_name__icontains=search)
                | Q(student__last_name__icontains=search)
                | Q(student__lrn__icontains=search)
            ) if search else active_enrollment_queryset(Enrollment.objects.filter(section__in=sections))
        ).select_related('student', 'grade_level', 'section', 'section__academic_year', 'section__strand')
        enrollments = enrollments.order_by('student__last_name', 'student__first_name')
        today = timezone.localdate()
        risk_distribution = {}
        academic_concerns = 0
        intervention_student_ids = set()
        follow_up_student_ids = set()
        attendance_record_count = 0
        behavior_record_count = 0
        class_averages = []
        total_school_days = 0
        total_days_present = 0
        attention_students = []
        roster_students = []

        for enrollment in enrollments:
            academic_records = list(enrollment.academic_records.filter(
                final_grade__isnull=False,
                academic_year__is_active=True,
                academic_year_id=enrollment.academic_year_id,
            ).values_list('final_grade', flat=True))
            average = round(float(sum(academic_records) / len(academic_records)), 2) if academic_records else None
            academic_concern = average is not None and average < 75
            if average is not None:
                class_averages.append(average)

            attendance_records = enrollment.attendance_records.all()
            attendance = attendance_records.aggregate(
                present=Sum('days_present'),
                absences=Sum('absences'),
                tardy=Sum('times_tardy'),
                school_days=Sum('school_days'),
            )
            applicable_school_days = school_days or attendance['school_days']
            attendance_percentage = round((int(attendance['present'] or 0) / applicable_school_days) * 100, 2) if applicable_school_days else None
            attendance_record_count += attendance_records.count()
            total_school_days += applicable_school_days or 0
            total_days_present += int(attendance['present'] or 0)

            behavior_records = enrollment.behavioral_assessments.filter(
                academic_year__is_active=True,
                academic_year_id=enrollment.academic_year_id,
            )
            behavior = behavior_records.aggregate(
                average_score=Avg('numeric_score'),
            )
            behavior_average = round(float(behavior['average_score']), 2) if behavior['average_score'] is not None else None
            behavior_record_count += behavior_records.count()

            prediction = enrollment.risk_predictions.order_by('-prediction_date').values(
                'id', 'risk_level', 'probability', 'prediction_date', 'explanation',
            ).first()
            prediction_factors = []
            if prediction:
                prediction_factors = list(PredictionFactor.objects.filter(prediction_id=prediction['id']).values(
                    'feature_name', 'feature_value', 'direction', 'explanation_text',
                ))
            if prediction:
                risk_distribution[prediction['risk_level']] = risk_distribution.get(prediction['risk_level'], 0) + 1

            interventions = list(enrollment.interventions.filter(status__in=['planned', 'in_progress', 'paused']).values('status', 'end_date'))
            has_follow_up = any(item['end_date'] and item['end_date'] <= today for item in interventions)

            concerns = []
            if academic_concern:
                concerns.append('Academic average below 75')
                academic_concerns += 1
            if prediction and prediction['risk_level'] in {'High', 'Moderate'}:
                concerns.append(f"{prediction['risk_level']} risk prediction")
            if interventions:
                concerns.append('Active intervention')
                intervention_student_ids.add(enrollment.student_id)
            if has_follow_up:
                concerns.append('Follow-up due')
                follow_up_student_ids.add(enrollment.student_id)

            student_data = {
                    'id': enrollment.student_id,
                    'name': f'{enrollment.student.first_name} {enrollment.student.last_name}'.strip(),
                    'lrn': enrollment.student.lrn,
                    'grade': enrollment.grade_level.name,
                    'section': enrollment.section.name if enrollment.section else 'Unassigned',
                    'academic_year': enrollment.section.academic_year.name if enrollment.section else None,
                    'school_level': enrollment.grade_level.school_level,
                    'strand': enrollment.section.strand.name if enrollment.section and enrollment.section.strand else None,
                    'enrollment_status': enrollment.enrollment_status,
                    'general_average': average,
                    'attendance_percentage': attendance_percentage,
                    'school_days': school_days or None,
                    'days_present': int(attendance['present'] or 0) if school_days else None,
                    'times_tardy': int(attendance['tardy'] or 0) if school_days else None,
                    'behavior_average': behavior_average,
                    'behavior_records': behavior_records.count(),
                    'risk_level': prediction['risk_level'] if prediction else None,
                    'risk_probability': float(prediction['probability']) if prediction else None,
                    'risk_explanation': prediction['explanation'] if prediction else None,
                    'risk_factors': prediction_factors,
                    'intervention': bool(interventions),
                    'intervention_statuses': [item['status'] for item in interventions],
                    'follow_up': has_follow_up,
                    'concerns': concerns,
            }
            roster_students.append(student_data)
            if concerns:
                attention_students.append(student_data)

        attention_students.sort(key=lambda item: (-len(item['concerns']), item['name']))
        return Response({
            'sections': list(sections.values('id', 'name', 'grade_level__name', 'grade_level__school_level', 'academic_year__name', 'strand__name')),
            'summary': {
                'total_students': enrollments.count(),
                'active_students': enrollments.count(),
                'academic_concerns': academic_concerns,
                'class_general_average': round(sum(class_averages) / len(class_averages), 2) if class_averages else None,
                'attendance_rate': round((total_days_present / total_school_days) * 100, 2) if total_school_days else None,
                'school_days': school_days,
                'attendance_concerns': None,
                'behavioral_concerns': None,
                'active_interventions': len(intervention_student_ids),
                'follow_up_required': len(follow_up_student_ids),
                'students_requiring_attention': len(attention_students),
                'students_with_attendance_records': len({enrollment.student_id for enrollment in enrollments if enrollment.attendance_records.exists()}),
                'students_with_behavior_records': len({enrollment.student_id for enrollment in enrollments if enrollment.behavioral_assessments.filter(academic_year__is_active=True, academic_year_id=enrollment.academic_year_id).exists()}),
            },
            'attendance_summary': {
                'students_with_records': len({enrollment.student_id for enrollment in enrollments if enrollment.attendance_records.exists()}),
                'record_count': attendance_record_count,
                'school_days': school_days,
            },
            'school_days': school_days,
            'academic_year': school_day_summary['academic_year'].name if school_day_summary['academic_year'] else None,
            'behavior_summary': {
                'students_with_records': len({enrollment.student_id for enrollment in enrollments if enrollment.behavioral_assessments.exists()}),
                'record_count': behavior_record_count,
            },
            'risk_distribution': risk_distribution,
            'students': roster_students,
            'students_requiring_attention': attention_students,
            'disclaimer': 'AI-generated risk information is a decision-support indicator and should be interpreted using professional judgment.',
        })
