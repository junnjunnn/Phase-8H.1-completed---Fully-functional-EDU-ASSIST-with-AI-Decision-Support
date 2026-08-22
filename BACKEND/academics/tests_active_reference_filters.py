from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from academics.models import AcademicYear, GradeLevel, Section, Subject, TeacherAssignment


class ActiveReferenceFilterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(username='active_filter_admin', password='AdminPass1!')
        UserProfile.objects.create(user=self.admin, role_name='SCHOOL_ADMIN')
        self.active_teacher = user_model.objects.create_user(username='active_filter_teacher', password='TeacherPass1!', is_active=True)
        UserProfile.objects.create(user=self.active_teacher, role_name='TEACHER')
        self.inactive_teacher = user_model.objects.create_user(username='inactive_filter_teacher', password='TeacherPass1!', is_active=False)
        UserProfile.objects.create(user=self.inactive_teacher, role_name='TEACHER')
        self.guidance = user_model.objects.create_user(username='active_filter_guidance', password='GuidancePass1!')
        UserProfile.objects.create(user=self.guidance, role_name='GUIDANCE')

        self.active_year = AcademicYear.objects.create(name='filter-active-year', start_date='2030-06-01', end_date='2031-03-31', is_active=True)
        self.archived_year = AcademicYear.objects.create(name='filter-archived-year', start_date='2029-06-01', end_date='2030-03-31', is_active=False)
        self.active_grade = GradeLevel.objects.create(name='Filter Active Grade', code='FAG', school_level='Elementary', order=90, is_active=True)
        self.archived_grade = GradeLevel.objects.create(name='Filter Archived Grade', code='FRG', school_level='Elementary', order=91, is_active=False)
        self.active_section = Section.objects.create(name='Active Section', grade_level=self.active_grade, academic_year=self.active_year, is_active=True)
        self.archived_section = Section.objects.create(name='Archived Section', grade_level=self.active_grade, academic_year=self.active_year, is_active=False)
        self.archived_year_section = Section.objects.create(name='Archived Year Section', grade_level=self.active_grade, academic_year=self.archived_year, is_active=True)
        self.archived_grade_section = Section.objects.create(name='Archived Grade Section', grade_level=self.archived_grade, academic_year=self.active_year, is_active=True)
        self.subject = Subject.objects.create(code='FILTER-SUBJECT', name='Filter Subject', category='Learning Area', grade_level=self.active_grade, is_active=True)
        self.historical_assignment = TeacherAssignment.objects.create(teacher=self.inactive_teacher, academic_year=self.archived_year, grade_level=self.archived_grade, section=self.archived_grade_section, subject=self.subject, is_active=True)

    def test_active_grade_levels_endpoint_excludes_archived(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/grade-levels/?active_only=true')
        ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.active_grade.id, ids)
        self.assertNotIn(self.archived_grade.id, ids)

    def test_active_sections_endpoint_requires_active_section_grade_and_year(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/sections/?active_only=true')
        ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.active_section.id, ids)
        self.assertNotIn(self.archived_section.id, ids)
        self.assertNotIn(self.archived_year_section.id, ids)
        self.assertNotIn(self.archived_grade_section.id, ids)

    def test_user_endpoint_combines_active_and_role_filters(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/auth/users/?active_only=true&role_name=TEACHER')
        ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.active_teacher.id, ids)
        self.assertNotIn(self.inactive_teacher.id, ids)
        self.assertNotIn(self.guidance.id, ids)

    def test_user_endpoint_default_preserves_inactive_records(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/auth/users/')
        ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.inactive_teacher.id, ids)

    def test_historical_assignment_remains_readable(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/teacher-assignments/')
        ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.historical_assignment.id, ids)

    def test_teacher_cannot_access_user_management(self):
        self.client.force_authenticate(user=self.active_teacher)
        response = self.client.get('/api/auth/users/')
        self.assertIn(response.status_code, (401, 403))
