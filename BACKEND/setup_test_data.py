#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from academics.models import Strand, AcademicYear, GradeLevel, Section
from students.models import Student
from django.contrib.auth import get_user_model

User = get_user_model()

# Create strands
strands_to_create = ['STEM', 'ABM', 'HUMSS', 'GAS', 'TVL ICT', 'TVL HE']
for strand_name in strands_to_create:
    s, created = Strand.objects.get_or_create(
        name=strand_name, 
        defaults={'code': strand_name.replace(' ', '_'), 'is_active': True}
    )
    if created:
        print(f"Created strand: {strand_name}")
    else:
        print(f"Strand already exists: {strand_name}")

# Get or create grade 12
grade_12, created = GradeLevel.objects.get_or_create(
    name='Grade 12 - Garnet',
    defaults={'code': 'G12G', 'school_level': 'Senior High School', 'order': 12}
)
print(f"Grade 12 - Garnet: {grade_12} (created={created})")

# Get active academic year
active_year = AcademicYear.objects.filter(is_active=True).first()
if not active_year:
    active_year = AcademicYear.objects.create(
        name='2026-2027', 
        start_date='2026-08-01', 
        end_date='2027-03-31', 
        is_active=True
    )
print(f"Active year: {active_year}")

# Get teacher user
teacher = User.objects.filter(username='demo_teacher').first()
if not teacher:
    teacher = User.objects.filter(role='Teacher').first()
print(f"Teacher: {teacher}")

# Create sections
sections_to_create = [
    {'name': 'Grade 12 - Ruby', 'capacity': 30},
    {'name': 'Grade 12 - Sapphire', 'capacity': 28},
    {'name': 'Grade 12 - Diamond', 'capacity': 32},
]

for sec_data in sections_to_create:
    section, created = Section.objects.get_or_create(
        grade_level=grade_12,
        academic_year=active_year,
        name=sec_data['name'],
        defaults={
            'capacity': sec_data['capacity'],
            'description': f'Senior High {sec_data["name"]}',
            'adviser': teacher,
            'is_active': True
        }
    )
    if created:
        print(f"Created section: {section.name}")
    else:
        print(f"Section already exists: {section.name}")

# Get some students
students = Student.objects.all()[:5]
print(f"Available students: {len(students)}")
for student in students:
    full_name = f"{student.first_name} {student.last_name}"
    print(f"  - {full_name} (LRN: {student.lrn})")

print("\nSetup complete!")
