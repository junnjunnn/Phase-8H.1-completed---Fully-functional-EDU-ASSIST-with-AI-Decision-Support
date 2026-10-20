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

    def assignment_payload(self, **overrides):
        payload = {
            'teacher': self.active_teacher.id,
            'academic_year': self.active_year.id,
            'grade_level': self.active_grade.id,
            'section': self.active_section.id,
            'subject': self.subject.id,
            'assignment_type': 'SUBJECT',
            'is_active': True,
        }
        payload.update(overrides)
        return payload

    def authenticate_admin(self):
        self.client.force_authenticate(user=self.admin)

    def test_active_assignment_references_are_accepted(self):
        self.authenticate_admin()
        response = self.client.post('/api/teacher-assignments/', self.assignment_payload(), format='json')
        self.assertEqual(response.status_code, 201)

    def test_inactive_teacher_is_rejected_for_new_assignment(self):
        self.authenticate_admin()
        response = self.client.post('/api/teacher-assignments/', self.assignment_payload(teacher=self.inactive_teacher.id), format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('teacher', response.data)

    def test_archived_grade_is_rejected_for_new_assignment(self):
        self.authenticate_admin()
        response = self.client.post('/api/teacher-assignments/', self.assignment_payload(grade_level=self.archived_grade.id, section=self.archived_grade_section.id), format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('grade_level', response.data)

    def test_archived_subject_is_rejected_for_new_assignment(self):
        archived_subject = Subject.objects.create(code='FILTER-ARCHIVED', name='Archived Filter Subject', category='Learning Area', grade_level=self.active_grade, is_active=False)
        self.authenticate_admin()
        response = self.client.post('/api/teacher-assignments/', self.assignment_payload(subject=archived_subject.id), format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('subject', response.data)

    def test_grade_scoped_active_subject_endpoint_excludes_archived_and_other_grades(self):
        archived_subject = Subject.objects.create(code='FILTER-ENDPOINT-ARCHIVED', name='Archived Endpoint Subject', category='Learning Area', grade_level=self.active_grade, is_active=False)
        other_grade = GradeLevel.objects.create(name='Endpoint Other Grade', code='EOG', school_level='Elementary', order=94, is_active=True)
        other_subject = Subject.objects.create(code='FILTER-ENDPOINT-OTHER', name='Other Endpoint Subject', category='Learning Area', grade_level=other_grade, is_active=True)
        self.authenticate_admin()
        response = self.client.get('/api/subjects/', {'active_only': 'true', 'grade_level': self.active_grade.id})
        ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.subject.id, ids)
        self.assertNotIn(archived_subject.id, ids)
        self.assertNotIn(other_subject.id, ids)

    def test_subject_for_another_grade_is_rejected(self):
        other_grade = GradeLevel.objects.create(name='Other Filter Grade', code='OFG', school_level='Elementary', order=92, is_active=True)
        other_subject = Subject.objects.create(code='FILTER-OTHER', name='Other Grade Subject', category='Learning Area', grade_level=other_grade, is_active=True)
        self.authenticate_admin()
        response = self.client.post('/api/teacher-assignments/', self.assignment_payload(subject=other_subject.id), format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('subject', response.data)

    def test_archived_section_is_rejected_for_new_assignment(self):
        self.authenticate_admin()
        response = self.client.post('/api/teacher-assignments/', self.assignment_payload(section=self.archived_section.id), format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('section', response.data)

    def test_section_for_another_grade_is_rejected(self):
        other_grade = GradeLevel.objects.create(name='Section Other Grade', code='SOG', school_level='Elementary', order=93, is_active=True)
        other_section = Section.objects.create(name='Other Grade Section', grade_level=other_grade, academic_year=self.active_year, is_active=True)
        self.authenticate_admin()
        response = self.client.post('/api/teacher-assignments/', self.assignment_payload(section=other_section.id), format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('section', response.data)

    def test_section_for_another_year_is_rejected(self):
        other_year = AcademicYear.objects.create(name='filter-other-year', start_date='2032-06-01', end_date='2033-03-31', is_active=False)
        other_section = Section.objects.create(name='Other Year Section', grade_level=self.active_grade, academic_year=other_year, is_active=True)
        self.authenticate_admin()
        response = self.client.post('/api/teacher-assignments/', self.assignment_payload(section=other_section.id), format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('section', response.data)

    def test_historical_archived_subject_can_be_preserved_on_edit(self):
        archived_subject = Subject.objects.create(code='FILTER-HISTORICAL', name='Historical Archived Subject', category='Learning Area', grade_level=self.archived_grade, is_active=False)
        historical_section = Section.objects.create(name='Historical Archived Section', grade_level=self.archived_grade, academic_year=self.archived_year, is_active=False)
        historical = TeacherAssignment.objects.create(
            teacher=self.inactive_teacher,
            academic_year=self.archived_year,
            grade_level=self.archived_grade,
            section=historical_section,
            subject=archived_subject,
            is_active=True,
        )
        self.authenticate_admin()
        response = self.client.patch(f'/api/teacher-assignments/{historical.id}/', {'subject': archived_subject.id}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['subject'], archived_subject.id)

    def test_academic_reference_endpoints_default_to_active_only(self):
        self.authenticate_admin()

        active_year_response = self.client.get('/api/academic-years/')
        active_year_ids = {item['id'] for item in active_year_response.data['results']}
        self.assertIn(self.active_year.id, active_year_ids)
        self.assertNotIn(self.archived_year.id, active_year_ids)

        active_grade_response = self.client.get('/api/grade-levels/')
        active_grade_ids = {item['id'] for item in active_grade_response.data['results']}
        self.assertIn(self.active_grade.id, active_grade_ids)
        self.assertNotIn(self.archived_grade.id, active_grade_ids)

        active_section_response = self.client.get('/api/sections/')
        active_section_ids = {item['id'] for item in active_section_response.data['results']}
        self.assertIn(self.active_section.id, active_section_ids)
        self.assertNotIn(self.archived_section.id, active_section_ids)
        self.assertNotIn(self.archived_year_section.id, active_section_ids)
        self.assertNotIn(self.archived_grade_section.id, active_section_ids)

    def test_historical_reference_records_are_available_when_explicitly_requested(self):
        self.authenticate_admin()

        archived_year_response = self.client.get('/api/academic-years/?include_archived=true')
        archived_year_ids = {item['id'] for item in archived_year_response.data['results']}
        self.assertIn(self.archived_year.id, archived_year_ids)

        archived_grade_response = self.client.get('/api/grade-levels/?include_archived=true')
        archived_grade_ids = {item['id'] for item in archived_grade_response.data['results']}
        self.assertIn(self.archived_grade.id, archived_grade_ids)

        archived_section_response = self.client.get('/api/sections/?include_archived=true')
        archived_section_ids = {item['id'] for item in archived_section_response.data['results']}
        self.assertIn(self.archived_section.id, archived_section_ids)
        self.assertIn(self.archived_year_section.id, archived_section_ids)
        self.assertIn(self.archived_grade_section.id, archived_section_ids)
