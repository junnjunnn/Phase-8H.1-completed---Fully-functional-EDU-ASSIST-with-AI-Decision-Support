from django.test import TestCase
from django.contrib.auth import get_user_model

from academics.models import AcademicYear, GradeLevel, Section
from students.models import Student, Enrollment
from common.authorization import get_user_scope, authorized_students_queryset, authorized_enrollment_queryset

User = get_user_model()


class AuthorizationTests(TestCase):
    def setUp(self):
        # Academic fixtures
        self.year = AcademicYear.objects.create(name='2025-2026', start_date='2025-06-01', end_date='2026-03-31', is_active=True)
        self.grade = GradeLevel.objects.create(name='Grade 7', code='G7', school_level='Junior High School', order=7)
        self.section_a = Section.objects.create(grade_level=self.grade, academic_year=self.year, name='A')
        self.section_b = Section.objects.create(grade_level=self.grade, academic_year=self.year, name='B')

        # Students
        self.student1 = Student.objects.create(lrn='S001', first_name='Alice', last_name='One')
        self.student2 = Student.objects.create(lrn='S002', first_name='Bob', last_name='Two')

        Enrollment.objects.create(student=self.student1, academic_year=self.year, grade_level=self.grade, section=self.section_a)
        Enrollment.objects.create(student=self.student2, academic_year=self.year, grade_level=self.grade, section=self.section_b)

        # Users
        self.admin = User.objects.create_user(username='admin', password='pass')
        self.admin_profile = self.admin.profile
        self.admin_profile.role_name = 'SCHOOL_ADMIN'
        self.admin_profile.save()

        self.teacher = User.objects.create_user(username='teacher', password='pass')
        self.teacher_profile = self.teacher.profile
        self.teacher_profile.role_name = 'TEACHER'
        self.teacher_profile.save()
        self.teacher_profile.assigned_sections.add(self.section_a)

        self.guidance = User.objects.create_user(username='guidance', password='pass')
        self.guidance_profile = self.guidance.profile
        self.guidance_profile.role_name = 'GUIDANCE'
        self.guidance_profile.save()

    def test_get_user_scope(self):
        self.assertEqual(get_user_scope(self.admin), 'schoolwide')
        self.assertEqual(get_user_scope(self.teacher), 'teacher')
        self.assertEqual(get_user_scope(self.guidance), 'guidance')

    def test_authorized_students_for_teacher(self):
        qs = authorized_students_queryset(self.teacher, Student.objects.all())
        self.assertIn(self.student1, list(qs))
        self.assertNotIn(self.student2, list(qs))

    def test_authorized_students_for_admin(self):
        qs = authorized_students_queryset(self.admin, Student.objects.all())
        self.assertIn(self.student1, list(qs))
        self.assertIn(self.student2, list(qs))

    def test_authorized_enrollment_queryset_teacher(self):
        # Use Enrollment queryset via enrollment_field
        from academics.models import Enrollment
        qs = authorized_enrollment_queryset(self.teacher, Enrollment.objects.all(), enrollment_field='enrollment')
        # teacher assigned to section_a should see student1's enrollment
        self.assertEqual(qs.filter(student=self.student1).count(), 1)
        self.assertEqual(qs.filter(student=self.student2).count(), 0)
