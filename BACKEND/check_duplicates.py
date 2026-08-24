import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from academics.models import AcademicRecord
from django.db.models import Count

print("=== Checking for Duplicate Academic Records ===")
try:
    # Find records with same enrollment, subject, academic_year, period, quarter
    duplicates = AcademicRecord.objects.values(
        'enrollment', 'subject', 'academic_year', 'grading_period_type', 'quarter', 'semester'
    ).annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    print(f"Found {duplicates.count()} groups with duplicates:")
    
    for dup in duplicates[:10]:
        print(f"\nDuplicate group:")
        print(f"  Enrollment: {dup['enrollment']}")
        print(f"  Subject: {dup['subject']}")
        print(f"  Academic Year: {dup['academic_year']}")
        period_str = f"Q{dup['quarter']}" if dup['quarter'] else f"S{dup['semester']}"
        print(f"  Period: {dup['grading_period_type']} {period_str}")
        print(f"  Count: {dup['count']}")
        
        # Show the records
        records = AcademicRecord.objects.filter(
            enrollment_id=dup['enrollment'],
            subject_id=dup['subject'],
            academic_year_id=dup['academic_year'],
            grading_period_type=dup['grading_period_type'],
            quarter=dup['quarter'],
            semester=dup['semester']
        ).order_by('-created_at')
        
        for i, record in enumerate(records):
            print(f"    Record {i+1}: id={record.id}, grade={record.grade}, created={record.created_at}")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n\n=== Checking Computer Quarter 1 for Student 30 (edizon) ===")
try:
    computer_q1_records = AcademicRecord.objects.filter(
        enrollment_id=31,  # edizon's enrollment
        subject__name__icontains='Computer',
        grading_period_type='Quarter',
        quarter=1
    ).order_by('-created_at')
    
    print(f"Found {computer_q1_records.count()} record(s):")
    for record in computer_q1_records:
        print(f"  id={record.id}, grade={record.grade}, final_grade={record.final_grade}, created={record.created_at}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n\n=== Checking Adviser Information ===")
try:
    from academics.models import Section
    from accounts.models import UserProfile
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # Get the Onyx section
    onyx = Section.objects.get(name='Onyx')
    print(f"Onyx section adviser: {onyx.adviser}")
    
    if onyx.adviser:
        profile = UserProfile.objects.filter(user=onyx.adviser).first()
        print(f"Adviser profile role: {profile.role_name if profile else 'No profile'}")
        print(f"Adviser assigned sections: {profile.assigned_sections.count() if profile else 0}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
