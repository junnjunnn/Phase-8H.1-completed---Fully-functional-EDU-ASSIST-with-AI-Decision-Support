import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from academics.models import TeacherAssignment
from django.contrib.auth import get_user_model

User = get_user_model()

print("=== Teacher Assignments for test1 (Adviser) ===")
try:
    adviser = User.objects.get(username='test1')
    print(f"Adviser: {adviser.username} (id={adviser.id})")
    
    assignments = TeacherAssignment.objects.filter(teacher=adviser, is_active=True)
    print(f"Total active assignments: {assignments.count()}")
    
    for assignment in assignments:
        print(f"  - {assignment.section.name} {assignment.subject.name if assignment.subject else '(Adviser)'} ({assignment.assignment_type})")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n\n=== Teacher Assignments for teacher_test ===")
try:
    teacher = User.objects.get(username='teacher_test')
    print(f"Teacher: {teacher.username} (id={teacher.id})")
    
    assignments = TeacherAssignment.objects.filter(teacher=teacher, is_active=True)
    print(f"Total active assignments: {assignments.count()}")
    
    for assignment in assignments:
        role = 'Adviser' if assignment.assignment_type == 'ADVISER' else assignment.subject.name if assignment.subject else 'None'
        print(f"  - {assignment.section.name} {role} ({assignment.assignment_type})")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n\n=== Computer Subject Assignments in Grade 6 Onyx ===")
try:
    from academics.models import Subject, Section
    
    onyx = Section.objects.get(name='Onyx')
    computer = Subject.objects.get(name__icontains='Computer')
    
    assignments = TeacherAssignment.objects.filter(
        subject=computer,
        section=onyx,
        is_active=True,
        assignment_type='SUBJECT'
    )
    
    print(f"Computer subject assignments in Onyx: {assignments.count()}")
    for assignment in assignments:
        print(f"  - {assignment.teacher.username}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
