from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from academics.models import AcademicYear, AcademicRecord, GradeLevel, Section, TeacherAssignment, Enrollment, Subject
from accounts.models import UserProfile
from attendance.models import AttendanceRecord
from behavior.models import BehavioralAssessment, BehaviorIndicator, BehavioralRating, CoreValue
from common.authorization import get_adviser_sections, get_adviser_students
from interventions.models import Intervention
from predictions.models import RiskPrediction
from students.models import Student


class AdviserStudentAuthorizationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()

        self.admin = self.user_model.objects.create_user(username='adviser_admin', password='AdminPass1!')
        UserProfile.objects.create(user=self.admin, role_name='SCHOOL_ADMIN')

        self.adviser_a = self.user_model.objects.create_user(username='adviser_a', password='TeacherPass1!')
        UserProfile.objects.create(user=self.adviser_a, role_name='TEACHER')

        self.adviser_b = self.user_model.objects.create_user(username='adviser_b', password='TeacherPass1!')
        UserProfile.objects.create(user=self.adviser_b, role_name='TEACHER')

        self.subject_teacher = self.user_model.objects.create_user(username='subject_teacher', password='TeacherPass1!')
        UserProfile.objects.create(user=self.subject_teacher, role_name='TEACHER')

        self.guidance = self.user_model.objects.create_user(username='guidance_user', password='GuidancePass1!')
        UserProfile.objects.create(user=self.guidance, role_name='GUIDANCE')

        self.registrar = self.user_model.objects.create_user(username='registrar_user', password='RegistrarPass1!')
        UserProfile.objects.create(user=self.registrar, role_name='REGISTRAR')

        self.year = AcademicYear.objects.create(name='2027-2028', start_date='2027-06-01', end_date='2028-03-31', is_active=True)
        self.grade = GradeLevel.objects.get(code='G7')

        self.section_a = Section.objects.create(name='A', grade_level=self.grade, academic_year=self.year, adviser=self.adviser_a)
        self.section_b = Section.objects.create(name='B', grade_level=self.grade, academic_year=self.year, adviser=self.adviser_b)
        self.section_c = Section.objects.create(name='C', grade_level=self.grade, academic_year=self.year)
        self.archived_section = Section.objects.create(name='Archived', grade_level=self.grade, academic_year=self.year, adviser=self.adviser_a, is_active=False)

        self.student_a = Student.objects.create(first_name='Ava', last_name='Adviser', student_status='active')
        self.student_b = Student.objects.create(first_name='Ben', last_name='Other', student_status='active')
        self.student_c = Student.objects.create(first_name='Cara', last_name='Unassigned', student_status='active')
        self.student_d = Student.objects.create(first_name='Drew', last_name='Archived', student_status='active')

        Enrollment.objects.create(student=self.student_a, academic_year=self.year, grade_level=self.grade, section=self.section_a, enrollment_status='active')
        Enrollment.objects.create(student=self.student_b, academic_year=self.year, grade_level=self.grade, section=self.section_b, enrollment_status='active')
        Enrollment.objects.create(student=self.student_c, academic_year=self.year, grade_level=self.grade, section=self.section_c, enrollment_status='active')
        Enrollment.objects.create(student=self.student_d, academic_year=self.year, grade_level=self.grade, section=self.archived_section, enrollment_status='active')

        TeacherAssignment.objects.create(
            teacher=self.adviser_a,
            academic_year=self.year,
            grade_level=self.grade,
            section=self.section_a,
            assignment_type='ADVISER',
            is_active=True,
        )
        TeacherAssignment.objects.create(
            teacher=self.adviser_b,
            academic_year=self.year,
            grade_level=self.grade,
            section=self.section_b,
            assignment_type='ADVISER',
            is_active=True,
        )

        self.math = Subject.objects.create(code='ADV-MATH', name='Mathematics', category='Learning Area', grade_level=self.grade)
        TeacherAssignment.objects.create(
            teacher=self.subject_teacher,
            academic_year=self.year,
            grade_level=self.grade,
            section=self.section_c,
            subject=self.math,
            assignment_type='SUBJECT',
            is_active=True,
        )

    def test_get_adviser_sections_and_students_are_scoped(self):
        adviser_sections = get_adviser_sections(self.adviser_a)
        adviser_students = get_adviser_students(self.adviser_a, Student.objects.all())

        self.assertEqual(list(adviser_sections.values_list('id', flat=True)), [self.section_a.id])
        self.assertNotIn(self.student_b.id, adviser_students.values_list('id', flat=True))
        self.assertNotIn(self.student_d.id, adviser_students.values_list('id', flat=True))

    def test_adviser_can_access_own_student(self):
        self.client.force_authenticate(user=self.adviser_a)
        response = self.client.get(f'/api/students/{self.student_a.id}/')
        self.assertEqual(response.status_code, 200)

    def test_adviser_academic_records_support_quarter_and_semester_filters(self):
        enrollment = self.student_a.enrollments.get()
        quarter_record = AcademicRecord.objects.create(
            enrollment=enrollment,
            subject=self.math,
            academic_year=self.year,
            grading_period_type='Quarter',
            quarter=1,
            grade=81,
            final_grade=81,
            encoded_by=self.adviser_a,
        )
        semester_record = AcademicRecord.objects.create(
            enrollment=enrollment,
            subject=self.math,
            academic_year=self.year,
            grading_period_type='Semester',
            semester=1,
            grade=86,
            final_grade=86,
            encoded_by=self.adviser_a,
        )

        self.client.force_authenticate(user=self.adviser_a)
        all_records = self.client.get('/api/academic-records/', {'enrollment': enrollment.id}).data['results']
        quarter_records = self.client.get('/api/academic-records/', {'enrollment': enrollment.id, 'grading_period_type': 'Quarter'}).data['results']
        semester_records = self.client.get('/api/academic-records/', {'enrollment': enrollment.id, 'grading_period_type': 'Semester'}).data['results']

        self.assertEqual({item['id'] for item in all_records}, {quarter_record.id, semester_record.id})
        self.assertEqual([item['id'] for item in quarter_records], [quarter_record.id])
        self.assertEqual([item['id'] for item in semester_records], [semester_record.id])
        self.assertEqual(quarter_records[0]['encoded_by_name'], 'adviser_a')

    def test_adviser_cannot_access_other_advisers_student(self):
        self.client.force_authenticate(user=self.adviser_a)
        response = self.client.get(f'/api/students/{self.student_b.id}/')
        self.assertIn(response.status_code, {403, 404})

    def test_adviser_cannot_access_unassigned_student(self):
        self.client.force_authenticate(user=self.adviser_a)
        response = self.client.get(f'/api/students/{self.student_c.id}/')
        self.assertIn(response.status_code, {403, 404})

    def test_adviser_cannot_bypass_student_scope_through_related_endpoints(self):
        enrollment = self.student_b.enrollments.get()
        academic_record = AcademicRecord.objects.create(
            enrollment=enrollment,
            subject=self.math,
            academic_year=self.year,
            grading_period_type='Quarter',
            quarter=1,
            grade=80,
            final_grade=80,
        )
        attendance_record = AttendanceRecord.objects.create(
            enrollment=enrollment,
            month='June',
            school_days=20,
            days_present=19,
            absences=1,
            times_tardy=0,
        )
        core_value = CoreValue.objects.create(name='Maka-Diyos')
        indicator = BehaviorIndicator.objects.create(name='Shows respect', core_value=core_value)
        rating = BehavioralRating.objects.create(code='AO', label='Always Observed')
        behavior_record = BehavioralAssessment.objects.create(
            enrollment=enrollment,
            academic_year=self.year,
            grading_period_type='Quarter',
            quarter=1,
            core_value=core_value,
            behavior_indicator=indicator,
            rating=rating,
            numeric_score=5,
        )
        intervention = Intervention.objects.create(enrollment=enrollment, intervention_type='Tutoring')
        prediction = RiskPrediction.objects.create(
            enrollment=enrollment,
            prediction_type='Academic Risk',
            risk_level='Moderate',
            probability='0.5000',
        )
        factor = prediction.prediction_factors.create(feature_name='attendance', feature_value='95%')

        self.client.force_authenticate(user=self.adviser_a)
        endpoints = [
            ('academic-records', academic_record.id),
            ('attendance-records', attendance_record.id),
            ('behavioral-assessments', behavior_record.id),
            ('enrollments', enrollment.id),
            ('interventions', intervention.id),
            ('risk-predictions', prediction.id),
            ('prediction-factors', factor.id),
        ]

        for endpoint, record_id in endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(f'/api/{endpoint}/{record_id}/')
                self.assertIn(response.status_code, {403, 404})

    def test_subject_teacher_cannot_access_adviser_only_student(self):
        self.client.force_authenticate(user=self.subject_teacher)
        response = self.client.get(f'/api/students/{self.student_a.id}/')
        self.assertIn(response.status_code, {403, 404})

    def test_admin_guidance_and_registrar_access_remains_valid(self):
        for user in (self.admin, self.guidance, self.registrar):
            self.client.force_authenticate(user=user)
            response = self.client.get(f'/api/students/{self.student_a.id}/')
            self.assertEqual(response.status_code, 200)

    def test_multiple_advisory_sections_are_included(self):
        self.section_b.adviser = self.adviser_a
        self.section_b.save(update_fields=['adviser'])
        self.adviser_a.profile.assigned_sections.add(self.section_b)

        adviser_sections = get_adviser_sections(self.adviser_a)
        adviser_students = get_adviser_students(self.adviser_a, Student.objects.all())
        self.assertEqual(set(adviser_sections.values_list('id', flat=True)), {self.section_a.id, self.section_b.id})
        self.assertIn(self.student_b.id, adviser_students.values_list('id', flat=True))

    def test_archived_section_students_are_not_exposed(self):
        adviser_students = get_adviser_students(self.adviser_a, Student.objects.all())
        self.assertNotIn(self.student_d.id, adviser_students.values_list('id', flat=True))

    def test_adviser_assignments_remain_separate_from_subject_assignments(self):
        self.client.force_authenticate(user=self.adviser_a)
        response = self.client.get('/api/teacher-assignments/my-context/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['section_name'] for item in response.data['advisory_classes']], ['A'])
        self.assertEqual(response.data['subject_assignments'], [])

    def test_adviser_dashboard_returns_only_authorized_students(self):
        self.client.force_authenticate(user=self.adviser_a)
        response = self.client.get('/api/adviser-dashboard/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['total_students'], 1)
        self.assertEqual([item['name'] for item in response.data['sections']], ['A'])
        returned_ids = {item['id'] for item in response.data['students_requiring_attention']}
        self.assertNotIn(self.student_b.id, returned_ids)
        self.assertNotIn(self.student_c.id, returned_ids)
        self.assertNotIn(self.student_d.id, returned_ids)

    def test_subject_only_teacher_cannot_access_adviser_dashboard(self):
        self.client.force_authenticate(user=self.subject_teacher)
        response = self.client.get('/api/adviser-dashboard/')
        self.assertEqual(response.status_code, 403)

    def test_teacher_without_advisory_section_receives_empty_dashboard(self):
        teacher = self.user_model.objects.create_user(username='unassigned_teacher', password='TeacherPass1!')
        UserProfile.objects.create(user=teacher, role_name='TEACHER')
        self.client.force_authenticate(user=teacher)
        response = self.client.get('/api/adviser-dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary']['total_students'], 0)
        self.assertEqual(response.data['students_requiring_attention'], [])

    def test_dashboard_represents_existing_prediction_intervention_and_attendance_data(self):
        enrollment = self.student_a.enrollments.get()
        AcademicRecord.objects.create(
            enrollment=enrollment,
            subject=self.math,
            academic_year=self.year,
            grading_period_type='Quarter',
            quarter=1,
            grade=72,
            final_grade=72,
        )
        AttendanceRecord.objects.create(
            enrollment=enrollment,
            month='June',
            school_days=20,
            days_present=18,
            absences=2,
            times_tardy=1,
        )
        Intervention.objects.create(
            enrollment=enrollment,
            intervention_type='Tutoring',
            status='in_progress',
            end_date='2026-06-15',
        )
        RiskPrediction.objects.create(
            enrollment=enrollment,
            prediction_type='Academic Risk',
            risk_level='High',
            probability='0.8500',
        )

        self.client.force_authenticate(user=self.adviser_a)
        response = self.client.get('/api/adviser-dashboard/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['risk_distribution'], {'High': 1})
        self.assertEqual(response.data['summary']['active_interventions'], 1)
        self.assertEqual(response.data['summary']['follow_up_required'], 1)
        student = response.data['students_requiring_attention'][0]
        self.assertEqual(student['general_average'], 72.0)
        self.assertEqual(student['attendance_percentage'], 90.0)
        self.assertEqual(student['intervention_statuses'], ['in_progress'])
        self.assertTrue(student['follow_up'])

        profile_response = self.client.get(f'/api/academic-records/', {'enrollment': enrollment.id})
        self.assertEqual(profile_response.status_code, 200)
        profile_records = profile_response.data.get('results', profile_response.data)
        self.assertEqual(profile_records[0]['final_grade'], '72.00')

    def test_advisory_roster_supports_authorized_section_and_search_filters(self):
        self.section_b.adviser = self.adviser_a
        self.section_b.save(update_fields=['adviser'])

        self.client.force_authenticate(user=self.adviser_a)
        section_response = self.client.get('/api/adviser-dashboard/', {'section': self.section_b.id})
        self.assertEqual(section_response.status_code, 200)
        self.assertEqual([student['id'] for student in section_response.data['students']], [self.student_b.id])

        search_response = self.client.get('/api/adviser-dashboard/', {'search': 'Ava'})
        self.assertEqual(search_response.status_code, 200)
        self.assertEqual([student['id'] for student in search_response.data['students']], [self.student_a.id])
        self.assertNotIn(self.student_b.id, [student['id'] for student in search_response.data['students']])

    def test_advisory_roster_rejects_unassigned_section(self):
        self.client.force_authenticate(user=self.adviser_a)
        response = self.client.get('/api/adviser-dashboard/', {'section': self.section_b.id})
        self.assertEqual(response.status_code, 404)
        self.assertNotIn('students', response.data)
