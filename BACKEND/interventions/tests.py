from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from academics.models import AcademicYear, GradeLevel, Section, Enrollment
from interventions.models import Intervention
from students.models import Student


class InterventionAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()

        self.superadmin = self.user_model.objects.create_user(username='superadmin_interventions', password='SuperPass1!')
        UserProfile.objects.create(user=self.superadmin, role_name='SUPER_ADMIN')

        self.teacher = self.user_model.objects.create_user(username='teacher_interventions', password='TeacherPass1!')
        teacher_profile = UserProfile.objects.create(user=self.teacher, role_name='TEACHER')

        self.academic_year = AcademicYear.objects.create(name='2025-2026', start_date='2025-06-01', end_date='2026-03-31', is_active=True)
        self.grade_level = GradeLevel.objects.create(name='Grade 11', code='G11', school_level='Senior High School', order=11)
        section_a = Section.objects.create(name='A', grade_level=self.grade_level, academic_year=self.academic_year)
        self.section_b = Section.objects.create(name='B', grade_level=self.grade_level, academic_year=self.academic_year)
        teacher_profile.assigned_sections.add(section_a)

        self.student_a = Student.objects.create(first_name='Alice', last_name='Anderson', gender='Female', student_status='active')
        self.student_b = Student.objects.create(first_name='Bob', last_name='Baker', gender='Male', student_status='active')

        self.enrollment_a = Enrollment.objects.create(student=self.student_a, academic_year=self.academic_year, grade_level=self.grade_level, section=section_a, enrollment_status='active')
        self.enrollment_b = Enrollment.objects.create(student=self.student_b, academic_year=self.academic_year, grade_level=self.grade_level, section=self.section_b, enrollment_status='active')

        self.intervention_a = Intervention.objects.create(
            enrollment=self.enrollment_a,
            intervention_type='Tutoring',
            recommendation='Extra practice',
            status='planned',
            priority='medium',
        )
        self.intervention_b = Intervention.objects.create(
            enrollment=self.enrollment_b,
            intervention_type='Tutoring',
            recommendation='Extra support',
            status='planned',
            priority='medium',
        )

    def test_teacher_only_sees_assigned_section_interventions(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get('/api/interventions/')
        self.assertEqual(response.status_code, 200)
        intervention_ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.intervention_a.id, intervention_ids)
        self.assertNotIn(self.intervention_b.id, intervention_ids)

    def test_superadmin_sees_all_interventions(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get('/api/interventions/')
        self.assertEqual(response.status_code, 200)
        intervention_ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.intervention_a.id, intervention_ids)
        self.assertIn(self.intervention_b.id, intervention_ids)
