#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from behavior.models import CoreValue, BehaviorIndicator, BehavioralAssessment, BehavioralRating

print("\n=== CORE VALUES ===")
for cv in CoreValue.objects.all():
    print(f"  {cv.name} (id={cv.id}, is_active={cv.is_active})")

print("\n=== BEHAVIOR INDICATORS ===")
for bi in BehaviorIndicator.objects.all():
    print(f"  {bi.name} (id={bi.id}) -> {bi.core_value.name} (is_active={bi.is_active})")

print("\n=== BEHAVIORAL RATINGS ===")
for br in BehavioralRating.objects.all():
    print(f"  {br.code} - {br.label} (is_active={br.is_active})")

print("\n=== BEHAVIORAL ASSESSMENT RECORDS ===")
count = BehavioralAssessment.objects.count()
print(f"Total records: {count}")
for record in BehavioralAssessment.objects.select_related('core_value', 'behavior_indicator', 'rating').all()[:10]:
    print(f"  {record.enrollment.student.first_name} - CV:{record.core_value.name} - Indicator:{record.behavior_indicator.name} - Rating:{record.rating.code if record.rating else 'NONE'}")
