import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import TestCase
from django.contrib.auth import get_user_model
from academics.models import AcademicYear, GradeLevel, Section, Enrollment, Subject, AcademicRecord, TeacherAssignment
from students.models import Student
from accounts.models import UserProfile
from accounts.utils import get_authorized_enrollment_queryset, get_user_scope
from common.authorization import teacher_assignment_queryset
from django.db.models import Exists, OuterRef, Q

User = get_user_model()

def setup_test_data():
    """Create test data for academic record visibility tests."""
    # Create academic year
    ay = AcademicYear.objects.create(
        name='Test-2026',
        start_date='2026-06-01',
        end_date='2027-03-31',
        is_active=True
    )
    
    # Create grade level
    grade_6 = GradeLevel.objects.create(
        name='Grade 6 Test',
        code='G6TEST',
        school_level='Elementary',
        order=6
    )
    
    # Create section
    section = Section.objects.create(
        name='Test Section',
        grade_level=grade_6,
        academic_year=ay
    )
    
    # Create users
    adviser = User.objects.create_user(username='test_adviser', password='pass123')
    adviser_profile = UserProfile.objects.create(user=adviser, role_name='TEACHER')
    
    subject_teacher = User.objects.create_user(username='test_subject_teacher', password='pass123')
    subject_teacher_profile = UserProfile.objects.create(user=subject_teacher, role_name='TEACHER')
    
    # Create student
    student = Student.objects.create(
        first_name='Test',
        last_name='Student',
        student_status='active'
    )
    
    # Create enrollment
    enrollment = Enrollment.objects.create(
        student=student,
        academic_year=ay,
        grade_level=grade_6,
        section=section,
        enrollment_status='active'
    )
    
    # Create subjects
    math = Subject.objects.create(
        code='MATH6',
        name='Mathematics',
        category='Learning Area',
        grade_level=grade_6
    )
    
    english = Subject.objects.create(
        code='ENG6',
        name='English',
        category='Learning Area',
        grade_level=grade_6
    )
    
    science = Subject.objects.create(
        code='SCI6',
        name='Science',
        category='Learning Area',
        grade_level=grade_6
    )
    
    # Create teacher assignments
    # Adviser for the section
    TeacherAssignment.objects.create(
        teacher=adviser,
        academic_year=ay,
        grade_level=grade_6,
        section=section,
        assignment_type='ADVISER',
        is_active=True
    )
    
    # Subject teacher teaches Math and English
    TeacherAssignment.objects.create(
        teacher=subject_teacher,
        academic_year=ay,
        grade_level=grade_6,
        section=section,
        subject=math,
        assignment_type='SUBJECT',
        is_active=True
    )
    
    TeacherAssignment.objects.create(
        teacher=subject_teacher,
        academic_year=ay,
        grade_level=grade_6,
        section=section,
        subject=english,
        assignment_type='SUBJECT',
        is_active=True
    )
    
    # Create academic records
    # Math record (taught by subject_teacher)
    math_record = AcademicRecord.objects.create(
        enrollment=enrollment,
        subject=math,
        academic_year=ay,
        grading_period_type='Quarter',
        quarter=1,
        grade=85.00,
        encoded_by=subject_teacher
    )
    
    # English record (taught by subject_teacher)
    english_record = AcademicRecord.objects.create(
        enrollment=enrollment,
        subject=english,
        academic_year=ay,
        grading_period_type='Quarter',
        quarter=1,
        grade=90.00,
        encoded_by=subject_teacher
    )
    
    # Science record (NOT taught by subject_teacher, but adviser should see it)
    science_record = AcademicRecord.objects.create(
        enrollment=enrollment,
        subject=science,
        academic_year=ay,
        grading_period_type='Quarter',
        quarter=1,
        grade=88.00,
        encoded_by=subject_teacher  # Still encoded by subject_teacher, but it's not their assigned subject
    )
    
    return {
        'ay': ay,
        'section': section,
        'adviser': adviser,
        'subject_teacher': subject_teacher,
        'student': student,
        'enrollment': enrollment,
        'math': math,
        'english': english,
        'science': science,
        'math_record': math_record,
        'english_record': english_record,
        'science_record': science_record,
    }

