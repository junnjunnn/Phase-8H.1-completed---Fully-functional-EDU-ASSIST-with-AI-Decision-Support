import csv
from io import StringIO

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from academics.models import AcademicRecord, AcademicYear, Enrollment, GradeLevel, Section, Subject
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

    def test_report_export_returns_professional_csv(self):
        self.client.force_login(self.user)
        response = self.client.get('/api/reports/export/', {'category': 'student', 'export_format': 'csv'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertRegex(response['Content-Disposition'], r'attachment; filename="student_report_\d{4}-\d{2}-\d{2}\.csv"')
        rows = list(csv.reader(StringIO(response.content.decode('utf-8'))))
        self.assertEqual(rows[0], ['Report Type', 'Academic Year', 'Reporting Period', 'Generated At', 'Metric', 'Value'])
        self.assertIn(['Student Reports', 'All active academic years', 'All dates to Present', rows[1][3], 'Student Count', '1'], rows)

    def test_report_export_respects_selected_filters_and_escapes_metadata(self):
        self.academic_year.name = '2024, "Current"'
        self.academic_year.save(update_fields=['name'])
        self.client.force_login(self.user)
        response = self.client.get('/api/reports/export/', {
            'category': 'student',
            'export_format': 'csv',
            'academic_year': self.academic_year.pk,
            'search': 'Ana',
        })

        self.assertEqual(response.status_code, 200)
        rows = list(csv.reader(StringIO(response.content.decode('utf-8'))))
        self.assertEqual(rows[1][1], '2024, "Current"')
        self.assertEqual(rows[1][2], 'All dates to Present')
        self.assertEqual(rows[-1][-1], '1')
        self.assertIn(b'"2024, ""Current"""', response.content)

    def test_empty_report_export_still_has_header(self):
        self.client.force_login(self.user)
        response = self.client.get('/api/reports/export/', {'category': 'student', 'export_format': 'csv', 'search': 'Nobody'})

        self.assertEqual(response.status_code, 200)
        rows = list(csv.reader(StringIO(response.content.decode('utf-8'))))
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[1][-1], '0')

    def test_report_export_does_not_expose_data_to_unknown_role(self):
        unauthorized = get_user_model().objects.create_user(username='unknown-reporter', password='secret123')
        UserProfile.objects.create(user=unauthorized, role_name='UNKNOWN')
        self.client.force_login(unauthorized)
        response = self.client.get('/api/reports/export/', {'category': 'student', 'export_format': 'csv'})

        self.assertEqual(response.status_code, 200)
        rows = list(csv.reader(StringIO(response.content.decode('utf-8'))))
        self.assertEqual(rows[1][-1], '0')

    def test_report_center_excludes_archived_school_year_data(self):
        archived_year = AcademicYear.objects.create(name='2023-2024', start_date='2023-01-01', end_date='2024-12-31', is_active=False)
        archived_grade = GradeLevel.objects.get(code='G10')
        archived_section = Section.objects.create(grade_level=archived_grade, academic_year=archived_year, name='Archived-A', capacity=30, adviser=self.user)
        archived_student = Student.objects.create(first_name='Archived', last_name='Student', lrn='987654321098')
        archived_enrollment = Enrollment.objects.create(
            student=archived_student,
            academic_year=archived_year,
            grade_level=archived_grade,
            section=archived_section,
            enrollment_status='active',
        )
        RiskPrediction.objects.create(
            enrollment=archived_enrollment,
            prediction_type='Academic Risk',
            risk_level='High',
            probability=0.95,
            explanation='Historical archived year prediction',
        )

        self.client.force_login(self.user)
        response = self.client.get('/api/reports/center/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['summary']['student_count'], 1)
        self.assertEqual(response.json()['student_reports']['enrollment_count'], 1)
        self.assertEqual(response.json()['ai_reports']['summary']['prediction_count'], 1)

    def test_report_center_excludes_archived_student_child_records_and_restores_them(self):
        subject = Subject.objects.create(
            code='REPORT-MATH',
            name='Report Mathematics',
            category='Learning Area',
            grade_level=self.grade_level,
        )
        archived_student = Student.objects.create(first_name='Archived', last_name='Learner', lrn='111111111111')
        archived_enrollment = Enrollment.objects.create(
            student=archived_student,
            academic_year=self.academic_year,
            grade_level=self.grade_level,
            section=self.section,
            enrollment_status='active',
        )
        AcademicRecord.objects.create(
            enrollment=archived_enrollment,
            subject=subject,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            grade=60,
            final_grade=60,
        )
        AttendanceRecord.objects.create(
            enrollment=archived_enrollment,
            month='November',
            school_days=20,
            days_present=1,
            absences=19,
            times_tardy=3,
        )
        BehavioralAssessment.objects.create(
            enrollment=archived_enrollment,
            academic_year=self.academic_year,
            core_value=self.core_value,
            behavior_indicator=self.indicator,
            rating=self.rating,
            numeric_score=1.0,
            assessment_date='2024-11-01',
        )
        RiskPrediction.objects.create(
            enrollment=archived_enrollment,
            prediction_type='Academic Risk',
            risk_level='High',
            probability=0.99,
        )
        Intervention.objects.create(
            enrollment=archived_enrollment,
            intervention_type='Tutoring',
            status='planned',
            assigned_personnel=self.user,
        )
        archived_student.student_status = 'archived'
        archived_student.save(update_fields=['student_status'])

        self.client.force_login(self.user)
        response = self.client.get('/api/reports/center/', {'include_archived': 'true'})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['student_reports']['student_count'], 1)
        self.assertEqual(data['student_reports']['enrollment_count'], 1)
        self.assertEqual(data['academic_reports']['summary']['total_records'], 0)
        self.assertEqual(data['attendance_reports']['summary']['present_count'], 18)
        self.assertEqual(data['behavior_reports']['summary']['assessment_count'], 1)
        self.assertEqual(data['ai_reports']['summary']['prediction_count'], 1)
        self.assertEqual(data['intervention_reports']['summary']['total'], 1)

        archived_student.student_status = 'active'
        archived_student.save(update_fields=['student_status'])
        response = self.client.get('/api/reports/center/', {'include_archived': 'true'})
        data = response.json()
        self.assertEqual(data['student_reports']['student_count'], 2)
        self.assertEqual(data['academic_reports']['summary']['total_records'], 1)
        self.assertEqual(data['attendance_reports']['summary']['present_count'], 19)
        self.assertEqual(data['behavior_reports']['summary']['assessment_count'], 2)
        self.assertEqual(data['ai_reports']['summary']['prediction_count'], 2)
        self.assertEqual(data['intervention_reports']['summary']['total'], 2)

    def test_report_center_excludes_archived_child_academic_context(self):
        archived_year = AcademicYear.objects.create(
            name='2023-2024-context',
            start_date='2023-01-01',
            end_date='2023-12-31',
            is_active=False,
        )
        subject = Subject.objects.create(
            code='REPORT-CONTEXT',
            name='Context Mathematics',
            category='Learning Area',
            grade_level=self.grade_level,
        )
        AcademicRecord.objects.create(
            enrollment=self.enrollment,
            subject=subject,
            academic_year=archived_year,
            grading_period_type='Quarter',
            quarter=1,
            grade=50,
            final_grade=50,
        )
        BehavioralAssessment.objects.create(
            enrollment=self.enrollment,
            academic_year=archived_year,
            core_value=self.core_value,
            behavior_indicator=self.indicator,
            rating=self.rating,
            numeric_score=1.0,
            assessment_date='2023-11-01',
        )

        self.client.force_login(self.user)
        response = self.client.get('/api/reports/center/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['academic_reports']['summary']['total_records'], 0)
        self.assertEqual(data['behavior_reports']['summary']['assessment_count'], 1)
        self.assertTrue(AcademicRecord.objects.filter(academic_year=archived_year).exists())
        self.assertTrue(BehavioralAssessment.objects.filter(academic_year=archived_year).exists())

    def test_report_center_excludes_inactive_relationship_chain(self):
        inactive_grade = GradeLevel.objects.create(
            name='Inactive Report Grade',
            code='REPORT-INACTIVE-GRD',
            school_level='Elementary',
            is_active=False,
        )
        inactive_section = Section.objects.create(
            grade_level=self.grade_level,
            academic_year=self.academic_year,
            name='Inactive Report Section',
            is_active=False,
        )
        inactive_grade_section = Section.objects.create(
            grade_level=inactive_grade,
            academic_year=self.academic_year,
            name='Inactive Grade Section',
        )
        cases = [
            ('Inactive Section', inactive_section, self.grade_level, 'active'),
            ('Inactive Grade', inactive_grade_section, inactive_grade, 'active'),
            ('Inactive Enrollment', self.section, self.grade_level, 'withdrawn'),
        ]
        for index, (name, section, grade_level, enrollment_status) in enumerate(cases, start=1):
            student = Student.objects.create(first_name=name, last_name='Case', lrn=f'2222222222{index:02d}')
            Enrollment.objects.create(
                student=student,
                academic_year=self.academic_year,
                grade_level=grade_level,
                section=section,
                enrollment_status=enrollment_status,
            )

        self.client.force_login(self.user)
        response = self.client.get('/api/reports/center/', {'include_archived': 'true'})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['student_reports']['student_count'], 1)
        self.assertEqual(data['student_reports']['enrollment_count'], 1)
