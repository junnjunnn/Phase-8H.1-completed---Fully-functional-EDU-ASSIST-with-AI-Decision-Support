"""
Test to verify that enrollment-scoped endpoints properly validate user authorization on CREATE/UPDATE.

This tests for a critical vulnerability where teachers could create records for students
they don't have access to (e.g., attendance records, behavioral assessments, interventions).
"""
import os
import sys
import django

# Set up Django
os.chdir('f:\\edu_new\\BACKEND')
sys.path.insert(0, 'f:\\edu_new\\BACKEND')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from academics.models import AcademicYear, GradeLevel, Section, Strand, Subject
from students.models import Student
from academics.models import Enrollment
from accounts.models import UserProfile
from attendance.models import AttendanceRecord
from behavior.models import BehavioralAssessment, CoreValue, BehaviorIndicator, BehavioralRating
from interventions.models import Intervention


User = get_user_model()


class EnrollmentScopedAuthorizationTest(TestCase):
    """Test that enrollment-scoped endpoints enforce authorization on writes."""

    def setUp(self):
        """Set up test data with two sections and teachers."""
        # Create academic year
        self.year = AcademicYear.objects.create(name='2024-2025', start_date='2024-06-01', end_date='2025-05-31')
        
        # Create grade levels
        self.grade7 = GradeLevel.objects.create(name='Grade 7', level_number=7)
        
        # Create strands
        self.strand_abm = Strand.objects.create(name='ABM', description='Accountancy Business Management')
        self.strand_stem = Strand.objects.create(name='STEM', description='Science Technology Engineering Math')
        
        # Create sections
        self.section_a = Section.objects.create(name='7-A', grade_level=self.grade7, academic_year=self.year)
        self.section_b = Section.objects.create(name='7-B', grade_level=self.grade7, academic_year=self.year)
        
        # Create subject
        self.subject = Subject.objects.create(name='Mathematics', grade_level=self.grade7, strand=self.strand_stem)
        
        # Create students
        self.student_a = Student.objects.create(lrn='20240001', first_name='Alice', last_name='A')
        self.student_b = Student.objects.create(lrn='20240002', first_name='Bob', last_name='B')
        
        # Create enrollments
        self.enrollment_a = Enrollment.objects.create(
            student=self.student_a,
            academic_year=self.year,
            grade_level=self.grade7,
            section=self.section_a,
            strand=self.strand_abm,
            enrollment_status='active'
        )
        self.enrollment_b = Enrollment.objects.create(
            student=self.student_b,
            academic_year=self.year,
            grade_level=self.grade7,
            section=self.section_b,
            strand=self.strand_stem,
            enrollment_status='active'
        )
        
        # Create users: teacher_a assigned to section_a, teacher_b assigned to section_b
        self.teacher_a_user = User.objects.create_user(username='teacher_a', password='pass123')
        self.teacher_a_profile = UserProfile.objects.create(user=self.teacher_a_user, role_name='TEACHER')
        self.teacher_a_profile.assigned_sections.add(self.section_a)
        
        self.teacher_b_user = User.objects.create_user(username='teacher_b', password='pass123')
        self.teacher_b_profile = UserProfile.objects.create(user=self.teacher_b_user, role_name='TEACHER')
        self.teacher_b_profile.assigned_sections.add(self.section_b)
        
        # Create admin
        self.admin_user = User.objects.create_user(username='admin', password='pass123')
        self.admin_profile = UserProfile.objects.create(user=self.admin_user, role_name='SCHOOL_ADMIN')
        
        # Create behavior reference data
        self.core_value = CoreValue.objects.create(name='Honesty', description='Being truthful')
        self.behavior_indicator = BehaviorIndicator.objects.create(
            name='Honest Communication',
            description='Communicates truthfully',
            core_value=self.core_value
        )
        self.behavior_rating = BehavioralRating.objects.create(
            code='EXCELLENT',
            label='Excellent',
            numeric_value=5
        )
        
        self.client = Client()

    def test_teacher_a_cannot_create_attendance_for_unauthorized_student_b(self):
        """Teacher A should not be able to create attendance record for Student B (unauthorized)."""
        self.client.force_authenticate(user=self.teacher_a_user)
        
        # Teacher A tries to create attendance for Student B (section_b)
        response = self.client.post('/api/attendance-records/', {
            'enrollment': self.enrollment_b.id,
            'month': '2024-06',
            'school_days': 20,
            'days_present': 18,
            'absences': 2,
            'times_tardy': 0,
        })
        
        print(f"Test: Teacher A creating attendance for unauthorized Student B")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.data}")
        
        # VULNERABILITY: This currently returns 201 (Created) but should return 403 (Forbidden)
        # Expected: 403
        # Actual: likely 201
        self.assertNotEqual(response.status_code, 201, 
            "VULNERABILITY: Teacher A should not be able to create attendance for Student B")

    def test_teacher_a_can_create_attendance_for_authorized_student_a(self):
        """Teacher A should be able to create attendance record for Student A (authorized)."""
        self.client.force_authenticate(user=self.teacher_a_user)
        
        # Teacher A creates attendance for Student A (section_a)
        response = self.client.post('/api/attendance-records/', {
            'enrollment': self.enrollment_a.id,
            'month': '2024-06',
            'school_days': 20,
            'days_present': 20,
            'absences': 0,
            'times_tardy': 0,
        })
        
        print(f"Test: Teacher A creating attendance for authorized Student A")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.data}")
        
        # This should succeed
        self.assertEqual(response.status_code, 201, "Teacher A should be able to create attendance for Student A")

    def test_teacher_a_cannot_create_behavior_assessment_for_unauthorized_student_b(self):
        """Teacher A should not be able to create behavioral assessment for Student B (unauthorized)."""
        self.client.force_authenticate(user=self.teacher_a_user)
        
        # Teacher A tries to create behavioral assessment for Student B
        response = self.client.post('/api/behavioral-assessments/', {
            'enrollment': self.enrollment_b.id,
            'academic_year': self.year.id,
            'grading_period_type': 'quarter',
            'quarter': 1,
            'core_value': self.core_value.id,
            'behavior_indicator': self.behavior_indicator.id,
            'rating': self.behavior_rating.id,
        })
        
        print(f"Test: Teacher A creating behavioral assessment for unauthorized Student B")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.data}")
        
        # VULNERABILITY: This currently returns 201 but should return 403
        self.assertNotEqual(response.status_code, 201,
            "VULNERABILITY: Teacher A should not be able to create behavioral assessment for Student B")

    def test_teacher_a_cannot_create_intervention_for_unauthorized_student_b(self):
        """Teacher A should not be able to create intervention for Student B (unauthorized)."""
        self.client.force_authenticate(user=self.teacher_a_user)
        
        # Teacher A tries to create intervention for Student B
        response = self.client.post('/api/interventions/', {
            'enrollment': self.enrollment_b.id,
            'risk_type': 'academic',
            'intervention_type': 'tutoring',
            'status': 'planned',
            'priority': 'high',
        })
        
        print(f"Test: Teacher A creating intervention for unauthorized Student B")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.data}")
        
        # VULNERABILITY: This currently returns 201 but should return 403
        self.assertNotEqual(response.status_code, 201,
            "VULNERABILITY: Teacher A should not be able to create intervention for Student B")


if __name__ == '__main__':
    import unittest
    unittest.main()