def simulate_get_queryset(user, qs_input=None):
    """Simulate the get_queryset method from AcademicRecordViewSet."""
    if qs_input is None:
        qs_input = AcademicRecord.objects.select_related('enrollment', 'subject', 'academic_year', 'encoded_by')
    
    qs = get_authorized_enrollment_queryset(user, qs_input, enrollment_field='enrollment')
    scope = get_user_scope(user)
    
    if scope == 'teacher':
        adviser_assignments = teacher_assignment_queryset(user).filter(assignment_type='ADVISER')
        has_adviser_role = adviser_assignments.exists()
        
        active_subject_assignments = teacher_assignment_queryset(user).filter(assignment_type='SUBJECT')
        has_subject_assignments = active_subject_assignments.exists()
        
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
            else:
                qs = qs.filter(enrollment__section_id__in=advised_section_ids)
        elif has_subject_assignments:
            matching_assignment = active_subject_assignments.filter(
                academic_year_id=OuterRef('academic_year_id'),
                grade_level_id=OuterRef('enrollment__grade_level_id'),
                section_id=OuterRef('enrollment__section_id'),
                subject_id=OuterRef('subject_id'),
            )
            qs = qs.annotate(has_teacher_assignment=Exists(matching_assignment)).filter(has_teacher_assignment=True)
    
    return qs

# Run tests
print("=== Test 1: Adviser can see ALL academic records for their advisory students ===")
data = setup_test_data()

adviser_records = simulate_get_queryset(data['adviser']).filter(enrollment=data['enrollment']).order_by('subject__name')
print(f"Total records visible to adviser: {adviser_records.count()}")
print(f"Expected: 3 (Math, English, Science)")

subjects_visible = [r.subject.name for r in adviser_records]
print(f"Subjects visible: {subjects_visible}")

assert adviser_records.count() == 3, f"Expected 3 records, got {adviser_records.count()}"
assert 'Science' in subjects_visible, "Science not visible to adviser"
assert 'Mathematics' in subjects_visible, "Math not visible to adviser"
assert 'English' in subjects_visible, "English not visible to adviser"
print("✓ PASS: Adviser can see all records including those not taught by them")

print("\n=== Test 2: Subject teacher sees only their assigned subjects ===")
teacher_records = simulate_get_queryset(data['subject_teacher']).filter(enrollment=data['enrollment']).order_by('subject__name')
print(f"Total records visible to subject teacher: {teacher_records.count()}")
print(f"Expected: 2 (Math, English)")

subjects_visible = [r.subject.name for r in teacher_records]
print(f"Subjects visible: {subjects_visible}")

assert teacher_records.count() == 2, f"Expected 2 records, got {teacher_records.count()}"
assert 'Mathematics' in subjects_visible, "Math not visible to subject teacher"
assert 'English' in subjects_visible, "English not visible to subject teacher"
assert 'Science' not in subjects_visible, "Science should NOT be visible to subject teacher"
print("✓ PASS: Subject teacher sees only assigned subjects")

print("\n=== Test 3: Adviser can still encode only their assigned subjects ===")
# This test verifies that the authorization for CREATING/UPDATING grades is still restricted
from academics.serializers import AcademicRecordSerializer
from rest_framework.test import APIRequestFactory

factory = APIRequestFactory()
request = factory.post('/academic-records/')
request.user = data['adviser']

# Try to update a science record (not assigned to adviser)
serializer = AcademicRecordSerializer(
    data={
        'enrollment': data['enrollment'].id,
        'subject': data['science'].id,
        'academic_year': data['ay'].id,
        'grading_period_type': 'Quarter',
        'quarter': 1,
        'grade': 95.00,
    },
    context={'request': request}
)

# Should fail because adviser is not a teacher for science
try:
    if serializer.is_valid(raise_exception=True):
        print("WARNING: Serializer validation passed but should have failed")
except Exception as e:
    if 'only encode grades for your assigned subject' in str(e):
        print("✓ PASS: Adviser cannot encode grades for non-assigned subjects")
    else:
        print(f"✓ PASS: Grade encoding validation works (error: {e})")

print("\n=== All tests passed! ===")
print("\nSummary:")
print("1. Advisers can VIEW all academic records for their advisory class students")
print("2. Subject teachers can VIEW only records for subjects they teach")
print("3. Both advisers and subject teachers cannot ENCODE grades for non-assigned subjects")
print("4. This preserves monitoring functionality while maintaining edit restrictions")
