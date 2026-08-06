import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_sqlite')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import UserProfile
from academics.models import AcademicYear, GradeLevel, Section, Enrollment, Subject, AcademicRecord
from attendance.models import AttendanceRecord
from behavior.models import CoreValue, BehaviorIndicator, BehavioralAssessment, BehavioralRating
from interventions.models import Intervention
from students.models import Student

User = get_user_model()
user, _ = User.objects.get_or_create(username='demo_admin', defaults={'email': 'demo_admin@example.com', 'is_active': True})
user.set_password('DemoAdmin123!')
user.save()
UserProfile.objects.get_or_create(user=user, defaults={'role_name': 'SUPER_ADMIN'})

academic_year, _ = AcademicYear.objects.get_or_create(
    name='2025-2026',
    defaults={'start_date': '2025-08-01', 'end_date': '2026-05-31', 'is_active': True},
)
grade_level, _ = GradeLevel.objects.get_or_create(
    code='G9',
    defaults={'name': 'Grade 9', 'school_level': 'Junior High School', 'order': 9, 'is_active': True},
)
section, _ = Section.objects.get_or_create(
    name='9A',
    grade_level=grade_level,
    academic_year=academic_year,
    defaults={'is_active': True},
)
student, _ = Student.objects.get_or_create(
    lrn='999900000002',
    defaults={
        'first_name': 'Test',
        'middle_name': 'B.',
        'last_name': 'Student Two',
        'gender': 'Male',
        'birth_date': '2010-02-15',
        'student_status': 'active',
    },
)
enrollment, _ = Enrollment.objects.get_or_create(
    student=student,
    academic_year=academic_year,
    defaults={
        'grade_level': grade_level,
        'section': section,
        'enrollment_status': 'active',
        'enrollment_date': '2025-08-10',
    },
)
subject, _ = Subject.objects.get_or_create(
    code='MATH9',
    defaults={
        'name': 'Mathematics 9',
        'category': 'Learning Area',
        'grade_level': grade_level,
        'is_active': True,
    },
)
AcademicRecord.objects.get_or_create(
    enrollment=enrollment,
    subject=subject,
    academic_year=academic_year,
    grading_period_type='Quarter',
    quarter=1,
    defaults={'grade': 65, 'final_grade': 65},
)
AttendanceRecord.objects.get_or_create(
    enrollment=enrollment,
    month='August 2025',
    defaults={'days_present': 20, 'absences': 2, 'times_tardy': 1, 'school_days': 22},
)
core_value, _ = CoreValue.objects.get_or_create(
    name='Respect',
    defaults={'description': 'Shows respect to teachers and peers.', 'is_active': True},
)
behavior_indicator, _ = BehaviorIndicator.objects.get_or_create(
    core_value=core_value,
    name='Shows respect to teachers and peers',
    defaults={'description': 'Respect indicator', 'is_active': True},
)
rating, _ = BehavioralRating.objects.get_or_create(
    code='AO',
    defaults={'label': 'Approaching Outstanding', 'numeric_value': 4.0, 'description': 'Approaching Outstanding', 'is_active': True},
)
BehavioralAssessment.objects.get_or_create(
    enrollment=enrollment,
    academic_year=academic_year,
    grading_period_type='Quarter',
    quarter=1,
    core_value=core_value,
    behavior_indicator=behavior_indicator,
    defaults={'rating': rating, 'assessment_date': '2025-08-15'},
)
Intervention.objects.get_or_create(
    enrollment=enrollment,
    intervention_type='Academic Monitoring',
    defaults={'status': 'in_progress', 'priority': 'medium', 'start_date': '2025-08-15', 'end_date': '2025-09-15'},
)
print('seeded student id', student.id)
