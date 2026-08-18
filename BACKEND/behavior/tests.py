from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from academics.models import AcademicYear, GradeLevel, Section, Enrollment
from behavior.models import CoreValue, BehaviorIndicator, BehavioralRating, BehavioralAssessment
from students.models import Student


class BehavioralAssessmentAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()

        self.superadmin = self.user_model.objects.create_user(username='superadmin_behavior', password='SuperPass1!')
        UserProfile.objects.create(user=self.superadmin, role_name='SUPER_ADMIN')

        self.teacher = self.user_model.objects.create_user(username='teacher_behavior', password='TeacherPass1!')
        teacher_profile = UserProfile.objects.create(user=self.teacher, role_name='TEACHER')

        self.academic_year = AcademicYear.objects.create(name='2025-2026', start_date='2025-06-01', end_date='2026-03-31', is_active=True)
        # Use the grade level from Phase 1 migration (0004)
        self.grade_level = GradeLevel.objects.get(code='G11')
        section_a = Section.objects.create(name='A', grade_level=self.grade_level, academic_year=self.academic_year)
        self.section_b = Section.objects.create(name='B', grade_level=self.grade_level, academic_year=self.academic_year)
        teacher_profile.assigned_sections.add(section_a)

        self.student_a = Student.objects.create(first_name='Alice', last_name='Anderson', gender='Female', student_status='active')
        self.student_b = Student.objects.create(first_name='Bob', last_name='Baker', gender='Male', student_status='active')

        self.enrollment_a = Enrollment.objects.create(student=self.student_a, academic_year=self.academic_year, grade_level=self.grade_level, section=section_a, enrollment_status='active')
        self.enrollment_b = Enrollment.objects.create(student=self.student_b, academic_year=self.academic_year, grade_level=self.grade_level, section=self.section_b, enrollment_status='active')

        self.core_value = CoreValue.objects.create(name='Responsibility')
        self.behavior_indicator = BehaviorIndicator.objects.create(name='Attendance', core_value=self.core_value)
        self.rating = BehavioralRating.objects.create(code='EX', label='Excellent', numeric_value=5.0)

        self.assessment_a = BehavioralAssessment.objects.create(
            enrollment=self.enrollment_a,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            core_value=self.core_value,
            behavior_indicator=self.behavior_indicator,
            rating=self.rating,
            numeric_score=5.0,
        )
        self.assessment_b = BehavioralAssessment.objects.create(
            enrollment=self.enrollment_b,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            core_value=self.core_value,
            behavior_indicator=self.behavior_indicator,
            rating=self.rating,
            numeric_score=4.0,
        )

    def test_teacher_only_sees_assigned_section_behavioral_assessments(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get('/api/behavioral-assessments/')
        self.assertEqual(response.status_code, 200)
        assessment_ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.assessment_a.id, assessment_ids)
        self.assertNotIn(self.assessment_b.id, assessment_ids)

    def test_superadmin_sees_all_behavioral_assessments(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get('/api/behavioral-assessments/')
        self.assertEqual(response.status_code, 200)
        assessment_ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.assessment_a.id, assessment_ids)
        self.assertIn(self.assessment_b.id, assessment_ids)

    def test_behavioral_assessment_can_save_without_numeric_score(self):
        assessment = BehavioralAssessment(
            enrollment=self.enrollment_a,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            core_value=self.core_value,
            behavior_indicator=self.behavior_indicator,
            rating=self.rating,
            assessment_date='2025-11-01',
        )
        try:
            assessment.full_clean()
            assessment.save()
        except ValidationError:
            self.fail('BehavioralAssessment should allow null numeric_score for legacy or derived data.')

    def test_quarter_grading_period_requires_quarter(self):
        assessment = BehavioralAssessment(
            enrollment=self.enrollment_a,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            core_value=self.core_value,
            behavior_indicator=self.behavior_indicator,
            rating=self.rating,
            assessment_date='2025-11-01',
        )
        with self.assertRaises(ValidationError) as context:
            assessment.full_clean()
        self.assertIn('quarter', context.exception.message_dict)

    def test_quarter_grading_period_disallows_semester(self):
        assessment = BehavioralAssessment(
            enrollment=self.enrollment_a,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            semester=1,
            core_value=self.core_value,
            behavior_indicator=self.behavior_indicator,
            rating=self.rating,
            assessment_date='2025-11-01',
        )
        with self.assertRaises(ValidationError) as context:
            assessment.full_clean()
        self.assertIn('semester', context.exception.message_dict)

    def test_behavioral_assessment_create_sets_assessed_by(self):
        self.client.force_authenticate(user=self.teacher)
        payload = {
            'enrollment': self.enrollment_a.id,
            'academic_year': self.academic_year.id,
            'grading_period_type': 'Quarter',
            'quarter': 1,
            'core_value': self.core_value.id,
            'behavior_indicator': self.behavior_indicator.id,
            'rating': self.rating.id,
            'numeric_score': 4.0,
            'assessment_date': '2025-11-01',
        }

        response = self.client.post('/api/behavioral-assessments/', payload, format='json')

        self.assertEqual(response.status_code, 201)
        assessment = BehavioralAssessment.objects.get(pk=response.data['id'])
        self.assertEqual(assessment.assessed_by, self.teacher)
