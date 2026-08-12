from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient

from accounts.models import UserProfile
from academics.models import AcademicYear, GradeLevel, Section, Enrollment
from students.models import Student


class InterventionCreateTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()

        self.teacher = self.user_model.objects.create_user(username='teacher_int', password='Teacher1!')
        teacher_profile = UserProfile.objects.create(user=self.teacher, role_name='TEACHER')

        self.academic_year = AcademicYear.objects.create(name='2025-2026', start_date='2025-06-01', end_date='2026-03-31', is_active=True)
        self.grade = GradeLevel.objects.create(name='Grade 1', code='G1', school_level='Primary', order=1)
        self.section_a = Section.objects.create(name='A', grade_level=self.grade, academic_year=self.academic_year)
        self.section_b = Section.objects.create(name='B', grade_level=self.grade, academic_year=self.academic_year)
        teacher_profile.assigned_sections.add(self.section_a)

        self.student_a = Student.objects.create(first_name='Sam', last_name='A', gender='Male', student_status='active')
        self.student_b = Student.objects.create(first_name='Sam', last_name='B', gender='Male', student_status='active')

        self.enrollment_a = Enrollment.objects.create(student=self.student_a, academic_year=self.academic_year, grade_level=self.grade, section=self.section_a, enrollment_status='active')
        self.enrollment_b = Enrollment.objects.create(student=self.student_b, academic_year=self.academic_year, grade_level=self.grade, section=self.section_b, enrollment_status='inactive')

    def test_teacher_can_create_intervention_for_assigned_enrollment(self):
        self.client.force_authenticate(user=self.teacher)
        payload = {'enrollment': self.enrollment_a.id, 'intervention_type': 'Tutoring', 'recommendation': 'Help', 'status': 'planned', 'priority': 'low'}
        resp = self.client.post('/api/interventions/', payload)
        self.assertEqual(resp.status_code, 201)

    def test_teacher_cannot_create_intervention_for_inactive_enrollment(self):
        self.client.force_authenticate(user=self.teacher)
        payload = {'enrollment': self.enrollment_b.id, 'intervention_type': 'Tutoring', 'recommendation': 'Help', 'status': 'planned', 'priority': 'low'}
        resp = self.client.post('/api/interventions/', payload)
        # expecting 400 or 403 depending on validation; ensure not created
        self.assertIn(resp.status_code, (400, 403))

    def test_unauthenticated_cannot_create_intervention(self):
        payload = {'enrollment': self.enrollment_a.id, 'intervention_type': 'Tutoring', 'recommendation': 'Help', 'status': 'planned', 'priority': 'low'}
        resp = self.client.post('/api/interventions/', payload)
        self.assertIn(resp.status_code, (401, 403))
