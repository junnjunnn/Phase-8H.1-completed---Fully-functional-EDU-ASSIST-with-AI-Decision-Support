from django.contrib.auth import get_user_model
from django.core.management import call_command
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
        self.rating = BehavioralRating.objects.create(code='AO', label='Always Observed')

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

    def test_teacher_cannot_create_behavior_for_unrelated_section(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post('/api/behavioral-assessments/', {
            'enrollment': self.enrollment_b.id,
            'academic_year': self.academic_year.id,
            'grading_period_type': 'Quarter',
            'quarter': 2,
            'core_value': self.core_value.id,
            'behavior_indicator': self.behavior_indicator.id,
            'rating': self.rating.id,
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('permission', str(response.data).lower())

    def test_adviser_can_assess_students_in_advisory_section(self):
        adviser = self.user_model.objects.create_user(username='adviser_behavior', password='AdviserPass1!')
        UserProfile.objects.create(user=adviser, role_name='TEACHER')
        section = self.enrollment_a.section
        section.adviser = adviser
        section.save(update_fields=['adviser'])
        self.client.force_authenticate(user=adviser)
        response = self.client.post('/api/behavioral-assessments/', {
            'enrollment': self.enrollment_a.id,
            'academic_year': self.academic_year.id,
            'grading_period_type': 'Quarter',
            'quarter': 2,
            'core_value': self.core_value.id,
            'behavior_indicator': self.behavior_indicator.id,
            'rating': self.rating.id,
        }, format='json')
        self.assertEqual(response.status_code, 201)

    def test_bulk_behavior_save_is_atomic_and_updates_existing_record(self):
        self.client.force_authenticate(user=self.teacher)
        payload = [
            {
                'enrollment': self.enrollment_a.id,
                'academic_year': self.academic_year.id,
                'grading_period_type': 'Quarter',
                'quarter': 2,
                'core_value': self.core_value.id,
                'behavior_indicator': self.behavior_indicator.id,
                'rating': self.rating.id,
            },
            {
                'enrollment': self.enrollment_b.id,
                'academic_year': self.academic_year.id,
                'grading_period_type': 'Quarter',
                'quarter': 2,
                'core_value': self.core_value.id,
                'behavior_indicator': self.behavior_indicator.id,
                'rating': self.rating.id,
            },
        ]
        response = self.client.post('/api/behavioral-assessments/bulk/', payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(BehavioralAssessment.objects.filter(enrollment=self.enrollment_a, quarter=2).exists())

        response = self.client.post('/api/behavioral-assessments/bulk/', [payload[0]], format='json')
        self.assertEqual(response.status_code, 201)
        created = BehavioralAssessment.objects.get(enrollment=self.enrollment_a, quarter=2)
        response = self.client.post('/api/behavioral-assessments/bulk/', [{**payload[0], 'rating': self.rating.id}], format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(BehavioralAssessment.objects.filter(enrollment=self.enrollment_a, quarter=2).count(), 1)
        self.assertEqual(response.data['results'][0]['id'], created.id)

    def test_bulk_update_cannot_use_an_unrelated_assessment_id(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post('/api/behavioral-assessments/bulk/', [{
            'id': self.assessment_b.id,
            'enrollment': self.enrollment_a.id,
            'academic_year': self.academic_year.id,
            'grading_period_type': 'Quarter',
            'quarter': 1,
            'core_value': self.core_value.id,
            'behavior_indicator': self.behavior_indicator.id,
            'rating': self.rating.id,
        }], format='json')
        self.assertEqual(response.status_code, 400)
        self.assessment_b.refresh_from_db()
        self.assertEqual(self.assessment_b.enrollment_id, self.enrollment_b.id)

    def test_invalid_source_rating_is_rejected(self):
        invalid_rating = BehavioralRating.objects.create(code='EX', label='Excellent')
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post('/api/behavioral-assessments/', {
            'enrollment': self.enrollment_a.id,
            'academic_year': self.academic_year.id,
            'grading_period_type': 'Quarter',
            'quarter': 2,
            'core_value': self.core_value.id,
            'behavior_indicator': self.behavior_indicator.id,
            'rating': invalid_rating.id,
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('valid DepEd', str(response.data))

    def test_source_behavior_reference_structure_is_returned(self):
        call_command('sync_deped_behavior')
        self.client.force_authenticate(user=self.teacher)
        values = self.client.get('/api/core-values/?is_active=true').data['results']
        indicators = self.client.get('/api/behavior-indicators/?is_active=true').data['results']
        ratings = self.client.get('/api/behavioral-ratings/?is_active=true').data['results']
        self.assertEqual(len(values), 4)
        self.assertEqual(len(indicators), 7)
        self.assertEqual({item['code'] for item in ratings}, {'AO', 'SO', 'RO', 'NO'})

    # Priority 6 Issue 2: Canonical Core Values Tests
    def test_canonical_core_values_are_active_after_sync(self):
        """Verify that canonical DepEd core values are active after sync."""
        call_command('sync_deped_behavior')
        
        canonical_names = {
            'Maka-Diyos (Love for God)',
            'Makatao (Love for Fellowmen)',
            'Maka-Kalikasan (Love for Nature)',
            'Makabansa (Love for Country)',
        }
        active_values = CoreValue.objects.filter(is_active=True)
        active_names = {cv.name for cv in active_values}
        
        for name in canonical_names:
            self.assertIn(name, active_names, f"Canonical value '{name}' should be active")

    def test_legacy_core_values_are_inactive_after_sync(self):
        """Verify that legacy core values are marked inactive after sync."""
        call_command('sync_deped_behavior')
        
        legacy_values = CoreValue.objects.filter(name__in=['Respect', 'Discipline'])
        for cv in legacy_values:
            self.assertFalse(cv.is_active, f"Legacy value '{cv.name}' should be inactive")

    def test_cannot_create_behavioral_assessment_with_inactive_core_value(self):
        """Verify that new behavioral assessments cannot use legacy/inactive core values."""
        call_command('sync_deped_behavior')
        
        # Create an inactive core value manually to simulate legacy data
        inactive_cv = CoreValue.objects.create(name='LegacyValue', is_active=False)
        inactive_indicator = BehaviorIndicator.objects.create(name='LegacyIndicator', core_value=inactive_cv, is_active=False)
        
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post('/api/behavioral-assessments/', {
            'enrollment': self.enrollment_a.id,
            'academic_year': self.academic_year.id,
            'grading_period_type': 'Quarter',
            'quarter': 1,
            'core_value': inactive_cv.id,
            'behavior_indicator': inactive_indicator.id,
            'rating': self.rating.id,
        }, format='json')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('not active', str(response.data).lower())


    def test_can_create_behavioral_assessment_with_maka_diyos(self):
        """Verify that new assessments can use Maka-Diyos core value."""
        call_command('sync_deped_behavior')
        
        cv = CoreValue.objects.get(name='Maka-Diyos (Love for God)')
        indicator = cv.indicators.first()
        
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post('/api/behavioral-assessments/', {
            'enrollment': self.enrollment_a.id,
            'academic_year': self.academic_year.id,
            'grading_period_type': 'Quarter',
            'quarter': 2,
            'core_value': cv.id,
            'behavior_indicator': indicator.id,
            'rating': self.rating.id,
            'assessment_date': '2025-11-01',
        }, format='json')
        
        self.assertEqual(response.status_code, 201)
        assessment = BehavioralAssessment.objects.get(pk=response.data['id'])
        self.assertEqual(assessment.core_value.name, 'Maka-Diyos (Love for God)')

    def test_can_create_behavioral_assessment_with_makatao(self):
        """Verify that new assessments can use Makatao core value."""
        call_command('sync_deped_behavior')
        
        cv = CoreValue.objects.get(name='Makatao (Love for Fellowmen)')
        indicator = cv.indicators.first()
        
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post('/api/behavioral-assessments/', {
            'enrollment': self.enrollment_a.id,
            'academic_year': self.academic_year.id,
            'grading_period_type': 'Quarter',
            'quarter': 2,
            'core_value': cv.id,
            'behavior_indicator': indicator.id,
            'rating': self.rating.id,
            'assessment_date': '2025-11-01',
        }, format='json')
        
        self.assertEqual(response.status_code, 201)

    def test_can_create_behavioral_assessment_with_maka_kalikasan(self):
        """Verify that new assessments can use Maka-Kalikasan core value."""
        call_command('sync_deped_behavior')
        
        cv = CoreValue.objects.get(name='Maka-Kalikasan (Love for Nature)')
        indicator = cv.indicators.first()
        
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post('/api/behavioral-assessments/', {
            'enrollment': self.enrollment_a.id,
            'academic_year': self.academic_year.id,
            'grading_period_type': 'Quarter',
            'quarter': 2,
            'core_value': cv.id,
            'behavior_indicator': indicator.id,
            'rating': self.rating.id,
            'assessment_date': '2025-11-01',
        }, format='json')
        
        self.assertEqual(response.status_code, 201)

    def test_can_create_behavioral_assessment_with_makabansa(self):
        """Verify that new assessments can use Makabansa core value."""
        call_command('sync_deped_behavior')
        
        cv = CoreValue.objects.get(name='Makabansa (Love for Country)')
        indicator = cv.indicators.first()
        
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post('/api/behavioral-assessments/', {
            'enrollment': self.enrollment_a.id,
            'academic_year': self.academic_year.id,
            'grading_period_type': 'Quarter',
            'quarter': 2,
            'core_value': cv.id,
            'behavior_indicator': indicator.id,
            'rating': self.rating.id,
            'assessment_date': '2025-11-01',
        }, format='json')
        
        self.assertEqual(response.status_code, 201)

    def test_can_create_behavioral_assessment_with_ao_rating(self):
        """Verify that AO (Always Observed) rating works."""
        call_command('sync_deped_behavior')
        
        cv = CoreValue.objects.get(name='Maka-Diyos (Love for God)')
        indicator = cv.indicators.first()
        rating = BehavioralRating.objects.get(code='AO')
        
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post('/api/behavioral-assessments/', {
            'enrollment': self.enrollment_a.id,
            'academic_year': self.academic_year.id,
            'grading_period_type': 'Quarter',
            'quarter': 2,
            'core_value': cv.id,
            'behavior_indicator': indicator.id,
            'rating': rating.id,
            'assessment_date': '2025-11-01',
        }, format='json')
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['rating_code'], 'AO')

    def test_can_create_behavioral_assessment_with_so_rating(self):
        """Verify that SO (Sometimes Observed) rating works."""
        call_command('sync_deped_behavior')
        
        cv = CoreValue.objects.get(name='Makatao (Love for Fellowmen)')
        indicator = cv.indicators.first()
        rating = BehavioralRating.objects.get(code='SO')
        
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post('/api/behavioral-assessments/', {
            'enrollment': self.enrollment_a.id,
            'academic_year': self.academic_year.id,
            'grading_period_type': 'Quarter',
            'quarter': 2,
            'core_value': cv.id,
            'behavior_indicator': indicator.id,
            'rating': rating.id,
            'assessment_date': '2025-11-01',
        }, format='json')
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['rating_code'], 'SO')

    def test_can_create_behavioral_assessment_with_ro_rating(self):
        """Verify that RO (Rarely Observed) rating works."""
        call_command('sync_deped_behavior')
        
        cv = CoreValue.objects.get(name='Maka-Kalikasan (Love for Nature)')
        indicator = cv.indicators.first()
        rating = BehavioralRating.objects.get(code='RO')
        
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post('/api/behavioral-assessments/', {
            'enrollment': self.enrollment_a.id,
            'academic_year': self.academic_year.id,
            'grading_period_type': 'Quarter',
            'quarter': 2,
            'core_value': cv.id,
            'behavior_indicator': indicator.id,
            'rating': rating.id,
            'assessment_date': '2025-11-01',
        }, format='json')
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['rating_code'], 'RO')

    def test_can_create_behavioral_assessment_with_no_rating(self):
        """Verify that NO (Not Observed) rating works."""
        call_command('sync_deped_behavior')
        
        cv = CoreValue.objects.get(name='Makabansa (Love for Country)')
        indicator = cv.indicators.first()
        rating = BehavioralRating.objects.get(code='NO')
        
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post('/api/behavioral-assessments/', {
            'enrollment': self.enrollment_a.id,
            'academic_year': self.academic_year.id,
            'grading_period_type': 'Quarter',
            'quarter': 2,
            'core_value': cv.id,
            'behavior_indicator': indicator.id,
            'rating': rating.id,
            'assessment_date': '2025-11-01',
        }, format='json')
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['rating_code'], 'NO')

    def test_historical_legacy_records_are_preserved(self):
        """Verify that historical behavioral records with legacy values are preserved."""
        # Count initial records (setUp creates 2 records)
        count_before_sync = BehavioralAssessment.objects.count()
        self.assertEqual(count_before_sync, 2)
        
        # Verify records are preserved after sync
        call_command('sync_deped_behavior')
        count_after_sync = BehavioralAssessment.objects.count()
        self.assertEqual(count_after_sync, count_before_sync, "Sync should not delete historical records")
        
        # Verify the records still have their original data
        for assessment in BehavioralAssessment.objects.all():
            self.assertIsNotNone(assessment.core_value)
            self.assertIsNotNone(assessment.behavior_indicator)
            self.assertIsNotNone(assessment.rating)


    def test_core_values_endpoint_filters_to_active_by_default(self):
        """Verify that the core values endpoint returns only active values by default."""
        call_command('sync_deped_behavior')
        
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get('/api/core-values/')
        
        # Should only get 4 canonical values, not the 2 legacy values
        self.assertEqual(len(response.data['results']), 4)
        names = {cv['name'] for cv in response.data['results']}
        
        # Should not contain legacy values
        self.assertNotIn('Respect', names)
        self.assertNotIn('Discipline', names)
        
        # Should contain canonical values
        self.assertIn('Maka-Diyos (Love for God)', names)
        self.assertIn('Makatao (Love for Fellowmen)', names)
        self.assertIn('Maka-Kalikasan (Love for Nature)', names)
        self.assertIn('Makabansa (Love for Country)', names)

    def test_behavior_indicators_endpoint_filters_to_active_by_default(self):
        """Verify that behavior indicators endpoint returns only active indicators by default."""
        call_command('sync_deped_behavior')
        
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get('/api/behavior-indicators/')
        
        # Should only get 7 canonical indicators, not the 2 legacy indicators
        self.assertEqual(len(response.data['results']), 7)
        names = {bi['name'] for bi in response.data['results']}
        
        # Should not contain legacy indicators
        self.assertNotIn('Respectful Behavior', names)
        self.assertNotIn('Compliance with school rules', names)

    def test_ratings_endpoint_filters_to_active_by_default(self):
        """Verify that ratings endpoint returns only active ratings by default."""
        call_command('sync_deped_behavior')
        
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get('/api/behavioral-ratings/')
        
        # Should get all 4 canonical ratings
        codes = {r['code'] for r in response.data['results']}
        self.assertEqual(codes, {'AO', 'SO', 'RO', 'NO'})

    def test_adviser_can_view_canonical_behavior_records_for_assigned_students(self):
        """Verify that advisers can view canonical behavior records."""
        call_command('sync_deped_behavior')
        
        # Create an adviser and assign them to a section
        adviser = self.user_model.objects.create_user(username='adviser_view', password='AdviserPass1!')
        UserProfile.objects.create(user=adviser, role_name='TEACHER')
        section = self.enrollment_a.section
        section.adviser = adviser
        section.save(update_fields=['adviser'])
        
        # Create a canonical behavior record for this student
        cv = CoreValue.objects.get(name='Maka-Diyos (Love for God)')
        indicator = cv.indicators.first()
        rating = BehavioralRating.objects.get(code='AO')
        
        BehavioralAssessment.objects.create(
            enrollment=self.enrollment_a,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=3,
            core_value=cv,
            behavior_indicator=indicator,
            rating=rating,
            assessed_by=adviser,
            assessment_date='2025-11-20',
        )
        
        # Adviser should see this record
        self.client.force_authenticate(user=adviser)
        response = self.client.get('/api/behavioral-assessments/')
        
        assessment_ids = {item['id'] for item in response.data['results']}
        canonical_record = BehavioralAssessment.objects.get(core_value__name='Maka-Diyos (Love for God)')
        self.assertIn(canonical_record.id, assessment_ids)

    def test_adviser_cannot_view_other_advisers_student_behavior_records(self):
        """Verify that adviser authorization is preserved."""
        call_command('sync_deped_behavior')
        
        adviser1 = self.user_model.objects.create_user(username='adviser1', password='AdviserPass1!')
        adviser2 = self.user_model.objects.create_user(username='adviser2', password='AdviserPass1!')
        UserProfile.objects.create(user=adviser1, role_name='TEACHER')
        UserProfile.objects.create(user=adviser2, role_name='TEACHER')
        
        section_a = self.enrollment_a.section
        section_a.adviser = adviser1
        section_a.save(update_fields=['adviser'])
        
        section_b = self.enrollment_b.section
        section_b.adviser = adviser2
        section_b.save(update_fields=['adviser'])
        
        # Create a canonical record for student_a
        cv = CoreValue.objects.get(name='Maka-Diyos (Love for God)')
        indicator = cv.indicators.first()
        rating = BehavioralRating.objects.get(code='AO')
        
        record_a = BehavioralAssessment.objects.create(
            enrollment=self.enrollment_a,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=3,
            core_value=cv,
            behavior_indicator=indicator,
            rating=rating,
            assessed_by=adviser1,
            assessment_date='2025-11-20',
        )
        
        # Adviser 2 should NOT see adviser 1's student's record
        self.client.force_authenticate(user=adviser2)
        response = self.client.get('/api/behavioral-assessments/')
        
        assessment_ids = {item['id'] for item in response.data['results']}
        self.assertNotIn(record_a.id, assessment_ids)

