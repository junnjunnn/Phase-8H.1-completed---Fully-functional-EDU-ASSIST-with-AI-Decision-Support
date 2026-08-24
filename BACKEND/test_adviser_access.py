import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from academics.models import AcademicRecord, Enrollment
from accounts.utils import get_authorized_enrollment_queryset, get_user_scope
from django.contrib.auth import get_user_model

User = get_user_model()

print("=== Checking Adviser (test1) Access to Academic Records ===")
try:
    adviser = User.objects.get(username='test1')
    print(f"Adviser: {adviser.username} (id={adviser.id})")
    
    # Check what enrollments the adviser can see
    all_enrollments = Enrollment.objects.all()
    print(f"Total enrollments in system: {all_enrollments.count()}")
    
    # Check authorized enrollments using the authorization function
    authorized_enrollments = get_authorized_enrollment_queryset(adviser, all_enrollments)
    print(f"Enrollments visible to adviser: {authorized_enrollments.count()}")
    
    # Check if student 30 (edizon) is in authorized enrollments
    student_30_enrollments = authorized_enrollments.filter(student_id=30)
    print(f"Student 30 enrollments visible to adviser: {student_30_enrollments.count()}")
    
    if student_30_enrollments.exists():
        for enrollment in student_30_enrollments:
            print(f"  - Enrollment {enrollment.id}: {enrollment.student} in {enrollment.section}")
            
            # Check academic records for this enrollment
            records = AcademicRecord.objects.filter(enrollment=enrollment)
            print(f"    Total academic records: {records.count()}")
            
            # Now check if these records are visible through the filtered queryset
            # This simulates what the API does
            filtered_records = AcademicRecord.objects.filter(
                enrollment__in=authorized_enrollments
            ).filter(enrollment_id=enrollment.id)
            print(f"    Records visible through API filter: {filtered_records.count()}")
            
            for record in filtered_records[:3]:
                print(f"      - {record.subject.name} Q{record.quarter if record.quarter else f'S{record.semester}'} Grade: {record.grade}")
    else:
        print("  Student 30 not found in adviser's authorized enrollments")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n\n=== Checking Enrollment Authorization Logic ===")
try:
    adviser = User.objects.get(username='test1')
    enrollment = Enrollment.objects.get(id=31)  # edizon's enrollment
    
    print(f"Checking authorization for:")
    print(f"  User: {adviser.username} (id={adviser.id})")
    print(f"  Enrollment: {enrollment.id} - {enrollment.student} in {enrollment.section}")
    
    # Check user scope
    scope = get_user_scope(adviser)
    print(f"  User scope: {scope}")
    
    # Check if enrollment is in the authorized list
    authorized = get_authorized_enrollment_queryset(adviser, Enrollment.objects.filter(id=31))
    print(f"  Is enrollment authorized: {authorized.exists()}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n\n=== Testing API Filter (enrollment__student) ===")
try:
    adviser = User.objects.get(username='test1')
    all_records = AcademicRecord.objects.all()
    print(f"Total academic records: {all_records.count()}")
    
    # Filter for student 30
    records_for_student_30 = AcademicRecord.objects.filter(enrollment__student_id=30)
    print(f"Records for student 30 (enrollment__student): {records_for_student_30.count()}")
    
    for record in records_for_student_30:
        print(f"  - {record.subject.name} Grade: {record.grade}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
