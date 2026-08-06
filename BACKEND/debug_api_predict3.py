import os
import traceback
from uuid import uuid4

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django

django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from accounts.models import UserProfile
from academics.models import AcademicYear, GradeLevel, Section, Enrollment, Subject, AcademicRecord
from students.models import Student

User = get_user_model()
client = APIClient()
client.defaults['HTTP_HOST'] = 'testserver'

suffix = uuid4().hex[:8]
username = f'debug_superadmin_{suffix}'
user = User.objects.create_user(username=username, password='DebugPass1!')
UserProfile.objects.create(user=user, role_name='SUPER_ADMIN')

academic_year = AcademicYear.objects.create(name=f'2025-2026-{suffix}', start_date='2025-06-01', end_date='2026-03-31', is_active=True)
grade_level = GradeLevel.objects.create(name=f'Grade 11 {suffix}', code=f'G11-{suffix}', school_level='Senior High School', order=11)
section = Section.objects.create(name=f'A-{suffix}', grade_level=grade_level, academic_year=academic_year)
student = Student.objects.create(first_name='Alice', last_name='Test', gender='Female', student_status='active')
enrollment = Enrollment.objects.create(student=student, academic_year=academic_year, grade_level=grade_level, section=section, enrollment_status='active')
subject = Subject.objects.create(code=f'MATH-{suffix}', name='Mathematics', category='Core', grade_level=grade_level)
AcademicRecord.objects.create(enrollment=enrollment, subject=subject, academic_year=academic_year, grading_period_type='Quarter', quarter=1, grade=65, final_grade=65)

client.force_authenticate(user=user)
response = client.post(f'/api/predictions/predict/{student.id}/')
print('status', response.status_code)
try:
    print('json', response.json())
except Exception as exc:
    print('json error', exc)
print('content', response.content.decode('utf-8', errors='replace'))

if response.status_code != 200:
    import sys
    sys.exit(1)
