from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from academics.models import AcademicYear, Enrollment, GradeLevel, Section
from accounts.models import UserProfile
from attendance.models import AttendanceRecord
from behavior.models import BehavioralAssessment, BehavioralRating, BehaviorIndicator, CoreValue
from interventions.models import Intervention
from predictions.models import RiskPrediction
from students.models import Student


class ReportCenterViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(username='reporter', password='secret123')
        self.profile = UserProfile.objects.create(user=self.user, role_name='SCHOOL_ADMIN')

        self.academic_year = AcademicYear.objects.create(name='2024-2025', start_date='2024-01-01', end_date='2025-12-31', is_active=True)
        # Use the grade level from Phase 1 migration (0004)
        self.grade_level = GradeLevel.objects.get(code='G10')
        self.section = Section.objects.create(grade_level=self.grade_level, academic_year=self.academic_year, name='A', capacity=30, adviser=self.user)

        self.student = Student.objects.create(first_name='Ana', last_name='Cruz', lrn='123456789012')
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            academic_year=self.academic_year,
            grade_level=self.grade_level,
            section=self.section,
            enrollment_status='active',
        )

        self.core_value = CoreValue.objects.create(name='Respect')
        self.indicator = BehaviorIndicator.objects.create(name='Shows respect', core_value=self.core_value)
        self.rating = BehavioralRating.objects.create(code='4', label='Exemplary', numeric_value=4.0)
        BehavioralAssessment.objects.create(
            enrollment=self.enrollment,
            academic_year=self.academic_year,
            core_value=self.core_value,
            behavior_indicator=self.indicator,
            rating=self.rating,
            numeric_score=4.0,
            assessment_date='2024-10-01',
        )
        AttendanceRecord.objects.create(
            enrollment=self.enrollment,
            month='October',
            school_days=20,
            days_present=18,
            absences=2,
            times_tardy=1,
        )
        RiskPrediction.objects.create(
            enrollment=self.enrollment,
            prediction_type='Academic Risk',
            risk_level='High',
            probability=0.82,
            explanation='Needs support',
        )
        Intervention.objects.create(
            enrollment=self.enrollment,
            intervention_type='Tutoring',
            status='in_progress',
            assigned_personnel=self.user,
        )

    def test_report_center_returns_student_summary(self):
        self.client.force_login(self.user)
        response = self.client.get('/api/reports/center/', {'category': 'student'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['summary']['student_count'], 1)
        self.assertEqual(response.json()['student_reports']['enrollment_count'], 1)
