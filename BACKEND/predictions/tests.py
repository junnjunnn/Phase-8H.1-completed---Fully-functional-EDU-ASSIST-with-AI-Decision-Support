from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from academics.models import AcademicYear, GradeLevel, Section, Enrollment, Subject, AcademicRecord
from attendance.models import AttendanceRecord
from audit.models import AuditLog
from interventions.models import Intervention
from predictions.models import RiskPrediction, PredictionFactor
from predictions.services.prediction_service import FeatureContractError, PredictionService
from behavior.models import BehavioralAssessment, BehavioralRating, BehaviorIndicator, CoreValue
from students.models import Student


class PredictionsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()

        self.superadmin = self.user_model.objects.create_user(username='superadmin_predictions', password='SuperPass1!')
        UserProfile.objects.create(user=self.superadmin, role_name='SUPER_ADMIN')

        self.teacher = self.user_model.objects.create_user(username='teacher_predictions', password='TeacherPass1!')
        teacher_profile = UserProfile.objects.create(user=self.teacher, role_name='TEACHER')

        self.academic_year = AcademicYear.objects.create(name='2025-2026', start_date='2025-06-01', end_date='2026-03-31', is_active=True)
        # Use the grade level from Phase 1 migration (0004)
        self.grade_level = GradeLevel.objects.get(code='G4')
        section_a = Section.objects.create(name='A', grade_level=self.grade_level, academic_year=self.academic_year)
        self.section_b = Section.objects.create(name='B', grade_level=self.grade_level, academic_year=self.academic_year)
        teacher_profile.assigned_sections.add(section_a)

        self.student_a = Student.objects.create(first_name='Alice', last_name='Anderson', gender='Female', student_status='active')
        self.student_b = Student.objects.create(first_name='Bob', last_name='Baker', gender='Male', student_status='active')

        self.enrollment_a = Enrollment.objects.create(student=self.student_a, academic_year=self.academic_year, grade_level=self.grade_level, section=section_a, enrollment_status='active')
        self.enrollment_b = Enrollment.objects.create(student=self.student_b, academic_year=self.academic_year, grade_level=self.grade_level, section=self.section_b, enrollment_status='active')

        self.prediction_a = RiskPrediction.objects.create(
            enrollment=self.enrollment_a,
            prediction_type='Academic Risk',
            risk_level='Low',
            probability=0.2500,
            model_name='risk_model',
            model_version='1.0',
        )
        self.prediction_b = RiskPrediction.objects.create(
            enrollment=self.enrollment_b,
            prediction_type='Academic Risk',
            risk_level='High',
            probability=0.9000,
            model_name='risk_model',
            model_version='1.0',
        )
        self.factor_a = PredictionFactor.objects.create(prediction=self.prediction_a, feature_name='attendance', feature_value='good', contribution=0.25, direction='positive')
        self.factor_b = PredictionFactor.objects.create(prediction=self.prediction_b, feature_name='attendance', feature_value='poor', contribution=0.90, direction='negative')

    def test_prediction_service_uses_canonical_binary_contract(self):
        service = PredictionService()

        self.assertEqual(service.ml_prediction_label(1), 'At Risk')
        self.assertEqual(service.ml_prediction_label(0), 'Not At Risk')
        self.assertEqual(service.application_risk_level('At Risk'), 'High')
        self.assertEqual(service.application_risk_level('Not At Risk'), 'Low')
        self.assertNotIn(service.application_risk_level('At Risk'), ['Low', 'Moderate'])
        self.assertNotIn(service.application_risk_level('Not At Risk'), ['High', 'Moderate'])

    def test_teacher_only_sees_assigned_section_risk_predictions(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get('/api/risk-predictions/')
        self.assertEqual(response.status_code, 200)
        prediction_ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.prediction_a.id, prediction_ids)
        self.assertNotIn(self.prediction_b.id, prediction_ids)

    def test_teacher_only_sees_assigned_section_prediction_factors(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get('/api/prediction-factors/')
        self.assertEqual(response.status_code, 200)
        factor_ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.factor_a.id, factor_ids)
        self.assertNotIn(self.factor_b.id, factor_ids)

    def test_superadmin_sees_all_risk_predictions(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get('/api/risk-predictions/')
        self.assertEqual(response.status_code, 200)
        prediction_ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.prediction_a.id, prediction_ids)
        self.assertIn(self.prediction_b.id, prediction_ids)

    def test_current_predictions_exclude_archived_students_and_inactive_context(self):
        archived_student = Student.objects.create(first_name='Archived', last_name='Learner', gender='Female', student_status='archived')
        archived_enrollment = Enrollment.objects.create(
            student=archived_student, academic_year=self.academic_year, grade_level=self.grade_level,
            section=self.enrollment_a.section, enrollment_status='active',
        )
        archived_prediction = RiskPrediction.objects.create(
            enrollment=archived_enrollment, prediction_type='Academic Risk', risk_level='High', probability=0.9,
        )
        inactive_enrollment = self.enrollment_b
        inactive_enrollment.enrollment_status = 'inactive'
        inactive_enrollment.save(update_fields=['enrollment_status'])
        inactive_prediction = RiskPrediction.objects.create(
            enrollment=inactive_enrollment, prediction_type='Academic Risk', risk_level='High', probability=0.9,
        )
        archived_year = AcademicYear.objects.create(name='Archived Year', start_date='2024-06-01', end_date='2025-03-31', is_active=False)
        archived_section = Section.objects.create(name='Archived Context', grade_level=self.grade_level, academic_year=archived_year, is_active=False)
        historical_enrollment = Enrollment.objects.create(
            student=self.student_b, academic_year=archived_year, grade_level=self.grade_level,
            section=archived_section, enrollment_status='active',
        )
        historical_prediction = RiskPrediction.objects.create(
            enrollment=historical_enrollment, prediction_type='Academic Risk', risk_level='High', probability=0.9,
        )

        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get('/api/risk-predictions/')
        self.assertEqual(response.status_code, 200)
        prediction_ids = {item['id'] for item in response.data['results']}
        self.assertIn(self.prediction_a.id, prediction_ids)
        self.assertNotIn(archived_prediction.id, prediction_ids)
        self.assertNotIn(inactive_prediction.id, prediction_ids)
        self.assertNotIn(historical_prediction.id, prediction_ids)
        self.assertTrue(RiskPrediction.objects.filter(pk=archived_prediction.pk).exists())

    def test_prediction_response_resolves_student_name(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get('/api/risk-predictions/')
        item = next(item for item in response.data['results'] if item['id'] == self.prediction_a.id)
        self.assertEqual(item['student_id'], self.student_a.id)
        self.assertEqual(item['student_name'], 'Alice Anderson')

    def test_archived_student_generation_is_rejected_without_creating_prediction(self):
        self.client.force_authenticate(user=self.superadmin)
        before_count = RiskPrediction.objects.count()
        self.student_a.student_status = 'archived'
        self.student_a.save(update_fields=['student_status'])

        response = self.client.post(f'/api/predictions/predict/{self.student_a.id}/')
        self.assertEqual(response.status_code, 422)
        self.assertEqual(RiskPrediction.objects.count(), before_count)

    def test_archiving_student_hides_prediction_and_restore_returns_it(self):
        self.client.force_authenticate(user=self.superadmin)
        self.student_a.student_status = 'archived'
        self.student_a.save(update_fields=['student_status'])
        response = self.client.get('/api/risk-predictions/')
        self.assertNotIn(self.prediction_a.id, {item['id'] for item in response.data['results']})
        self.assertTrue(RiskPrediction.objects.filter(pk=self.prediction_a.pk).exists())

        self.student_a.student_status = 'active'
        self.student_a.save(update_fields=['student_status'])
        response = self.client.get('/api/risk-predictions/')
        self.assertIn(self.prediction_a.id, {item['id'] for item in response.data['results']})

    def test_dashboard_summary_endpoint_returns_risk_metrics(self):
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get('/api/dashboard-summary/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('total_students', data)
        self.assertIn('total_predictions', data)
        self.assertIn('at_risk_students', data)
        self.assertIn('high_risk_students', data)
        self.assertEqual(data['total_predictions'], 2)
        self.assertEqual(data['high_risk_students'], 1)
        self.assertEqual(data['moderate_risk_students'], 0)
        self.assertEqual(data['low_risk_students'], 1)

    def test_dashboard_summary_excludes_archived_school_year_data(self):
        archived_year = AcademicYear.objects.create(name='2024-2025', start_date='2024-06-01', end_date='2025-03-31', is_active=False)
        archived_grade = GradeLevel.objects.get(code='G4')
        archived_section = Section.objects.create(name='Archived Section', grade_level=archived_grade, academic_year=archived_year)
        archived_student = Student.objects.create(first_name='Archived', last_name='Student', gender='Female', student_status='active')
        archived_enrollment = Enrollment.objects.create(
            student=archived_student,
            academic_year=archived_year,
            grade_level=archived_grade,
            section=archived_section,
            enrollment_status='active',
        )
        RiskPrediction.objects.create(
            enrollment=archived_enrollment,
            prediction_type='Academic Risk',
            risk_level='High',
            probability=0.9500,
            model_name='risk_model',
            model_version='1.0',
        )

        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get('/api/dashboard-summary/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['total_students'], 2)
        self.assertEqual(data['total_predictions'], 2)
        self.assertEqual(data['high_risk_students'], 1)
        self.assertEqual(data['low_risk_students'], 1)

    def test_dashboard_summary_excludes_archived_students_and_restores_count_on_restore(self):
        self.client.force_authenticate(user=self.superadmin)

        self.student_a.student_status = 'archived'
        self.student_a.save(update_fields=['student_status'])

        response = self.client.get('/api/dashboard-summary/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['total_students'], 1)
        self.assertEqual(Student.objects.get(pk=self.student_a.pk).student_status, 'archived')
        self.assertTrue(self.student_a.enrollments.filter(enrollment_status='active').exists())

        self.student_a.student_status = 'active'
        self.student_a.save(update_fields=['student_status'])

        response = self.client.get('/api/dashboard-summary/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['total_students'], 2)

    def test_dashboard_excludes_archived_student_child_records_and_restores_metrics(self):
        subject = Subject.objects.create(code='DASH-MATH', name='Dashboard Mathematics', category='Learning Area', grade_level=self.grade_level)
        core_value = CoreValue.objects.create(name='Dashboard Respect')
        indicator = BehaviorIndicator.objects.create(name='Dashboard respect indicator', core_value=core_value)
        rating = BehavioralRating.objects.create(code='DASH-AO', label='Dashboard observed', numeric_value=4)
        AcademicRecord.objects.create(
            enrollment=self.enrollment_a,
            subject=subject,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            grade=95,
            final_grade=95,
        )
        AttendanceRecord.objects.create(
            enrollment=self.enrollment_a,
            month='June',
            school_days=20,
            days_present=18,
            absences=2,
        )
        BehavioralAssessment.objects.create(
            enrollment=self.enrollment_a,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            core_value=core_value,
            behavior_indicator=indicator,
            rating=rating,
            numeric_score=4,
        )
        Intervention.objects.create(
            enrollment=self.enrollment_a,
            intervention_type='Tutoring',
            status='planned',
        )

        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get('/api/dashboard-summary/')
        self.assertEqual(response.status_code, 200)
        before = response.json()
        self.assertEqual(before['total_students'], 2)
        self.assertEqual(before['total_predictions'], 2)
        self.assertEqual(before['intervention_status_distribution']['planned'], 1)
        self.assertEqual(before['behavior_rating_distribution']['Dashboard observed'], 1)
        self.assertEqual(before['academic_performance_distribution']['Excellent'], 1)

        self.student_a.student_status = 'archived'
        self.student_a.save(update_fields=['student_status'])
        response = self.client.get('/api/dashboard-summary/?include_archived=true')
        archived = response.json()
        self.assertEqual(archived['total_students'], 1)
        self.assertEqual(archived['total_predictions'], 1)
        self.assertNotIn('planned', archived['intervention_status_distribution'])
        self.assertNotIn('Dashboard observed', archived['behavior_rating_distribution'])
        self.assertEqual(archived['academic_performance_distribution']['Excellent'], 0)

        self.student_a.student_status = 'active'
        self.student_a.save(update_fields=['student_status'])
        response = self.client.get('/api/dashboard-summary/')
        restored = response.json()
        self.assertEqual(restored['total_students'], 2)
        self.assertEqual(restored['total_predictions'], 2)
        self.assertEqual(restored['intervention_status_distribution']['planned'], 1)
        self.assertEqual(restored['academic_performance_distribution']['Excellent'], 1)

    def test_predict_student_endpoint_creates_prediction(self):
        self.client.force_authenticate(user=self.superadmin)
        self._create_compatible_behavior(self.enrollment_a)
        subject = Subject.objects.create(code='MATH', name='Mathematics', category='Core', grade_level=self.grade_level)
        AcademicRecord.objects.create(
            enrollment=self.enrollment_a,
            subject=subject,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            grade=65,
            final_grade=65,
        )
        response = self.client.post(f'/api/predictions/predict/{self.student_a.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['prediction'], 'At Risk')
        self.assertTrue(RiskPrediction.objects.filter(enrollment=self.enrollment_a).exists())

    def test_predict_student_response_matches_persisted_prediction_record(self):
        self.client.force_authenticate(user=self.superadmin)
        self._create_compatible_behavior(self.enrollment_a)
        subject = Subject.objects.create(code='MATH_RESPONSE', name='Mathematics', category='Core', grade_level=self.grade_level)
        AcademicRecord.objects.create(
            enrollment=self.enrollment_a,
            subject=subject,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            grade=72,
            final_grade=72,
        )

        response = self.client.post(f'/api/predictions/predict/{self.student_a.id}/')
        self.assertEqual(response.status_code, 200)

        latest_prediction = RiskPrediction.objects.filter(enrollment=self.enrollment_a).order_by('-prediction_date').first()
        self.assertIsNotNone(latest_prediction)
        self.assertEqual(response.data['prediction_id'], latest_prediction.id)
        self.assertEqual(response.data['prediction'], 'At Risk')
        self.assertEqual(float(response.data['probability']), float(latest_prediction.probability))
        self.assertEqual(response.data['generated_at'], latest_prediction.prediction_date.isoformat())
        self.assertEqual(response.data['explanation'], latest_prediction.explanation)

    def test_behavior_rating_code_remains_compatible_with_prediction_features(self):
        core_value = CoreValue.objects.create(name='Maka-Diyos')
        indicator = BehaviorIndicator.objects.create(
            name='Shows adherence to ethical principles by upholding truth',
            core_value=core_value,
        )
        rating = BehavioralRating.objects.create(code='AO', label='Always Observed')
        BehavioralAssessment.objects.create(
            enrollment=self.enrollment_a,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            core_value=core_value,
            behavior_indicator=indicator,
            rating=rating,
        )
        _, feature_values = PredictionService().build_feature_vector(self.student_a.id)
        self.assertEqual(feature_values['behavior_teacher_rating'], 'AO')
        self.assertEqual(feature_values['behavior_core_value'], 'Maka-Diyos')
        self.assertEqual(feature_values['behavior_indicator'], 'Shows adherence to ethical principles by upholding truth')

    def test_all_source_behavior_rating_codes_are_model_compatible(self):
        core_value = CoreValue.objects.create(name='Makatao')
        indicator = BehaviorIndicator.objects.create(
            name='Demonstrate contributions toward solidarity',
            core_value=core_value,
        )
        for code in ['AO', 'SO', 'RO', 'NO']:
            BehavioralAssessment.objects.filter(enrollment=self.enrollment_a).delete()
            rating = BehavioralRating.objects.create(code=code, label=code)
            BehavioralAssessment.objects.create(
                enrollment=self.enrollment_a,
                academic_year=self.academic_year,
                grading_period_type='Quarter',
                quarter=1,
                core_value=core_value,
                behavior_indicator=indicator,
                rating=rating,
            )
            _, feature_values = PredictionService().build_feature_vector(self.student_a.id)
            self.assertEqual(feature_values['behavior_teacher_rating'], code)

    def test_generate_prediction_creates_a_new_prediction_record_for_updated_data(self):
        self.client.force_authenticate(user=self.superadmin)
        before_count = RiskPrediction.objects.filter(enrollment=self.enrollment_a).count()

        self._create_compatible_behavior(self.enrollment_a)
        subject = Subject.objects.create(code='MATH_REGEN', name='Mathematics', category='Core', grade_level=self.grade_level)
        AcademicRecord.objects.create(
            enrollment=self.enrollment_a,
            subject=subject,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            grade=65,
            final_grade=65,
        )

        first = self.client.post(f'/api/predictions/predict/{self.student_a.id}/')
        second = self.client.post(f'/api/predictions/predict/{self.student_a.id}/')

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertNotEqual(first.data['prediction_id'], second.data['prediction_id'])
        self.assertEqual(RiskPrediction.objects.filter(enrollment=self.enrollment_a).count(), before_count + 2)

        first_prediction = RiskPrediction.objects.filter(enrollment=self.enrollment_a).order_by('prediction_date').first()
        second_prediction = RiskPrediction.objects.filter(enrollment=self.enrollment_a).order_by('prediction_date').last()
        self.assertLess(first_prediction.prediction_date, second_prediction.prediction_date)
        self.assertEqual(second.data['prediction_id'], second_prediction.id)

    def test_teacher_cannot_generate_prediction_for_unrelated_student(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post(f'/api/predictions/predict/{self.student_b.id}/')
        self.assertEqual(response.status_code, 403)

    def test_latest_prediction_and_factors_reflect_the_newest_generated_record(self):
        self.client.force_authenticate(user=self.superadmin)
        self._create_compatible_behavior(self.enrollment_a)
        subject = Subject.objects.create(code='MATH_LATEST', name='Mathematics', category='Core', grade_level=self.grade_level)
        AcademicRecord.objects.create(
            enrollment=self.enrollment_a,
            subject=subject,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            grade=80,
            final_grade=80,
        )

        first = self.client.post(f'/api/predictions/predict/{self.student_a.id}/')
        second = self.client.post(f'/api/predictions/predict/{self.student_a.id}/')

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)

        newest_prediction = RiskPrediction.objects.filter(enrollment=self.enrollment_a).order_by('-prediction_date').first()
        newest_factors = list(PredictionFactor.objects.filter(prediction=newest_prediction).values_list('id', flat=True))

        response = self.client.get('/api/prediction-factors/', {'prediction': newest_prediction.id, 'ordering': 'feature_name'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['results'])
        self.assertEqual({item['id'] for item in response.data['results']}, set(newest_factors))
        self.assertTrue(all(item['prediction'] == newest_prediction.id for item in response.data['results']))

    def test_behavior_feature_vector_keeps_trained_model_shape(self):
        service = PredictionService()
        frame, _ = service.build_feature_vector(self.student_a.id)
        self.assertEqual(list(frame.columns), list(service.model.feature_names_in_))
        self.assertEqual(len(frame.columns), self.service_model_feature_count())

    def test_recognized_subject_grade_populates_model_feature(self):
        subject = Subject.objects.create(code='MATH_RECOGNIZED', name='Mathematics', category='Core', grade_level=self.grade_level)
        AcademicRecord.objects.create(
            enrollment=self.enrollment_a,
            subject=subject,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            grade=99,
            final_grade=99,
        )

        frame, feature_values = PredictionService().build_feature_vector(self.student_a.id)

        self.assertEqual(feature_values['mathematics_grade'], 99.0)
        self.assertEqual(frame.iloc[0]['mathematics_grade'], 99.0)
        self.assertFalse(any(diagnostic.startswith("Subject '") for diagnostic in feature_values['contract_diagnostics']))

    def test_education_grade_is_represented_by_its_own_model_feature(self):
        subject = Subject.objects.create(code='EDU', name='EDUCATION', category='Core', grade_level=self.grade_level)
        AcademicRecord.objects.create(
            enrollment=self.enrollment_a,
            subject=subject,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            grade=99,
            final_grade=99,
        )

        frame, feature_values = PredictionService().build_feature_vector(self.student_a.id)

        self.assertEqual(feature_values['general_average'], 99.0)
        self.assertEqual(feature_values['education_grade'], 99.0)
        self.assertEqual(frame.iloc[0]['education_grade'], 99.0)
        self.assertFalse(any(diagnostic.startswith("Subject '") for diagnostic in feature_values['contract_diagnostics']))

    def test_unsupported_subject_grade_is_rejected_instead_of_discarded(self):
        subject = Subject.objects.create(code='SOC', name='Sociology', category='Core', grade_level=self.grade_level)
        AcademicRecord.objects.create(
            enrollment=self.enrollment_a,
            subject=subject,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            grade=99,
            final_grade=99,
        )

        frame, feature_values = PredictionService().build_feature_vector(self.student_a.id)

        self.assertEqual(feature_values['general_average'], 99.0)
        self.assertEqual(frame.iloc[0]['education_grade'], 0.0)
        self.assertIn("Subject 'Sociology' is not represented", feature_values['contract_diagnostics'][0])
        self.assertIn('grade 99.0 was not encoded', feature_values['contract_diagnostics'][0])

    def test_current_domain_academic_categories_are_encoded(self):
        year = AcademicYear.objects.create(name='New School Year', start_date='2026-06-01', end_date='2027-03-31')
        grade_level = GradeLevel.objects.get(code='G1')
        section = Section.objects.create(name='Moonstone', grade_level=grade_level, academic_year=year)
        student = Student.objects.create(first_name='Unknown', last_name='Values', gender='Female', student_status='active')
        enrollment = Enrollment.objects.create(student=student, academic_year=year, grade_level=grade_level, section=section, enrollment_status='active')
        self._create_compatible_behavior(enrollment)

        frame, feature_values = PredictionService().build_feature_vector(student.id)
        diagnostics = ' '.join(feature_values['contract_diagnostics'])

        self.assertEqual(diagnostics, '')
        self.assertEqual(frame.iloc[0]['school_year_New School Year'], 1.0)
        self.assertEqual(frame.iloc[0]['grade_level_Grade 1'], 1.0)
        self.assertEqual(frame.iloc[0]['section_Moonstone'], 1.0)

    def test_no_intervention_uses_explicit_slot_and_zero_counts(self):
        self._create_compatible_behavior(self.enrollment_a)
        frame, feature_values = PredictionService().build_feature_vector(self.student_a.id)

        self.assertEqual(feature_values['has_intervention'], 0)
        self.assertEqual(feature_values['number_of_interventions'], 0)
        self.assertEqual(frame.iloc[0]['intervention_type_No Intervention'], 1.0)
        self.assertEqual(frame.filter(regex='^intervention_type_').to_numpy().sum(), 1.0)

    def test_current_aggregation_contract_uses_all_related_records_without_canonical_subject_selection(self):
        subject = Subject.objects.create(code='MATH_CURRENT', name='Mathematics', category='Core', grade_level=self.grade_level)
        self._create_compatible_behavior(self.enrollment_a)

        AcademicRecord.objects.create(
            enrollment=self.enrollment_a,
            subject=subject,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            grade=80,
            final_grade=80,
        )
        AcademicRecord.objects.create(
            enrollment=self.enrollment_a,
            subject=subject,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=2,
            grade=92,
            final_grade=92,
        )

        AttendanceRecord.objects.create(
            enrollment=self.enrollment_a,
            attendance_date='2025-08-01',
            month='2025-08',
            school_days=20,
            days_present=18,
            absences=2,
            times_tardy=1,
        )
        AttendanceRecord.objects.create(
            enrollment=self.enrollment_a,
            attendance_date='2025-09-01',
            month='2025-09',
            school_days=20,
            days_present=17,
            absences=3,
            times_tardy=1,
        )

        core_value = CoreValue.objects.create(name='Makatao (Love for Fellowmen)')
        indicator = BehaviorIndicator.objects.create(
            name='Demonstrate contributions toward solidarity',
            core_value=core_value,
        )
        ao_rating = BehavioralRating.objects.get_or_create(code='AO', defaults={'label': 'Always Observed'})[0]
        so_rating = BehavioralRating.objects.get_or_create(code='SO', defaults={'label': 'Sometimes Observed'})[0]

        BehavioralAssessment.objects.create(
            enrollment=self.enrollment_a,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            core_value=core_value,
            behavior_indicator=indicator,
            rating=ao_rating,
        )
        BehavioralAssessment.objects.create(
            enrollment=self.enrollment_a,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=2,
            core_value=core_value,
            behavior_indicator=indicator,
            rating=so_rating,
        )
        BehavioralAssessment.objects.create(
            enrollment=self.enrollment_a,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=3,
            core_value=core_value,
            behavior_indicator=indicator,
            rating=ao_rating,
        )

        Intervention.objects.create(
            enrollment=self.enrollment_a,
            risk_type='Academic Risk',
            intervention_type='Tutoring',
            recommendation='Review missed lessons.',
            status='planned',
            priority='medium',
        )
        Intervention.objects.create(
            enrollment=self.enrollment_a,
            risk_type='Academic Risk',
            intervention_type='Counseling',
            recommendation='Follow-up with student support.',
            status='in_progress',
            priority='high',
        )

        frame, feature_values = PredictionService().build_feature_vector(self.student_a.id)

        self.assertEqual(feature_values['general_average'], 86.0)
        self.assertEqual(feature_values['mathematics_grade'], 92.0)
        self.assertEqual(feature_values['present_days'], 35)
        self.assertEqual(feature_values['absent_days'], 5)
        self.assertEqual(feature_values['late_days'], 2)
        self.assertEqual(feature_values['attendance_rate'], 87.5)
        self.assertEqual(feature_values['behavior_teacher_rating'], 'AO')
        self.assertEqual(feature_values['intervention_type'], 'Counseling')
        self.assertEqual(feature_values['intervention_outcome'], 'Not Yet Evaluated')
        self.assertEqual(feature_values['has_intervention'], 1)
        self.assertEqual(feature_values['number_of_interventions'], 2)
        self.assertEqual(frame.iloc[0]['mathematics_grade'], 92.0)
        self.assertEqual(frame.iloc[0]['intervention_type_Counseling'], 1.0)

    def test_missing_related_record_collections_default_to_zero_and_not_yet_evaluated(self):
        student = Student.objects.create(first_name='Missing', last_name='Records', gender='Female', student_status='active')
        enrollment = Enrollment.objects.create(student=student, academic_year=self.academic_year, grade_level=self.grade_level, section=self.section_b, enrollment_status='active')

        frame, feature_values = PredictionService().build_feature_vector(student.id)

        self.assertEqual(feature_values['general_average'], 0.0)
        self.assertEqual(feature_values['mathematics_grade'], 0.0)
        self.assertEqual(feature_values['present_days'], 0)
        self.assertEqual(feature_values['absent_days'], 0)
        self.assertEqual(feature_values['late_days'], 0)
        self.assertEqual(feature_values['has_intervention'], 0)
        self.assertEqual(feature_values['number_of_interventions'], 0)
        self.assertEqual(feature_values['intervention_outcome'], 'Not Yet Evaluated')
        self.assertEqual(frame.iloc[0]['intervention_type_No Intervention'], 1.0)

    def test_behavior_rating_codes_use_exact_model_one_hot_slots(self):
        expected_columns = {
            'AO': 'behavior_teacher_rating_AO',
            'SO': 'behavior_teacher_rating_SO',
            'RO': 'behavior_teacher_rating_RO',
            'NO': 'behavior_teacher_rating_NO',
        }
        for code, expected_column in expected_columns.items():
            BehavioralAssessment.objects.filter(enrollment=self.enrollment_a).delete()
            self._create_compatible_behavior(self.enrollment_a, code=code)
            frame, _ = PredictionService().build_feature_vector(self.student_a.id)
            rating_frame = frame.filter(regex='^behavior_teacher_rating_')
            self.assertEqual(rating_frame.to_numpy().sum(), 1.0)
            self.assertEqual(frame.iloc[0][expected_column], 1.0)

    def test_predict_student_endpoint_creates_audit_log(self):
        self.client.force_authenticate(user=self.superadmin)
        self._create_compatible_behavior(self.enrollment_a)
        subject = Subject.objects.create(code='MATH', name='Mathematics', category='Core', grade_level=self.grade_level)
        AcademicRecord.objects.create(
            enrollment=self.enrollment_a,
            subject=subject,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            grade=65,
            final_grade=65,
        )

        response = self.client.post(f'/api/predictions/predict/{self.student_a.id}/')

        self.assertEqual(response.status_code, 200)
        audit_entry = AuditLog.objects.filter(
            user=self.superadmin,
            action='PREDICTION_GENERATED',
            module='predictions',
            object_type='RiskPrediction',
        ).first()
        self.assertIsNotNone(audit_entry)
        self.assertIn(str(self.student_a.id), audit_entry.object_id)
        self.assertIn(str(response.json()['prediction']), audit_entry.object_id)
        self.assertIn(str(response.json()['probability']), audit_entry.object_id)

    def test_predict_student_endpoint_persists_readable_explanation_summary(self):
        self.client.force_authenticate(user=self.superadmin)
        student = Student.objects.create(first_name='Clara', last_name='Cole', gender='Female', student_status='active')
        enrollment = Enrollment.objects.create(student=student, academic_year=self.academic_year, grade_level=self.grade_level, section=self.section_b, enrollment_status='active')
        self._create_compatible_behavior(enrollment)
        subject = Subject.objects.create(code='MATH', name='Mathematics', category='Core', grade_level=self.grade_level)
        AcademicRecord.objects.create(
            enrollment=enrollment,
            subject=subject,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            grade=65,
            final_grade=65,
        )

        response = self.client.post(f'/api/predictions/predict/{student.id}/')
        self.assertEqual(response.status_code, 200)

        prediction = RiskPrediction.objects.filter(enrollment=enrollment).order_by('-prediction_date').first()
        self.assertIsNotNone(prediction)
        self.assertIsInstance(prediction.explanation, str)
        self.assertIn('Prediction:', prediction.explanation)
        self.assertIn('Top Factors:', prediction.explanation)
        self.assertGreaterEqual(PredictionFactor.objects.filter(prediction=prediction).count(), 1)

    def test_prediction_explanation_uses_model_estimate_language(self):
        self.client.force_authenticate(user=self.superadmin)
        student = Student.objects.create(first_name='Mina', last_name='Mendez', gender='Female', student_status='active')
        enrollment = Enrollment.objects.create(student=student, academic_year=self.academic_year, grade_level=self.grade_level, section=self.section_b, enrollment_status='active')
        self._create_compatible_behavior(enrollment)
        subject = Subject.objects.create(code='MATH_MODEL', name='Mathematics', category='Core', grade_level=self.grade_level)
        AcademicRecord.objects.create(
            enrollment=enrollment,
            subject=subject,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            grade=62,
            final_grade=62,
        )

        response = self.client.post(f'/api/predictions/predict/{student.id}/')
        self.assertEqual(response.status_code, 200)

        prediction = RiskPrediction.objects.filter(enrollment=enrollment).order_by('-prediction_date').first()
        explanation = prediction.explanation.lower()
        self.assertIn('ai risk prediction', explanation)
        self.assertIn('model found patterns', explanation)
        self.assertIn('not a diagnosis', explanation)
        self.assertIn('teacher review focus', explanation)

    def test_prediction_factors_avoid_causal_claims(self):
        self.client.force_authenticate(user=self.superadmin)
        student = Student.objects.create(first_name='Noel', last_name='Nora', gender='Male', student_status='active')
        enrollment = Enrollment.objects.create(student=student, academic_year=self.academic_year, grade_level=self.grade_level, section=self.section_b, enrollment_status='active')
        self._create_compatible_behavior(enrollment)
        subject = Subject.objects.create(code='ENG_FACTOR', name='English', category='Core', grade_level=self.grade_level)
        AcademicRecord.objects.create(
            enrollment=enrollment,
            subject=subject,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            grade=50,
            final_grade=50,
        )

        response = self.client.post(f'/api/predictions/predict/{student.id}/')
        self.assertEqual(response.status_code, 200)

        prediction = RiskPrediction.objects.filter(enrollment=enrollment).order_by('-prediction_date').first()
        factor = PredictionFactor.objects.filter(prediction=prediction).order_by('id').first()
        self.assertIsNotNone(factor)
        text = factor.explanation_text.lower()
        self.assertIn('considered by the model', text)
        self.assertNotIn('caused', text)
        self.assertNotIn('global feature importance', text)

    def test_prediction_service_binary_classes_remain_hardcoded(self):
        self.client.force_authenticate(user=self.superadmin)
        student = Student.objects.create(first_name='Binary', last_name='Model', gender='Female', student_status='active')
        enrollment = Enrollment.objects.create(student=student, academic_year=self.academic_year, grade_level=self.grade_level, section=self.section_b, enrollment_status='active')
        self._create_compatible_behavior(enrollment)
        subject = Subject.objects.create(code='MATH_BINARY', name='Mathematics', category='Core', grade_level=self.grade_level)
        AcademicRecord.objects.create(
            enrollment=enrollment,
            subject=subject,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            grade=80,
            final_grade=80,
        )

        result = PredictionService().predict_for_student(student.id)
        self.assertIn(result['prediction'], ['At Risk', 'Not At Risk'])
        self.assertGreaterEqual(result['probability'], 0)
        self.assertLessEqual(result['probability'], 1)
        self.assertNotIn(result['prediction'], ['Low', 'Moderate', 'High'])

    def test_valid_feature_vector_matches_71_feature_contract(self):
        self._create_compatible_behavior(self.enrollment_a)
        subject = Subject.objects.create(code='MATH_71', name='Mathematics', category='Core', grade_level=self.grade_level)
        AcademicRecord.objects.create(
            enrollment=self.enrollment_a,
            subject=subject,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            grade=88,
            final_grade=88,
        )

        service = PredictionService()
        feature_frame, feature_values = service.build_feature_vector(self.student_a.id)
        service.validate_feature_frame(feature_frame, feature_values)

        self.assertEqual(len(feature_frame.columns), 71)
        self.assertEqual(list(feature_frame.columns), list(service.model.feature_names_in_))
        self.assertEqual(feature_frame.shape[1], service.model.n_features_in_)

    def test_wrong_feature_count_is_rejected(self):
        service = PredictionService()
        feature_frame, feature_values = service.build_feature_vector(self.student_a.id)
        reduced_frame = feature_frame.iloc[:, :-1]

        with self.assertRaises(FeatureContractError):
            service.validate_feature_frame(reduced_frame, feature_values)

    def test_unknown_categorical_value_is_rejected_before_model_predict(self):
        student = Student.objects.create(first_name='Invalid', last_name='Category', gender='Female', student_status='active')
        enrollment = Enrollment.objects.create(student=student, academic_year=self.academic_year, grade_level=self.grade_level, section=self.section_b, enrollment_status='active')
        core_value = CoreValue.objects.create(name='Maka-Diyos (Love for God)')
        behavior_indicator = BehaviorIndicator.objects.create(name='Unknown category behavior value', core_value=core_value)
        rating = BehavioralRating.objects.create(code='AO', label='Always Observed')
        BehavioralAssessment.objects.create(
            enrollment=enrollment,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            core_value=core_value,
            behavior_indicator=behavior_indicator,
            rating=rating,
        )
        subject = Subject.objects.create(code='MATH_INVALID', name='Mathematics', category='Core', grade_level=self.grade_level)
        AcademicRecord.objects.create(
            enrollment=enrollment,
            subject=subject,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            grade=82,
            final_grade=82,
        )

        with self.assertRaises(FeatureContractError):
            PredictionService().predict_for_student(student.id)

    def test_wrong_feature_order_is_detected_and_cannot_pass_validation(self):
        service = PredictionService()
        feature_frame, feature_values = service.build_feature_vector(self.student_a.id)
        reordered = feature_frame[feature_frame.columns[1:].tolist() + [feature_frame.columns[0]]]

        with self.assertRaises(FeatureContractError):
            service.validate_feature_frame(reordered, feature_values)

    def test_missing_enrollment_raises_controlled_prediction_error(self):
        student = Student.objects.create(first_name='No', last_name='Enrollment', gender='Male', student_status='active')

        with self.assertRaises(FeatureContractError):
            PredictionService().predict_for_student(student.id)

    def test_predict_student_endpoint_creates_prediction_factors_with_details(self):
        self.client.force_authenticate(user=self.superadmin)
        student = Student.objects.create(first_name='Dina', last_name='Dawson', gender='Female', student_status='active')
        enrollment = Enrollment.objects.create(student=student, academic_year=self.academic_year, grade_level=self.grade_level, section=self.section_b, enrollment_status='active')
        self._create_compatible_behavior(enrollment)
        subject = Subject.objects.create(code='SCI', name='Science', category='Core', grade_level=self.grade_level)
        AcademicRecord.objects.create(
            enrollment=enrollment,
            subject=subject,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            grade=55,
            final_grade=55,
        )

        response = self.client.post(f'/api/predictions/predict/{student.id}/')
        self.assertEqual(response.status_code, 200)

        prediction = RiskPrediction.objects.filter(enrollment=enrollment).order_by('-prediction_date').first()
        factors = PredictionFactor.objects.filter(prediction=prediction)
        self.assertGreaterEqual(factors.count(), 1)
        factor = factors.first()
        self.assertTrue(factor.feature_name)
        self.assertTrue(factor.feature_value)
        self.assertIsNotNone(factor.contribution)
        self.assertTrue(factor.explanation_text)

    def test_historical_prediction_factors_do_not_change_after_later_student_updates(self):
        self.client.force_authenticate(user=self.superadmin)
        student = Student.objects.create(first_name='Emma', last_name='Edwards', gender='Female', student_status='active')
        enrollment = Enrollment.objects.create(student=student, academic_year=self.academic_year, grade_level=self.grade_level, section=self.section_b, enrollment_status='active')
        self._create_compatible_behavior(enrollment)
        subject = Subject.objects.create(code='ENG', name='English', category='Core', grade_level=self.grade_level)
        record = AcademicRecord.objects.create(
            enrollment=enrollment,
            subject=subject,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            grade=70,
            final_grade=70,
        )

        response = self.client.post(f'/api/predictions/predict/{student.id}/')
        self.assertEqual(response.status_code, 200)

        prediction = RiskPrediction.objects.filter(enrollment=enrollment).order_by('-prediction_date').first()
        factor_snapshot = list(PredictionFactor.objects.filter(prediction=prediction).values('feature_name', 'feature_value', 'contribution', 'direction', 'explanation_text'))

        record.grade = 85
        record.final_grade = 85
        record.save()

        refreshed_factors = list(PredictionFactor.objects.filter(prediction=prediction).values('feature_name', 'feature_value', 'contribution', 'direction', 'explanation_text'))
        self.assertEqual(factor_snapshot, refreshed_factors)

    def test_current_subject_and_section_aliases_map_to_model_contract(self):
        student = Student.objects.create(first_name='Edizon', last_name='Alias', gender='Male', student_status='active')
        section = Section.objects.create(name='Onyx', grade_level=self.grade_level, academic_year=self.academic_year)
        enrollment = Enrollment.objects.create(student=student, academic_year=self.academic_year, grade_level=self.grade_level, section=section, enrollment_status='active')
        self._create_compatible_behavior(enrollment)

        aliases = [
            ('English - Writing', 'english_grade'),
            ('English - Reading', 'english_grade'),
            ('English - Language', 'english_grade'),
            ('Computer', 'education_grade'),
            ('Nihongo', 'education_grade'),
            ('Values Education', 'esp_grade'),
            ('EPP / HELE', 'tle_grade'),
            ('MAPE', 'mapeh_grade'),
            ('HeKaSi', 'araling_panlipunan_grade'),
        ]
        for subject_name, feature_key in aliases:
            subject = Subject.objects.create(code=f'ALIAS_{subject_name[:12].upper()}', name=subject_name, category='Learning Area', grade_level=self.grade_level)
            AcademicRecord.objects.create(
                enrollment=enrollment,
                subject=subject,
                academic_year=self.academic_year,
                grading_period_type='Quarter',
                quarter=1,
                grade=99,
                final_grade=99,
            )

        frame, feature_values = PredictionService().build_feature_vector(student.id)

        self.assertEqual(feature_values['section'], 'Moonstone')
        self.assertEqual(feature_values['english_grade'], 99.0)
        self.assertEqual(feature_values['education_grade'], 99.0)
        self.assertEqual(feature_values['esp_grade'], 99.0)
        self.assertEqual(feature_values['tle_grade'], 99.0)
        self.assertEqual(feature_values['mapeh_grade'], 99.0)
        self.assertEqual(feature_values['araling_panlipunan_grade'], 99.0)
        self.assertFalse(any('not represented in the current model vocabulary' in diagnostic for diagnostic in feature_values['contract_diagnostics']))
        self.assertEqual(frame.iloc[0]['section_Moonstone'], 1.0)

    def test_legacy_behavior_values_are_mapped_to_current_canonical_values(self):
        student = Student.objects.create(first_name='Legacy', last_name='Behavior', gender='Female', student_status='active')
        section = Section.objects.create(name='Legacy-A', grade_level=self.grade_level, academic_year=self.academic_year)
        enrollment = Enrollment.objects.create(student=student, academic_year=self.academic_year, grade_level=self.grade_level, section=section, enrollment_status='active')

        core_value = CoreValue.objects.create(name='Respect')
        indicator = BehaviorIndicator.objects.create(name='Respectful Behavior', core_value=core_value)
        rating = BehavioralRating.objects.create(code='NO', label='Not Observed')
        BehavioralAssessment.objects.create(
            enrollment=enrollment,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            core_value=core_value,
            behavior_indicator=indicator,
            rating=rating,
        )

        subject = Subject.objects.create(code='LEGACY_MATH', name='Mathematics', category='Learning Area', grade_level=self.grade_level)
        AcademicRecord.objects.create(
            enrollment=enrollment,
            subject=subject,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            grade=85,
            final_grade=85,
        )

        frame, feature_values = PredictionService().build_feature_vector(student.id)

        self.assertEqual(feature_values['behavior_core_value'], 'Makatao (Love for Fellowmen)')
        self.assertEqual(feature_values['behavior_indicator'], 'Demonstrate contributions toward solidarity')
        self.assertEqual(frame.iloc[0]['behavior_core_value_Makatao (Love for Fellowmen)'], 1.0)
        self.assertEqual(frame.iloc[0]['behavior_indicator_Demonstrate contributions toward solidarity'], 1.0)

    def _create_compatible_behavior(self, enrollment, code='AO'):
        core_value = CoreValue.objects.get_or_create(name='Maka-Diyos (Love for God)')[0]
        indicator = BehaviorIndicator.objects.get_or_create(
            name="Shows adherence to ethical principles by upholding truth",
            core_value=core_value,
        )[0]
        rating = BehavioralRating.objects.get_or_create(code=code, defaults={'label': code})[0]
        BehavioralAssessment.objects.create(
            enrollment=enrollment,
            academic_year=self.academic_year,
            grading_period_type='Quarter',
            quarter=1,
            core_value=core_value,
            behavior_indicator=indicator,
            rating=rating,
        )

    def service_model_feature_count(self):
        return PredictionService().model.n_features_in_
