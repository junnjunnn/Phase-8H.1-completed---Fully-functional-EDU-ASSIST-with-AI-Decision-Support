from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import UserProfile
from academics.models import AcademicYear, GradeLevel, Section, Strand, Subject, Enrollment, AcademicRecord
from attendance.models import AttendanceRecord
from behavior.models import CoreValue, BehaviorIndicator, BehavioralRating, BehavioralAssessment
from interventions.models import Intervention
from predictions.models import RiskPrediction, PredictionFactor
from students.models import Student


class Command(BaseCommand):
    help = 'Seed a safe demo student and related records for local development. Only runs when DEBUG=True.'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('seed_demo_data may only be run when DEBUG=True.')

        with transaction.atomic():
            self.stdout.write('Seeding demo development data...')

            User = get_user_model()
            teacher_username = 'demo_teacher'
            admin_username = 'demo_admin'

            demo_teacher, created = User.objects.get_or_create(
                username=teacher_username,
                defaults={
                    'email': 'demo_teacher@example.com',
                    'is_active': True,
                },
            )
            if created:
                demo_teacher.set_password('DemoTeacher123!')
                demo_teacher.save()
                self.stdout.write(f'  Created user: {teacher_username}')
            else:
                self.stdout.write(f'  Reusing existing user: {teacher_username}')

            demo_admin, admin_created = User.objects.get_or_create(
                username=admin_username,
                defaults={
                    'email': 'demo_admin@example.com',
                    'is_active': True,
                },
            )
            if admin_created:
                demo_admin.set_password('DemoAdmin123!')
                demo_admin.save()
                self.stdout.write(f'  Created user: {admin_username}')
            else:
                self.stdout.write(f'  Reusing existing user: {admin_username}')

            teacher_profile, _ = UserProfile.objects.get_or_create(
                user=demo_teacher,
                defaults={'role_name': 'TEACHER'},
            )
            if teacher_profile.role_name != 'TEACHER':
                teacher_profile.role_name = 'TEACHER'
                teacher_profile.save(update_fields=['role_name'])

            admin_profile, _ = UserProfile.objects.get_or_create(
                user=demo_admin,
                defaults={'role_name': 'SUPER_ADMIN'},
            )
            if admin_profile.role_name != 'SUPER_ADMIN':
                admin_profile.role_name = 'SUPER_ADMIN'
                admin_profile.save(update_fields=['role_name'])

            current_year, _ = AcademicYear.objects.get_or_create(
                name='2025-2026',
                defaults={
                    'start_date': '2025-08-01',
                    'end_date': '2026-05-31',
                    'is_active': True,
                },
            )
            if not current_year.is_active:
                current_year.is_active = True
                current_year.save(update_fields=['is_active'])

            grade_level, _ = GradeLevel.objects.get_or_create(
                code='G9',
                defaults={
                    'name': 'Grade 9',
                    'school_level': 'Junior High School',
                    'order': 9,
                    'is_active': True,
                },
            )

            section_a, _ = Section.objects.get_or_create(
                grade_level=grade_level,
                academic_year=current_year,
                name='9A',
                defaults={'adviser': demo_teacher, 'is_active': True},
            )
            section_b, _ = Section.objects.get_or_create(
                grade_level=grade_level,
                academic_year=current_year,
                name='9B',
                defaults={'adviser': None, 'is_active': True},
            )

            if section_a.adviser_id != demo_teacher.id:
                section_a.adviser = demo_teacher
                section_a.save(update_fields=['adviser'])

            if not teacher_profile.assigned_sections.filter(pk=section_a.pk).exists():
                teacher_profile.assigned_sections.add(section_a)

            strand, _ = Strand.objects.get_or_create(
                code='G9CORE',
                defaults={
                    'name': 'Grade 9 Core',
                    'description': 'Development test strand for Grade 9.',
                    'is_active': True,
                },
            )

            subject_data = [
                {'code': 'ENG9', 'name': 'English 9', 'category': 'Learning Area'},
                {'code': 'MATH9', 'name': 'Mathematics 9', 'category': 'Learning Area'},
                {'code': 'SCI9', 'name': 'Science 9', 'category': 'Learning Area'},
            ]
            subjects = []
            for item in subject_data:
                subject, _ = Subject.objects.get_or_create(
                    code=item['code'],
                    defaults={
                        'name': item['name'],
                        'category': item['category'],
                        'grade_level': grade_level,
                        'strand': strand,
                        'is_active': True,
                    },
                )
                subjects.append(subject)

            students_info = [
                {'lrn': '999900000001', 'first_name': 'Test', 'middle_name': 'A.', 'last_name': 'Student One', 'gender': 'Female', 'birth_date': '2010-01-15', 'student_status': 'active'},
                {'lrn': '999900000002', 'first_name': 'Test', 'middle_name': 'B.', 'last_name': 'Student Two', 'gender': 'Male', 'birth_date': '2010-02-15', 'student_status': 'active'},
                {'lrn': '999900000003', 'first_name': 'Test', 'middle_name': 'C.', 'last_name': 'Student Three', 'gender': 'Female', 'birth_date': '2010-03-15', 'student_status': 'active'},
                {'lrn': '999900000004', 'first_name': 'Test', 'middle_name': 'D.', 'last_name': 'Student Four', 'gender': 'Male', 'birth_date': '2010-04-15', 'student_status': 'active'},
                {'lrn': '999900000005', 'first_name': 'Test', 'middle_name': 'E.', 'last_name': 'Student Empty', 'gender': 'Female', 'birth_date': '2010-05-15', 'student_status': 'active'},
                {'lrn': '999900000006', 'first_name': 'Test', 'middle_name': 'F.', 'last_name': 'Student Other', 'gender': 'Male', 'birth_date': '2010-06-15', 'student_status': 'active'},
            ]
            students = []
            for info in students_info:
                student, _ = Student.objects.get_or_create(
                    lrn=info['lrn'],
                    defaults={
                        'first_name': info['first_name'],
                        'middle_name': info['middle_name'],
                        'last_name': info['last_name'],
                        'gender': info['gender'],
                        'birth_date': info['birth_date'],
                        'student_status': info['student_status'],
                    },
                )
                students.append(student)

            demo_student_lrns = [info['lrn'] for info in students_info]
            PredictionFactor.objects.filter(
                prediction__enrollment__student__lrn__in=demo_student_lrns,
                feature_name='Behavior Rating',
            ).delete()
            BehavioralRating.objects.filter(code='A').delete()

            enrollment_map = {
                '999900000001': section_a,
                '999900000002': section_a,
                '999900000003': section_a,
                '999900000004': section_a,
                '999900000005': section_a,
                '999900000006': section_b,
            }
            enrollments = {}
            for student in students:
                section = enrollment_map[student.lrn]
                enrollment, _ = Enrollment.objects.get_or_create(
                    student=student,
                    academic_year=current_year,
                    defaults={
                        'grade_level': grade_level,
                        'section': section,
                        'strand': strand,
                        'enrollment_status': 'active',
                        'enrollment_date': '2025-08-10',
                    },
                )
                if enrollment.grade_level_id != grade_level.id or enrollment.section_id != section.id or enrollment.strand_id != strand.id:
                    enrollment.grade_level = grade_level
                    enrollment.section = section
                    enrollment.strand = strand
                    enrollment.save(update_fields=['grade_level', 'section', 'strand'])
                enrollments[student.lrn] = enrollment

            demo_student_lrns = [info['lrn'] for info in students_info]
            BehavioralAssessment.objects.filter(enrollment__student__lrn__in=demo_student_lrns).delete()
            PredictionFactor.objects.filter(prediction__enrollment__student__lrn__in=demo_student_lrns).delete()
            RiskPrediction.objects.filter(enrollment__student__lrn__in=demo_student_lrns).delete()

            discipline, _ = CoreValue.objects.get_or_create(
                name='Discipline',
                defaults={'description': 'Demonstrates consistency with school rules and policies.', 'is_active': True},
            )
            respect, _ = CoreValue.objects.get_or_create(
                name='Respect',
                defaults={'description': 'Demonstrates respect toward teachers and peers.', 'is_active': True},
            )

            compliance_indicator, _ = BehaviorIndicator.objects.get_or_create(
                core_value=discipline,
                name='Compliance with school rules',
                defaults={'description': 'Observation of compliance with school policies and classroom expectations.', 'is_active': True},
            )
            respectful_indicator, _ = BehaviorIndicator.objects.get_or_create(
                core_value=respect,
                name='Respectful Behavior',
                defaults={'description': 'Observation of respectful interactions with adults and peers.', 'is_active': True},
            )

            rating_codes = [
                {'code': 'AO', 'label': 'Always Observe', 'description': 'Teacher observed this behavior consistently.'},
                {'code': 'SO', 'label': 'Sometimes Observe', 'description': 'Teacher observed this behavior occasionally.'},
                {'code': 'RO', 'label': 'Rarely Observe', 'description': 'Teacher observed this behavior rarely.'},
                {'code': 'NO', 'label': 'Not Observe', 'description': 'Teacher did not observe this behavior during the period.'},
            ]
            ratings = {}
            for rating_info in rating_codes:
                rating, created = BehavioralRating.objects.get_or_create(
                    code=rating_info['code'],
                    defaults={
                        'label': rating_info['label'],
                        'description': rating_info['description'],
                        'is_active': True,
                        'numeric_value': 0.0,
                    },
                )
                if not created and (rating.label != rating_info['label'] or rating.description != rating_info['description'] or not rating.is_active):
                    rating.label = rating_info['label']
                    rating.description = rating_info['description']
                    rating.is_active = True
                    rating.save(update_fields=['label', 'description', 'is_active'])
                ratings[rating.code] = rating

            academic_records_data = [
                {'student_lrn': '999900000001', 'grades': [92.00, 89.00, 91.00]},
                {'student_lrn': '999900000002', 'grades': [85.00, 87.00, 88.00]},
                {'student_lrn': '999900000003', 'grades': [78.00, 82.00, 80.00]},
                {'student_lrn': '999900000006', 'grades': [81.00, 83.00, 79.00]},
            ]
            academic_count = 0
            for record_data in academic_records_data:
                enrollment = enrollments[record_data['student_lrn']]
                for subject, grade in zip(subjects, record_data['grades']):
                    academic_record, created = AcademicRecord.objects.get_or_create(
                        enrollment=enrollment,
                        subject=subject,
                        academic_year=current_year,
                        grading_period_type='Quarter',
                        quarter=1,
                        defaults={
                            'grade': grade,
                            'final_grade': grade,
                            'remarks': 'Development test academic record.',
                            'encoded_by': demo_teacher,
                        },
                    )
                    if created:
                        academic_count += 1

            attendance_data = [
                {'student_lrn': '999900000001', 'days_present': 19, 'absences': 1, 'tardy': 0},
                {'student_lrn': '999900000002', 'days_present': 18, 'absences': 2, 'tardy': 1},
                {'student_lrn': '999900000003', 'days_present': 16, 'absences': 4, 'tardy': 2},
                {'student_lrn': '999900000006', 'days_present': 20, 'absences': 0, 'tardy': 0},
            ]
            attendance_count = 0
            for attendance_info in attendance_data:
                enrollment = enrollments[attendance_info['student_lrn']]
                attendance_record, created = AttendanceRecord.objects.get_or_create(
                    enrollment=enrollment,
                    month='June',
                    defaults={
                        'school_days': 20,
                        'days_present': attendance_info['days_present'],
                        'absences': attendance_info['absences'],
                        'times_tardy': attendance_info['tardy'],
                        'encoded_by': demo_teacher,
                    },
                )
                if created:
                    attendance_count += 1

            behavioral_assessments = [
                {
                    'student_lrn': '999900000001',
                    'core_value': discipline,
                    'behavior_indicator': compliance_indicator,
                    'rating': ratings['AO'],
                    'assessment_date': '2025-10-10',
                    'remarks': 'Always follows school rules and classroom expectations.',
                },
                {
                    'student_lrn': '999900000002',
                    'core_value': respect,
                    'behavior_indicator': respectful_indicator,
                    'rating': ratings['SO'],
                    'assessment_date': '2025-10-12',
                    'remarks': 'Sometimes respectful; needs occasional reminders.',
                },
                {
                    'student_lrn': '999900000003',
                    'core_value': discipline,
                    'behavior_indicator': compliance_indicator,
                    'rating': ratings['RO'],
                    'assessment_date': '2025-10-14',
                    'remarks': 'Rarely follows school rules without adult support.',
                },
                {
                    'student_lrn': '999900000004',
                    'core_value': respect,
                    'behavior_indicator': respectful_indicator,
                    'rating': ratings['NO'],
                    'assessment_date': '2025-10-16',
                    'remarks': 'Not observed exhibiting respectful interactions this quarter.',
                },
            ]
            behavior_count = 0
            for behavior_info in behavioral_assessments:
                enrollment = enrollments[behavior_info['student_lrn']]
                assessment, created = BehavioralAssessment.objects.get_or_create(
                    enrollment=enrollment,
                    academic_year=current_year,
                    grading_period_type='Quarter',
                    quarter=1,
                    core_value=behavior_info['core_value'],
                    behavior_indicator=behavior_info['behavior_indicator'],
                    defaults={
                        'rating': behavior_info['rating'],
                        'numeric_score': 0.0,
                        'assessed_by': demo_teacher,
                        'assessment_date': behavior_info['assessment_date'],
                        'remarks': behavior_info['remarks'],
                    },
                )
                if not created:
                    updated = False
                    if assessment.rating_id != behavior_info['rating'].id:
                        assessment.rating = behavior_info['rating']
                        updated = True
                    if assessment.numeric_score is None:
                        assessment.numeric_score = 0.0
                        updated = True
                    if updated:
                        assessment.save(update_fields=['rating', 'numeric_score'])
                if created:
                    behavior_count += 1

            intervention, _ = Intervention.objects.get_or_create(
                enrollment=enrollments['999900000004'],
                intervention_type='Counseling',
                defaults={
                    'risk_type': 'Behavioral Risk',
                    'recommendation': 'Schedule weekly check-ins with guidance counselor.',
                    'assigned_personnel': demo_teacher,
                    'status': 'planned',
                    'priority': 'high',
                    'notes': 'Target support for respectful behavior and classroom interactions.',
                    'start_date': '2025-10-20',
                },
            )
            intervention_count = 1 if intervention else 0

            risk_prediction, _ = RiskPrediction.objects.get_or_create(
                enrollment=enrollments['999900000001'],
                prediction_type='Academic Risk',
                risk_level='Moderate',
                defaults={
                    'probability': 0.62,
                    'model_name': 'DevRiskModel',
                    'model_version': 'v1.0',
                    'explanation': 'Test development prediction record only.',
                    'review_status': 'Pending',
                },
            )
            prediction_count = 1 if risk_prediction else 0

            PredictionFactor.objects.get_or_create(
                prediction=risk_prediction,
                feature_name='Attendance Trend',
                defaults={
                    'feature_value': '95%',
                    'contribution': 0.35,
                    'direction': 'negative',
                    'explanation_text': 'Development test feature only.',
                },
            )
            PredictionFactor.objects.get_or_create(
                prediction=risk_prediction,
                feature_name='Grade Stability',
                defaults={
                    'feature_value': 'B+',
                    'contribution': 0.25,
                    'direction': 'neutral',
                    'explanation_text': 'Development test feature only.',
                },
            )

        self.stdout.write(self.style.SUCCESS('Development seed data seeded successfully.'))
        self.stdout.write('Login with demo_teacher / DemoTeacher123! or demo_admin / DemoAdmin123!')
        self.stdout.write(f'Students created: {len(students)}')
        self.stdout.write(f'Enrollments created: {len(enrollments)}')
        self.stdout.write(f'Academic records added: {academic_count}')
        self.stdout.write(f'Attendance records added: {attendance_count}')
        self.stdout.write(f'Behavioral assessments added: {behavior_count}')
        self.stdout.write(f'Intervention records present: {intervention_count}')
        self.stdout.write(f'Prediction records present: {prediction_count}')
