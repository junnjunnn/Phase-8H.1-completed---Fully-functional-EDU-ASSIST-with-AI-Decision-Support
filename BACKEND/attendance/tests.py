from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from academics.models import AcademicYear, GradeLevel, Section, Enrollment
from students.models import Student
from .models import AttendanceRecord


class AttendanceRecordAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()

        self.superadmin = self.user_model.objects.create_user(username='superadmin_attendance', password='SuperPass1!')
        UserProfile.objects.create(user=self.superadmin, role_name='SUPER_ADMIN')

        self.teacher = self.user_model.objects.create_user(username='teacher_attendance', password='TeacherPass1!')
        teacher_profile = UserProfile.objects.create(user=self.teacher, role_name='TEACHER')

        academic_year = AcademicYear.objects.create(name='2025-2026', start_date='2025-06-01', end_date='2026-03-31', is_active=True)
        # Use the grade level from Phase 1 migration (0004)
        grade_level = GradeLevel.objects.get(code='G11')
        section_a = Section.objects.create(name='A', grade_level=grade_level, academic_year=academic_year)
        self.section_b = Section.objects.create(name='B', grade_level=grade_level, academic_year=academic_year)
        teacher_profile.assigned_sections.add(section_a)

        self.student_a = Student.objects.create(first_name='Alice', last_name='Anderson', gender='Female', student_status='active')
        self.student_b = Student.objects.create(first_name='Bob', last_name='Baker', gender='Male', student_status='active')

        self.enrollment_a = Enrollment.objects.create(student=self.student_a, academic_year=academic_year, grade_level=grade_level, section=section_a, enrollment_status='active')
        self.enrollment_b = Enrollment.objects.create(student=self.student_b, academic_year=academic_year, grade_level=grade_level, section=self.section_b, enrollment_status='active')

        self.attendance_a = AttendanceRecord.objects.create(enrollment=self.enrollment_a, month='June', school_days=20, days_present=18, absences=2, times_tardy=1)
        self.attendance_b = AttendanceRecord.objects.create(enrollment=self.enrollment_b, month='June', school_days=20, days_present=19, absences=1, times_tardy=0)

    def test_teacher_only_sees_assigned_section_attendance_records(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get('/api/attendance-records/')
        self.assertEqual(response.status_code, 200)
        record_ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.attendance_a.id, record_ids)
        self.assertNotIn(self.attendance_b.id, record_ids)

    def test_superadmin_sees_all_attendance_records(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get('/api/attendance-records/')
        self.assertEqual(response.status_code, 200)
        record_ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.attendance_a.id, record_ids)
        self.assertIn(self.attendance_b.id, record_ids)

    def test_teacher_cannot_create_attendance_for_unauthorized_enrollment(self):
        """Critical: Teacher should NOT be able to create attendance for unauthorized enrollment."""
        self.client.force_authenticate(user=self.teacher)
        
        # Teacher attempts to create attendance for student_b (unauthorized, not in teacher's section)
        response = self.client.post('/api/attendance-records/', {
            'enrollment': self.enrollment_b.id,
            'month': 'July',
            'school_days': 20,
            'days_present': 18,
            'absences': 2,
            'times_tardy': 0,
        })
        
        # Expected: 400 Bad Request with authorization error (or 403 Forbidden)
        # Either is acceptable - the important thing is that access is denied
        self.assertIn(response.status_code, [400, 403], 
            f"Teacher should not create attendance for unauthorized enrollment. Got {response.status_code}: {response.data}")
