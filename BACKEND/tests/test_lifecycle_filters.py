from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from academics.models import AcademicYear, Enrollment, GradeLevel, Section, TeacherAssignment
from attendance.models import AttendanceRecord
from students.models import Student


class LifecycleFilterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user = get_user_model().objects.create_user(username='lifecycle_admin', password='pass')
        UserProfile.objects.create(user=user, role_name='SCHOOL_ADMIN')
        self.client.force_authenticate(user=user)

        self.active_year = AcademicYear.objects.create(
            name='2030-2031', start_date='2030-06-01', end_date='2031-03-31', is_active=True,
        )
        self.archived_year = AcademicYear.objects.create(
            name='2029-2030', start_date='2029-06-01', end_date='2030-03-31', is_active=False,
        )
        self.active_grade = GradeLevel.objects.get(code='G7')
        self.archived_grade = GradeLevel.objects.create(
            name='Archived Grade', code='ARCHIVED-GRADE', school_level='Junior High School', order=99, is_active=False,
        )
        self.active_section = Section.objects.create(
            name='Current', grade_level=self.active_grade, academic_year=self.active_year, is_active=True,
        )
        self.archived_section = Section.objects.create(
            name='Historical', grade_level=self.archived_grade, academic_year=self.archived_year, is_active=False,
        )
        self.active_student = Student.objects.create(first_name='Current', last_name='Student', student_status='active')
        self.archived_student = Student.objects.create(first_name='Historical', last_name='Student', student_status='graduated')
        Enrollment.objects.create(
            student=self.active_student, academic_year=self.active_year, grade_level=self.active_grade,
            section=self.active_section, enrollment_status='active',
        )
        Enrollment.objects.create(
            student=self.archived_student, academic_year=self.archived_year, grade_level=self.archived_grade,
            section=self.archived_section, enrollment_status='graduated',
        )

    def ids(self, path, status):
        response = self.client.get(path, {'status': status})
        self.assertEqual(response.status_code, 200)
        data = response.data.get('results', response.data)
        return {item['id'] for item in data}

    def test_reference_status_contract(self):
        self.assertEqual(self.ids('/api/academic-years/', 'active'), {self.active_year.id})
        self.assertEqual(self.ids('/api/academic-years/', 'archived'), {self.archived_year.id})
        self.assertEqual(self.ids('/api/academic-years/', 'all'), {self.active_year.id, self.archived_year.id})
        self.assertEqual(self.ids('/api/grade-levels/', 'archived'), {self.archived_grade.id})
        self.assertEqual(self.ids('/api/sections/', 'archived'), {self.archived_section.id})

    def test_students_and_enrollments_preserve_historical_context(self):
        self.assertEqual(self.ids('/api/students/', 'active'), {self.active_student.id})
        self.assertEqual(self.ids('/api/students/', 'archived'), {self.archived_student.id})
        self.assertEqual(self.ids('/api/enrollments/', 'archived'), {self.archived_student.enrollments.get().id})

    def test_invalid_status_is_rejected(self):
        response = self.client.get('/api/academic-years/', {'status': 'retired'})
        self.assertEqual(response.status_code, 400)

    def test_historical_teacher_authorization_uses_real_assignment(self):
        teacher_a = get_user_model().objects.create_user(username='historical_teacher_a', password='pass')
        UserProfile.objects.create(user=teacher_a, role_name='TEACHER')
        teacher_b = get_user_model().objects.create_user(username='historical_teacher_b', password='pass')
        UserProfile.objects.create(user=teacher_b, role_name='TEACHER')
        TeacherAssignment.objects.create(
            teacher=teacher_a,
            academic_year=self.archived_year,
            grade_level=self.archived_grade,
            section=self.archived_section,
            assignment_type='ADVISER',
            is_active=False,
        )
        attendance = AttendanceRecord.objects.create(
            enrollment=self.archived_student.enrollments.get(),
            month='March',
            school_days=20,
            days_present=18,
            absences=2,
            times_tardy=0,
        )

        self.client.force_authenticate(user=teacher_a)
        response = self.client.get('/api/attendance-records/', {'status': 'archived'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(attendance.id, {item['id'] for item in response.data['results']})

        self.client.force_authenticate(user=teacher_b)
        response = self.client.get('/api/attendance-records/', {'status': 'archived'})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(attendance.id, {item['id'] for item in response.data['results']})
