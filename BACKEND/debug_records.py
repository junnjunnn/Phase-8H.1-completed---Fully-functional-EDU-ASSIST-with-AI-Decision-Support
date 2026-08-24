import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from students.models import Student
from academics.models import Enrollment, AcademicRecord, AcademicYear, GradeLevel, Section, Subject
from accounts.models import UserProfile
from django.contrib.auth import get_user_model

User = get_user_model()

print("=== Finding Test Student in Grade 6 Onyx ===")
try:
    grade_6 = GradeLevel.objects.get(name='Grade 6')
    print(f"Found Grade Level: {grade_6.name} (id={grade_6.id})")
    
    active_ay = AcademicYear.objects.get(is_active=True)
    print(f"Active Academic Year: {active_ay.name} (id={active_ay.id})")
    
    onyx_section = Section.objects.filter(grade_level=grade_6, academic_year=active_ay, name__icontains='Onyx').first()
    if onyx_section:
        print(f"Found Onyx Section: {onyx_section.name} (id={onyx_section.id})")
        enrollments = Enrollment.objects.filter(section=onyx_section, enrollment_status='active')
        print(f"Active enrollments in Onyx: {enrollments.count()}")
        for enrollment in enrollments[:5]:
            print(f"\n  Student: {enrollment.student.first_name} {enrollment.student.last_name} (id={enrollment.student.id})")
            print(f"  Enrollment id: {enrollment.id}")
            records = AcademicRecord.objects.filter(enrollment=enrollment).order_by('subject__name', '-created_at')
            print(f"  Total Academic Records: {records.count()}")
            for record in records:
                period_str = f"Q{record.quarter}" if record.quarter else f"S{record.semester}"
                print(f"    - {record.subject.name:20} / {period_str} / Grade: {record.grade} / Encoded by: {record.encoded_by}")
    else:
        print("Onyx section not found")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n\n=== Looking for Computer Subject / Quarter 1 records ===")
try:
    computer = Subject.objects.filter(name__icontains='Computer').first()
    if computer:
        print(f"Found Subject: {computer.name} (id={computer.id}, code={computer.code})")
        
        q1_records = AcademicRecord.objects.filter(
            subject=computer,
            grading_period_type='Quarter',
            quarter=1
        ).order_by('-created_at')
        print(f"Q1 Computer records: {q1_records.count()}")
        
        for record in q1_records:
            print(f"\n  Student: {record.enrollment.student.first_name} {record.enrollment.student.last_name} (id={record.enrollment.student.id})")
            print(f"  Section: {record.enrollment.section.name if record.enrollment.section else 'None'}")
            print(f"  Grade: {record.grade}")
            print(f"  Final Grade: {record.final_grade}")
            print(f"  Encoded by: {record.encoded_by}")
            print(f"  Created at: {record.created_at}")
            print(f"  Enrollment id: {record.enrollment.id}")
    else:
        print("Computer subject not found")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n\n=== Checking teacher_test user ===")
try:
    teacher_test = User.objects.get(username='teacher_test')
    print(f"Found user: {teacher_test.username} (id={teacher_test.id})")
    
    # Find records encoded by this teacher
    records = AcademicRecord.objects.filter(encoded_by=teacher_test)
    print(f"Records encoded by teacher_test: {records.count()}")
    
    for record in records[:10]:
        period_str = f"Q{record.quarter}" if record.quarter else f"S{record.semester}"
        print(f"  - {record.enrollment.student.first_name} / {record.subject.name} / {period_str} / Grade: {record.grade}")
        
except User.DoesNotExist:
    print("teacher_test user not found")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
