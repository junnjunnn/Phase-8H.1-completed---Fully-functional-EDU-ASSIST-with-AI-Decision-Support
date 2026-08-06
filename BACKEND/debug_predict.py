import os
import traceback
from uuid import uuid4

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django

django.setup()

from academics.models import AcademicYear, GradeLevel, Section, Enrollment, Subject, AcademicRecord
from students.models import Student
from predictions.services.prediction_service import PredictionService

unique = uuid4().hex[:8]

student = Student.objects.create(
    first_name=f'Test{unique}',
    last_name='Student',
    gender='Female',
    student_status='active',
)

academic_year, _ = AcademicYear.objects.get_or_create(
    name=f'2025-2026-{unique}',
    defaults={'start_date': '2025-06-01', 'end_date': '2026-03-31', 'is_active': True},
)
grade_level, _ = GradeLevel.objects.get_or_create(
    name=f'Grade 11 {unique}',
    code=f'G11-{unique}',
    defaults={'school_level': 'Senior High School', 'order': 11},
)
section, _ = Section.objects.get_or_create(
    name=f'A-{unique}',
    grade_level=grade_level,
    academic_year=academic_year,
)
enrollment, _ = Enrollment.objects.get_or_create(
    student=student,
    academic_year=academic_year,
    defaults={
        'grade_level': grade_level,
        'section': section,
        'enrollment_status': 'active',
    },
)
subject, _ = Subject.objects.get_or_create(
    code=f'MATH-{unique}',
    defaults={'name': 'Mathematics', 'category': 'Core', 'grade_level': grade_level},
)
AcademicRecord.objects.create(
    enrollment=enrollment,
    subject=subject,
    academic_year=academic_year,
    grading_period_type='Quarter',
    quarter=1,
    grade=65,
    final_grade=65,
)

service = PredictionService()
try:
    result = service.predict_for_student(student.id)
    print('result', result)
except Exception:
    traceback.print_exc()
