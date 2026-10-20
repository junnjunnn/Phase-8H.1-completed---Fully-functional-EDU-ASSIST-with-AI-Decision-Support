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
        # Use the grade level from Phase 1 migration (0004)
        grade_level = GradeLevel.objects.get(code='G11')
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

    def test_grade_and_section_filters_ignore_historical_inactive_enrollments(self):
        self.client.force_authenticate(user=self.superadmin)

        previous_year = AcademicYear.objects.create(name='2024-2025', start_date='2024-06-01', end_date='2025-03-31', is_active=False)
        historical_grade = GradeLevel.objects.get(code='G10')
        historical_section = Section.objects.create(name='History', grade_level=historical_grade, academic_year=previous_year)
        student = Student.objects.create(first_name='History', last_name='Student', gender='Female', student_status='active')
        Enrollment.objects.create(
            student=student,
            academic_year=previous_year,
            grade_level=historical_grade,
            section=historical_section,
            enrollment_status='inactive',
        )

        current_grade = GradeLevel.objects.get(code='G11')
        current_section = self.section_b
        Enrollment.objects.create(
            student=student,
            academic_year=AcademicYear.objects.get(name='2025-2026'),
            grade_level=current_grade,
            section=current_section,
            enrollment_status='active',
        )

        response = self.client.get(f'/api/students/?grade_level={historical_grade.id}')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(student.id, {item['id'] for item in response.data['results']})

        response = self.client.get(f'/api/students/?grade_level={current_grade.id}&section={current_section.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(student.id, {item['id'] for item in response.data['results']})

    def test_section_filter_endpoint_excludes_archived_sections_for_active_student_workflow(self):
        self.client.force_authenticate(user=self.superadmin)

        current_year = AcademicYear.objects.get(name='2025-2026')
        selected_grade = GradeLevel.objects.get(code='G11')
        other_grade = GradeLevel.objects.create(name='Grade 12 Archive Check', code='G12-ARCHIVE-CHECK', school_level='Senior High School', order=13, is_active=True)
        active_section = Section.objects.create(name='Active Section', grade_level=selected_grade, academic_year=current_year, is_active=True)
        archived_section = Section.objects.create(name='Archived Section', grade_level=selected_grade, academic_year=current_year, is_active=False)
        other_grade_section = Section.objects.create(name='Other Grade Section', grade_level=other_grade, academic_year=current_year, is_active=True)

        response = self.client.get('/api/sections/', {'active_only': 'true', 'academic_year': current_year.id, 'grade_level': selected_grade.id})
        self.assertEqual(response.status_code, 200)
        ids = {item['id'] for item in response.data['results']}
        self.assertIn(active_section.id, ids)
        self.assertNotIn(archived_section.id, ids)
        self.assertNotIn(other_grade_section.id, ids)

    def test_registration_creates_student_profile_without_enrollment(self):
        self.client.force_authenticate(user=self.superadmin)
        payload = {
            'lrn': '2025001',
            'first_name': 'Maria',
            'middle_name': 'Delos',
            'last_name': 'Cruz',
            'suffix': 'Jr.',
            'gender': 'Female',
            'birth_date': '2014-05-12',
            'address': '123 Sample Street, Davao City',
            'guardian_name': 'Anna Cruz',
            'parent_contact': '09171234567',
            'email': 'maria.cruz@example.com',
            'student_status': 'active',
        }

        response = self.client.post('/api/students/', payload, format='json')

        self.assertEqual(response.status_code, 201)
        student = Student.objects.get(lrn='2025001')
        self.assertEqual(student.first_name, 'Maria')
        self.assertEqual(student.guardian_name, 'Anna Cruz')
        self.assertEqual(student.parent_contact, '09171234567')
        self.assertFalse(student.enrollments.exists())

    def test_archived_student_is_hidden_from_active_student_workflows(self):
        self.client.force_authenticate(user=self.superadmin)
        archived_student = Student.objects.create(first_name='Arch', last_name='Student', gender='Female', student_status='archived')
        Enrollment.objects.create(
            student=archived_student,
            academic_year=AcademicYear.objects.get(name='2025-2026'),
            grade_level=GradeLevel.objects.get(code='G11'),
            section=self.section_b,
            enrollment_status='active',
        )

        response = self.client.get('/api/students/')
        self.assertEqual(response.status_code, 200)
        student_ids = {item['id'] for item in response.data['results']}
        self.assertNotIn(archived_student.id, student_ids)

    def test_archived_student_can_be_retrieved_explicitly_when_requested(self):
        self.client.force_authenticate(user=self.superadmin)
        archived_student = Student.objects.create(first_name='Hist', last_name='Student', gender='Female', student_status='archived')
        Enrollment.objects.create(
            student=archived_student,
            academic_year=AcademicYear.objects.get(name='2025-2026'),
            grade_level=GradeLevel.objects.get(code='G11'),
            section=self.section_b,
            enrollment_status='active',
        )

        response = self.client.get('/api/students/?include_archived=true')
        self.assertEqual(response.status_code, 200)
        student_ids = {item['id'] for item in response.data['results']}
        self.assertIn(archived_student.id, student_ids)

    def test_active_student_detail_does_not_require_current_enrollment(self):
        self.client.force_authenticate(user=self.superadmin)
        student = Student.objects.create(first_name='Unenrolled', last_name='Student', gender='Female', student_status='active')

        response = self.client.get(f'/api/students/{student.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], student.id)

    def test_active_student_without_enrollment_appears_in_student_list_api(self):
        self.client.force_authenticate(user=self.superadmin)
        student = Student.objects.create(first_name='Fresh', last_name='Student', gender='Female', student_status='active')

        response = self.client.get('/api/students/')

        self.assertEqual(response.status_code, 200)
        student_ids = {item['id'] for item in response.data['results']}
        self.assertIn(student.id, student_ids)

    def test_archived_student_detail_preserves_lifecycle_rules(self):
        self.client.force_authenticate(user=self.superadmin)
        archived_student = Student.objects.create(first_name='Archived', last_name='Detail', gender='Female', student_status='archived')

        default_response = self.client.get(f'/api/students/{archived_student.id}/')
        archived_response = self.client.get(f'/api/students/{archived_student.id}/', {'status': 'archived'})

        self.assertEqual(default_response.status_code, 404)
        self.assertEqual(archived_response.status_code, 200)
        self.assertEqual(archived_response.data['id'], archived_student.id)
