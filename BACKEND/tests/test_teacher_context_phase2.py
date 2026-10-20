from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from academics.models import AcademicYear, GradeLevel, Section, Subject, TeacherAssignment, Enrollment
from accounts.models import UserProfile
from common.authorization import authorized_students_queryset
from students.models import Student


class TeacherContextPhase2Tests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.teacher = user_model.objects.create_user(username='phase2_teacher', password='secret123')
        UserProfile.objects.create(user=self.teacher, role_name='TEACHER')
        self.other_teacher = user_model.objects.create_user(username='phase2_other', password='secret123')
        UserProfile.objects.create(user=self.other_teacher, role_name='TEACHER')

        self.year = AcademicYear.objects.create(name='2026-2027', start_date='2026-06-01', end_date='2027-03-31', is_active=True)
        self.grade = GradeLevel.objects.get(code='G10')
        self.advisory = Section.objects.create(name='Rizal', grade_level=self.grade, academic_year=self.year, adviser=self.teacher)
        self.subject_section = Section.objects.create(name='Bonifacio', grade_level=self.grade, academic_year=self.year)
        self.unrelated = Section.objects.create(name='Mabini', grade_level=self.grade, academic_year=self.year)
        self.math = Subject.objects.create(code='P2MATH', name='Mathematics', category='Learning Area', grade_level=self.grade)
        self.science = Subject.objects.create(code='P2SCI', name='Science', category='Learning Area', grade_level=self.grade)
        TeacherAssignment.objects.create(teacher=self.teacher, academic_year=self.year, grade_level=self.grade, section=self.subject_section, subject=self.math)
        TeacherAssignment.objects.create(teacher=self.other_teacher, academic_year=self.year, grade_level=self.grade, section=self.unrelated, subject=self.science)

        student = Student.objects.create(first_name='Assigned', last_name='Learner', student_status='active')
        Enrollment.objects.create(student=student, academic_year=self.year, grade_level=self.grade, section=self.advisory, enrollment_status='active')

    def authenticate(self):
        self.client.force_authenticate(user=self.teacher)

    def test_my_context_separates_adviser_and_subject_assignments(self):
        self.authenticate()
        response = self.client.get('/api/teacher-assignments/my-context/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['section_name'] for item in response.data['advisory_classes']], ['Rizal'])
        self.assertEqual([item['subject_name'] for item in response.data['subject_assignments']], ['Mathematics'])
        self.assertEqual(response.data['subject_assignments'][0]['role'], 'Subject Teacher')

    def test_teacher_assignment_list_is_self_scoped(self):
        self.authenticate()
        response = self.client.get('/api/teacher-assignments/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['section_name'] for item in response.data['results']], ['Bonifacio'])

    def test_authorized_students_queryset_unions_adviser_and_subject_sections(self):
        enrolled_subject_student = Student.objects.create(first_name='Subject', last_name='Roster', student_status='active')
        Enrollment.objects.create(student=enrolled_subject_student, academic_year=self.year, grade_level=self.grade, section=self.subject_section, enrollment_status='active')

        authorized_ids = set(authorized_students_queryset(self.teacher, Student.objects.all()).values_list('id', flat=True))

        self.assertIn(enrolled_subject_student.id, authorized_ids)

    def test_teacher_enrollment_scope_includes_advisory_but_not_unrelated(self):
        self.authenticate()
        response = self.client.get('/api/enrollments/', {'section': self.advisory.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        unrelated = self.client.get('/api/enrollments/', {'section': self.unrelated.id})
        self.assertEqual(unrelated.status_code, 200)
        self.assertEqual(unrelated.data['count'], 0)

    def test_other_teacher_does_not_receive_adviser_role(self):
        self.client.force_authenticate(user=self.other_teacher)
        response = self.client.get('/api/teacher-assignments/my-context/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['advisory_classes'], [])
        self.assertEqual(response.data['subject_assignments'][0]['section_name'], 'Mabini')

    def test_teacher_with_both_roles_keeps_one_context_entry_per_role(self):
        TeacherAssignment.objects.create(
            teacher=self.teacher,
            academic_year=self.year,
            grade_level=self.grade,
            section=self.advisory,
            assignment_type='ADVISER',
        )
        TeacherAssignment.objects.create(
            teacher=self.teacher,
            academic_year=self.year,
            grade_level=self.grade,
            section=self.advisory,
            subject=self.math,
        )
        self.authenticate()
        response = self.client.get('/api/teacher-assignments/my-context/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['advisory_classes']), 1)
        self.assertEqual(len(response.data['subject_assignments']), 2)
        dual_role = next(item for item in response.data['subject_assignments'] if item['section_name'] == 'Rizal')
        self.assertEqual(dual_role['role'], 'Adviser and Subject Teacher')

    def test_adviser_assignment_without_subject_is_excluded_from_subject_assignments(self):
        TeacherAssignment.objects.create(
            teacher=self.teacher,
            academic_year=self.year,
            grade_level=self.grade,
            section=self.advisory,
            assignment_type='ADVISER',
        )
        self.authenticate()
        response = self.client.get('/api/teacher-assignments/my-context/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['assignment_type'] for item in response.data['subject_assignments']], ['SUBJECT'])
        self.assertTrue(all(item.get('subject') for item in response.data['subject_assignments']))
        self.assertEqual([item['section_name'] for item in response.data['advisory_classes']], ['Rizal'])

    def test_teacher_report_rejects_unassigned_subject_scope(self):
        self.authenticate()
        response = self.client.get('/api/reports/center/', {'subject': self.science.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['student_reports']['student_count'], 0)
