from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from academics.models import AcademicYear, GradeLevel, Section, Enrollment, Subject, AcademicRecord
from students.models import Student


class AcademicsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()

        self.superadmin = self.user_model.objects.create_user(username='superadmin_academics', password='SuperPass1!')
        UserProfile.objects.create(user=self.superadmin, role_name='SUPER_ADMIN')

        self.teacher = self.user_model.objects.create_user(username='teacher_academics', password='TeacherPass1!')
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

        self.subject = Subject.objects.create(code='MATH11', name='Mathematics 11', category='Learning Area', grade_level=self.grade_level)
        self.record_a = AcademicRecord.objects.create(enrollment=self.enrollment_a, subject=self.subject, academic_year=self.academic_year, grading_period_type='Quarter', quarter=1, grade=85.00)
        self.record_b = AcademicRecord.objects.create(enrollment=self.enrollment_b, subject=self.subject, academic_year=self.academic_year, grading_period_type='Quarter', quarter=1, grade=90.00)

    def test_teacher_only_sees_assigned_section_enrollments(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get('/api/enrollments/')
        self.assertEqual(response.status_code, 200)
        enrollment_ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.enrollment_a.id, enrollment_ids)
        self.assertNotIn(self.enrollment_b.id, enrollment_ids)

    def test_teacher_only_sees_assigned_section_academic_records(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get('/api/academic-records/')
        self.assertEqual(response.status_code, 200)
        record_ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.record_a.id, record_ids)
        self.assertNotIn(self.record_b.id, record_ids)

    def test_superadmin_sees_all_academic_records(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get('/api/academic-records/')
        self.assertEqual(response.status_code, 200)
        record_ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.record_a.id, record_ids)
        self.assertIn(self.record_b.id, record_ids)

    def test_duplicate_academic_record_is_rejected(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.post('/api/academic-records/', {
            'enrollment': self.enrollment_a.id,
            'subject': self.subject.id,
            'academic_year': self.academic_year.id,
            'grading_period_type': 'Quarter',
            'quarter': 1,
            'grade': 88.00,
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('already exists', str(response.data))
