from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserProfile
from academics.models import AcademicYear, GradeLevel, Section, Enrollment, Subject, AcademicRecord
from audit.models import AuditLog
from predictions.models import RiskPrediction, PredictionFactor
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
        self.grade_level = GradeLevel.objects.create(name='Grade 11', code='G11', school_level='Senior High School', order=11)
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

    def test_predict_student_endpoint_creates_prediction(self):
        self.client.force_authenticate(user=self.superadmin)
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

    def test_predict_student_endpoint_creates_audit_log(self):
        self.client.force_authenticate(user=self.superadmin)
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

    def test_predict_student_endpoint_creates_prediction_factors_with_details(self):
        self.client.force_authenticate(user=self.superadmin)
        student = Student.objects.create(first_name='Dina', last_name='Dawson', gender='Female', student_status='active')
        enrollment = Enrollment.objects.create(student=student, academic_year=self.academic_year, grade_level=self.grade_level, section=self.section_b, enrollment_status='active')
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
