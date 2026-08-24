#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from students.models import Student
from academics.models import Enrollment, AcademicRecord, AcademicYear, GradeLevel, Section, Subject

# Find the test student (Grade 6, Onyx section)
print("=== Finding Test Student ===")
try:
    # Look for students in Grade 6 Onyx
    grade_6 = GradeLevel.objects.get(name='Grade 6')
    print(f"Found Grade Level: {grade_6.name} (id={grade_6.id})")
    
    active_ay = AcademicYear.objects.get(is_active=True)
    print(f"Active Academic Year: {active_ay.name} (id={active_ay.id})")
    
    onyx_section = Section.objects.filter(grade_level=grade_6, academic_year=active_ay, name__icontains='Onyx').first()
    if onyx_section:
        print(f"Found Onyx Section: {onyx_section.name} (id={onyx_section.id})")
        
        # Find students in this section
        enrollments = Enrollment.objects.filter(section=onyx_section, enrollment_status='active')
        print(f"\nActive enrollments in Onyx: {enrollments.count()}")
        
        for enrollment in enrollments[:3]:  # Show first 3
            print(f"\n  Student: {enrollment.student.first_name} {enrollment.student.last_name} (id={enrollment.student.id})")
            print(f"  Enrollment id: {enrollment.id}")
            
            # Check academic records for this student
            records = AcademicRecord.objects.filter(enrollment=enrollment)
            print(f"  Total Academic Records: {records.count()}")
            
            for record in records:
                print(f"    - {record.subject.name} / Q{record.quarter if record.quarter else f'S{record.semester}'} / Grade: {record.grade}")
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
        print(f"Found Subject: {computer.name} (id={computer.id})")
        
        # Find all Q1 Computer records
        q1_records = AcademicRecord.objects.filter(
            subject=computer,
            grading_period_type='Quarter',
            quarter=1
        )
        print(f"Q1 Computer records: {q1_records.count()}")
        
        for record in q1_records:
            print(f"\n  Student: {record.enrollment.student.first_name} {record.enrollment.student.last_name}")
            print(f"  Grade: {record.grade}")
            print(f"  Encoded by: {record.encoded_by}")
            print(f"  Created at: {record.created_at}")
            print(f"  Enrollment id: {record.enrollment.id}")
    else:
        print("Computer subject not found")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
