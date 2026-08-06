from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from academics.models import AcademicYear, GradeLevel, Section, Enrollment
from students.models import Student


class StudentAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()

        self.superadmin = self.user_model.objects.create_user(username='superadmin', password='SuperPass1!')
        UserProfile.objects.create(user=self.superadmin, role_name='SUPER_ADMIN')

        self.teacher = self.user_model.objects.create_user(username='teacher_user', password='TeacherPass1!')
        teacher_profile = UserProfile.objects.create(user=self.teacher, role_name='TEACHER')

        academic_year = AcademicYear.objects.create(name='2025-2026', start_date='2025-06-01', end_date='2026-03-31', is_active=True)
        grade_level = GradeLevel.objects.create(name='Grade 11', code='G11', school_level='Senior High School', order=11)
        section_a = Section.objects.create(name='A', grade_level=grade_level, academic_year=academic_year)
        self.section_b = Section.objects.create(name='B', grade_level=grade_level, academic_year=academic_year)
        teacher_profile.assigned_sections.add(section_a)

        self.student_a = Student.objects.create(first_name='Alice', last_name='Anderson', gender='Female', student_status='active')
        self.student_b = Student.objects.create(first_name='Bob', last_name='Baker', gender='Male', student_status='active')

        Enrollment.objects.create(student=self.student_a, academic_year=academic_year, grade_level=grade_level, section=section_a, enrollment_status='active')
        Enrollment.objects.create(student=self.student_b, academic_year=academic_year, grade_level=grade_level, section=self.section_b, enrollment_status='active')

    def test_teacher_only_sees_assigned_section_students(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get('/api/students/')
        self.assertEqual(response.status_code, 200)
        student_ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.student_a.id, student_ids)
        self.assertNotIn(self.student_b.id, student_ids)

    def test_superadmin_sees_all_students(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get('/api/students/')
        self.assertEqual(response.status_code, 200)
        student_ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.student_a.id, student_ids)
        self.assertIn(self.student_b.id, student_ids)

    def test_teacher_cannot_access_unauthorized_student_detail(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(f'/api/students/{self.student_b.id}/')
        self.assertEqual(response.status_code, 404)

    def test_student_search_is_scoped_by_teacher(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get('/api/students/?search=Bob')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

    def test_student_filtering_is_scoped_by_teacher(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(f'/api/students/?section={self.section_b.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
