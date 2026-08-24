import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from academics.models import AcademicRecord
from accounts.utils import get_authorized_enrollment_queryset, get_user_scope
from common.authorization import teacher_assignment_queryset
from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef, Q

User = get_user_model()

print("=== Testing AcademicRecordViewSet.get_queryset logic for adviser (test1) ===")
try:
    adviser = User.objects.get(username='test1')
    print(f"Adviser: {adviser.username} (id={adviser.id})")
    print(f"User scope: {get_user_scope(adviser)}")
    
    # Simulate the get_queryset logic from AcademicRecordViewSet
    qs = AcademicRecord.objects.select_related('enrollment', 'subject', 'academic_year', 'encoded_by')
    qs = get_authorized_enrollment_queryset(adviser, qs, enrollment_field='enrollment')
    
    scope = get_user_scope(adviser)
    if scope == 'teacher':
        # Check if teacher is a section adviser
        adviser_assignments = teacher_assignment_queryset(adviser).filter(assignment_type='ADVISER')
        has_adviser_role = adviser_assignments.exists()
        print(f"Has adviser role: {has_adviser_role}")
        
        # Get the teacher's subject assignments
        active_subject_assignments = teacher_assignment_queryset(adviser).filter(assignment_type='SUBJECT')
        has_subject_assignments = active_subject_assignments.exists()
        print(f"Has subject assignments: {has_subject_assignments}")
        
        # Build the filter based on adviser and subject roles
        if has_adviser_role:
            # Adviser can see all records for students in their advised sections
            advised_section_ids = adviser_assignments.values_list('section_id', flat=True)
            print(f"Advised section IDs: {list(advised_section_ids)}")
            
            if has_subject_assignments:
                # Teacher with both adviser and subject roles
                matching_assignment = active_subject_assignments.filter(
                    academic_year_id=OuterRef('academic_year_id'),
                    grade_level_id=OuterRef('enrollment__grade_level_id'),
                    section_id=OuterRef('enrollment__section_id'),
                    subject_id=OuterRef('subject_id'),
                )
                qs = qs.annotate(has_teacher_assignment=Exists(matching_assignment))
                qs = qs.filter(
                    Q(enrollment__section_id__in=advised_section_ids) |
                    Q(has_teacher_assignment=True)
                )
                print("Applied filter: adviser sections OR subject assignments")
            else:
                # Adviser with no subject assignments - just show all records for advised sections
                qs = qs.filter(enrollment__section_id__in=advised_section_ids)
                print("Applied filter: adviser sections only")
        elif has_subject_assignments:
            # Teacher without adviser role - only show records for their subject assignments
            matching_assignment = active_subject_assignments.filter(
                academic_year_id=OuterRef('academic_year_id'),
                grade_level_id=OuterRef('enrollment__grade_level_id'),
                section_id=OuterRef('enrollment__section_id'),
                subject_id=OuterRef('subject_id'),
            )
            qs = qs.annotate(has_teacher_assignment=Exists(matching_assignment)).filter(has_teacher_assignment=True)
            print("Applied filter: subject assignments only")
    
    total_records = qs.count()
    print(f"\nTotal academic records visible to adviser: {total_records}")
    
    # Filter for student 30 specifically
    student_30_records = qs.filter(enrollment__student_id=30)
    print(f"Records for student 30 (edizon): {student_30_records.count()}")
    
    # Show all subjects
    print("\nSubjects visible for student 30:")
    for record in student_30_records.order_by('subject__name'):
        print(f"  - {record.subject.name} (Grade: {record.grade})")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n\n=== Testing API logic for subject teacher (teacher_test) ===")
try:
    teacher = User.objects.get(username='teacher_test')
    print(f"Teacher: {teacher.username} (id={teacher.id})")
    print(f"User scope: {get_user_scope(teacher)}")
    
    # Simulate the get_queryset logic
    qs = AcademicRecord.objects.select_related('enrollment', 'subject', 'academic_year', 'encoded_by')
    qs = get_authorized_enrollment_queryset(teacher, qs, enrollment_field='enrollment')
    
    scope = get_user_scope(teacher)
    if scope == 'teacher':
        adviser_assignments = teacher_assignment_queryset(teacher).filter(assignment_type='ADVISER')
        has_adviser_role = adviser_assignments.exists()
        print(f"Has adviser role: {has_adviser_role}")
        
        active_subject_assignments = teacher_assignment_queryset(teacher).filter(assignment_type='SUBJECT')
        has_subject_assignments = active_subject_assignments.exists()
        print(f"Has subject assignments: {has_subject_assignments}")
        
        if has_adviser_role:
            advised_section_ids = adviser_assignments.values_list('section_id', flat=True)
            if has_subject_assignments:
                matching_assignment = active_subject_assignments.filter(
                    academic_year_id=OuterRef('academic_year_id'),
                    grade_level_id=OuterRef('enrollment__grade_level_id'),
                    section_id=OuterRef('enrollment__section_id'),
                    subject_id=OuterRef('subject_id'),
                )
                qs = qs.annotate(has_teacher_assignment=Exists(matching_assignment))
                qs = qs.filter(
                    Q(enrollment__section_id__in=advised_section_ids) |
                    Q(has_teacher_assignment=True)
                )
        elif has_subject_assignments:
            matching_assignment = active_subject_assignments.filter(
                academic_year_id=OuterRef('academic_year_id'),
                grade_level_id=OuterRef('enrollment__grade_level_id'),
                section_id=OuterRef('enrollment__section_id'),
                subject_id=OuterRef('subject_id'),
            )
            qs = qs.annotate(has_teacher_assignment=Exists(matching_assignment)).filter(has_teacher_assignment=True)
            print("Applied filter: subject assignments only")
    
    total_records = qs.count()
    print(f"\nTotal academic records visible to teacher: {total_records}")
    
    # Filter for student 30 specifically
    student_30_records = qs.filter(enrollment__student_id=30)
    print(f"Records for student 30 (edizon): {student_30_records.count()}")
    
    # Show all subjects
    print("\nSubjects visible for student 30:")
    for record in student_30_records.order_by('subject__name'):
        print(f"  - {record.subject.name} (Grade: {record.grade})")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
