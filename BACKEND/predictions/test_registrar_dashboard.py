from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from academics.models import AcademicYear, Enrollment, GradeLevel, Section
from attendance.models import SchoolCalendarDay
from students.models import Student


class RegistrarDashboardTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        User = get_user_model()
        self.registrar = User.objects.create_user(username='registrar_dashboard', password='pass')
        UserProfile.objects.create(user=self.registrar, role_name='REGISTRAR')
        self.teacher = User.objects.create_user(username='teacher_dashboard', password='pass')
        UserProfile.objects.create(user=self.teacher, role_name='TEACHER')

        self.year = AcademicYear.objects.create(
            name='2025-2026', start_date=date(2025, 6, 1), end_date=date(2026, 3, 31), is_active=True,
        )
        self.grade = GradeLevel.objects.get(code='G11')
        self.section = Section.objects.create(name='Registrar A', grade_level=self.grade, academic_year=self.year)
        self.student = Student.objects.create(first_name='Active', last_name='Student', student_status='active')
        Enrollment.objects.create(
            student=self.student, academic_year=self.year, grade_level=self.grade,
            section=self.section, enrollment_status='active', enrollment_date=date(2025, 6, 2),
        )
        SchoolCalendarDay.objects.create(
            academic_year=self.year, calendar_date=date(2025, 6, 2), day_type='SCHOOL_DAY',
            title='Opening day', attendance_expected=True,
        )

    def dashboard(self):
        self.client.force_authenticate(user=self.registrar)
        return self.client.get('/api/registrar-dashboard/')

    def test_registrar_dashboard_returns_operational_metrics(self):
        response = self.dashboard()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total_active_students'], 1)
        self.assertEqual(response.data['total_active_enrollments'], 1)
        self.assertEqual(response.data['total_active_sections'], 1)
        self.assertEqual(response.data['current_academic_year'], '2025-2026')
        self.assertEqual(response.data['school_days'], 1)
        self.assertEqual(response.data['enrollment_distribution'][0]['count'], 1)
        self.assertEqual(response.data['recent_enrollments'][0]['student__first_name'], 'Active')

    def test_archived_records_are_excluded_from_operational_metrics(self):
        archived_section = Section.objects.create(name='Archived', grade_level=self.grade, academic_year=self.year, is_active=False)
        archived_student = Student.objects.create(first_name='Archived', last_name='Student', student_status='archived')
        Enrollment.objects.create(
            student=archived_student, academic_year=self.year, grade_level=self.grade,
            section=archived_section, enrollment_status='active',
        )
        inactive_student = Student.objects.create(first_name='Inactive', last_name='Student', student_status='active')
        Enrollment.objects.create(
            student=inactive_student, academic_year=self.year, grade_level=self.grade,
            section=self.section, enrollment_status='inactive',
        )

        response = self.dashboard()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total_active_students'], 1)
        self.assertEqual(response.data['total_active_enrollments'], 1)
        self.assertEqual(response.data['total_active_sections'], 1)

    def test_teacher_cannot_access_registrar_dashboard(self):
        self.client.force_authenticate(user=self.teacher)

        self.assertEqual(self.client.get('/api/registrar-dashboard/').status_code, 403)

    def test_archived_academic_year_is_not_reported_as_current(self):
        archived_year = AcademicYear.objects.create(
            name='2024-2025', start_date=date(2024, 6, 1), end_date=date(2025, 3, 31), is_active=False,
        )
        archived_section = Section.objects.create(name='Historical', grade_level=self.grade, academic_year=archived_year)
        archived_student = Student.objects.create(first_name='Historical', last_name='Student', student_status='active')
        Enrollment.objects.create(
            student=archived_student, academic_year=archived_year, grade_level=self.grade,
            section=archived_section, enrollment_status='active',
        )

        response = self.dashboard()

        self.assertEqual(response.data['current_academic_year'], '2025-2026')
        self.assertEqual(response.data['total_active_enrollments'], 1)