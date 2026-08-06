from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Max, Min, Sum
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from academics.models import AcademicRecord, AcademicYear, Enrollment, GradeLevel, Section, Subject
from accounts.utils import get_authorized_enrollment_queryset, get_user_scope
from attendance.models import AttendanceRecord
from behavior.models import BehavioralAssessment
from interventions.models import Intervention
from predictions.models import RiskPrediction
from students.models import Student
from audit.models import AuditLog


class ReportsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def _get_queryset_for_scope(self, queryset):
        return get_authorized_enrollment_queryset(self.request.user, queryset)

    def _get_filters(self):
        params = self.request.query_params
        filters = {}
        year_id = params.get('academic_year')
        grade_id = params.get('grade_level')
        section_id = params.get('section')
        teacher_id = params.get('teacher')
        risk_level = params.get('risk_level')
        status = params.get('status')
        date_from = params.get('date_from')
        date_to = params.get('date_to')
        search = params.get('search')

        if year_id:
            filters['academic_year_id'] = year_id
        if grade_id:
            filters['grade_level_id'] = grade_id
        if section_id:
            filters['section_id'] = section_id
        if teacher_id:
            filters['section__adviser_id'] = teacher_id
        if risk_level:
            filters['risk_predictions__risk_level'] = risk_level
        if status:
            filters['interventions__status'] = status
        if date_from:
            filters['created_at__gte'] = date_from
        if date_to:
            filters['created_at__lte'] = date_to
        if search:
            filters['student__first_name__icontains'] = search

        return filters

    def _base_enrollment_queryset(self):
        qs = Enrollment.objects.select_related('student', 'academic_year', 'grade_level', 'section').prefetch_related('academic_records', 'attendance_records', 'behavioral_assessments', 'risk_predictions', 'interventions')
        return self._get_queryset_for_scope(qs)

    def _student_reports(self, enrollments):
        student_count = enrollments.values('student').distinct().count()
        enrollment_count = enrollments.count()
        academic_years = AcademicYear.objects.filter(enrollments__in=enrollments).distinct().count()
        grade_levels = GradeLevel.objects.filter(enrollments__in=enrollments).distinct().count()
        sections = Section.objects.filter(enrollments__in=enrollments).distinct().count()
        return {
            'student_count': student_count,
            'enrollment_count': enrollment_count,
            'academic_year_count': academic_years,
            'grade_level_count': grade_levels,
            'section_count': sections,
        }

    def _academic_reports(self, enrollments):
        academic_records = AcademicRecord.objects.filter(enrollment__in=enrollments)
        summary = academic_records.aggregate(
            average_grade=Avg('grade'),
            highest_grade=Max('grade'),
            lowest_grade=Min('grade'),
            total_records=Count('id'),
        )
        passing = academic_records.filter(grade__gte=75).count()
        failing = academic_records.filter(grade__lt=75).count()
        return {
            'summary': {
                'average_grade': round(float(summary['average_grade'] or 0), 2),
                'highest_grade': float(summary['highest_grade'] or 0),
                'lowest_grade': float(summary['lowest_grade'] or 0),
                'passing_rate': round((passing / summary['total_records'] * 100) if summary['total_records'] else 0, 2),
                'failing_rate': round((failing / summary['total_records'] * 100) if summary['total_records'] else 0, 2),
            },
            'subject_breakdown': list(
                academic_records.values('subject__name').annotate(record_count=Count('id'), average_grade=Avg('grade')).order_by('-record_count')[:8]
            ),
        }

    def _attendance_reports(self, enrollments):
        attendance_records = AttendanceRecord.objects.filter(enrollment__in=enrollments)
        summary = attendance_records.aggregate(
            total_present=Sum('days_present'),
            total_absent=Sum('absences'),
            total_late=Sum('times_tardy'),
            total_school_days=Sum('school_days'),
        )
        attendance_percentage = 0
        if summary['total_school_days']:
            attendance_percentage = round((summary['total_present'] / summary['total_school_days']) * 100, 2)
        return {
            'summary': {
                'present_count': int(summary['total_present'] or 0),
                'absent_count': int(summary['total_absent'] or 0),
                'late_count': int(summary['total_late'] or 0),
                'attendance_percentage': attendance_percentage,
            },
            'ranking': list(attendance_records.values('enrollment__student__first_name', 'enrollment__student__last_name').annotate(present=Sum('days_present'), school_days=Sum('school_days')).order_by('-present')[:10]),
        }

    def _behavior_reports(self, enrollments):
        assessments = BehavioralAssessment.objects.filter(enrollment__in=enrollments)
        summary = assessments.aggregate(average_score=Avg('numeric_score'), total_assessments=Count('id'))
        return {
            'summary': {
                'behavior_average': round(float(summary['average_score'] or 0), 2),
                'assessment_count': int(summary['total_assessments'] or 0),
            },
            'classification': list(assessments.values('rating__label').annotate(count=Count('id')).order_by('-count')[:5]),
            'students_needing_intervention': list(
                assessments.filter(numeric_score__lt=3).values('enrollment__student__first_name', 'enrollment__student__last_name').distinct()[:10]
            ),
        }

    def _ai_reports(self, enrollments):
        predictions = RiskPrediction.objects.filter(enrollment__in=enrollments)
        distribution = predictions.values('risk_level').annotate(count=Count('id')).order_by('risk_level')
        return {
            'summary': {
                'prediction_count': predictions.count(),
                'high_risk_count': predictions.filter(risk_level='High').count(),
                'moderate_risk_count': predictions.filter(risk_level='Moderate').count(),
                'low_risk_count': predictions.filter(risk_level='Low').count(),
            },
            'distribution': list(distribution),
            'history': list(predictions.order_by('-prediction_date')[:8].values('risk_level', 'prediction_date', 'enrollment__student__first_name', 'enrollment__student__last_name')),
            'factors': list(
                predictions.values('enrollment__student__first_name', 'enrollment__student__last_name', 'prediction_type').annotate(count=Count('id')).order_by('-count')[:8]
            ),
        }

    def _intervention_reports(self, enrollments):
        interventions = Intervention.objects.filter(enrollment__in=enrollments)
        return {
            'summary': {
                'total': interventions.count(),
                'completed': interventions.filter(status='completed').count(),
                'in_progress': interventions.filter(status='in_progress').count(),
                'planned': interventions.filter(status='planned').count(),
                'cancelled': interventions.filter(status='cancelled').count(),
                'overdue': interventions.filter(end_date__lt=timezone.now().date()).count(),
            },
            'teacher_activity': list(
                interventions.values('assigned_personnel__username').annotate(count=Count('id')).order_by('-count')[:8]
            ),
        }

    @action(detail=False, methods=['get'])
    def center(self, request):
        qs = self._base_enrollment_queryset()
        filters = self._get_filters()
        if filters:
            qs = qs.filter(**filters)

        student_reports = self._student_reports(qs)
        academic_reports = self._academic_reports(qs)
        attendance_reports = self._attendance_reports(qs)
        behavior_reports = self._behavior_reports(qs)
        ai_reports = self._ai_reports(qs)
        intervention_reports = self._intervention_reports(qs)

        response = {
            'summary': {
                'student_count': student_reports['student_count'],
                'enrollment_count': student_reports['enrollment_count'],
                'academic_report_count': academic_reports['summary']['passing_rate'] + academic_reports['summary']['failing_rate'],
                'attendance_percentage': attendance_reports['summary']['attendance_percentage'],
                'behavior_average': behavior_reports['summary']['behavior_average'],
                'prediction_count': ai_reports['summary']['prediction_count'],
                'intervention_count': intervention_reports['summary']['total'],
            },
            'student_reports': student_reports,
            'academic_reports': academic_reports,
            'attendance_reports': attendance_reports,
            'behavior_reports': behavior_reports,
            'ai_reports': ai_reports,
            'intervention_reports': intervention_reports,
        }

        return Response(response)

    @action(detail=False, methods=['get'])
    def export(self, request):
        payload = self.center(request).data
        export_format = request.query_params.get('format', 'csv')
        if export_format == 'pdf':
            AuditLog.objects.create(
                user=self.request.user if self.request.user.is_authenticated else None,
                action='REPORT_PRINTED',
                module='reports',
                object_type='ReportCenter',
                object_id='report-center',
            )
            return Response({'format': 'pdf', 'data': payload, 'message': 'Use the print dialog to save this report as a PDF.'})
        if export_format == 'xlsx':
            AuditLog.objects.create(
                user=self.request.user if self.request.user.is_authenticated else None,
                action='REPORT_EXPORTED',
                module='reports',
                object_type='ReportCenter',
                object_id='report-center',
            )
            return Response({'format': 'xlsx', 'data': payload, 'message': 'Excel export is prepared as a workbook-ready payload.'})
        AuditLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action='REPORT_EXPORTED',
            module='reports',
            object_type='ReportCenter',
            object_id='report-center',
        )
        return Response({'format': export_format, 'data': payload})
