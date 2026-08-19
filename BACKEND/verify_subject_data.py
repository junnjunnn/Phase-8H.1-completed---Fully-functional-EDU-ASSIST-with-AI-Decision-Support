#!/usr/bin/env python
"""Verify subject data compatibility with Phase 3 rules."""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_sqlite')
django.setup()

from academics.models import Subject

qs = Subject.objects.select_related('grade_level', 'strand')

total = qs.count()
elementary = qs.filter(grade_level__school_level='Elementary').count()
jhs = qs.filter(grade_level__school_level='Junior High School').count()
shs = qs.filter(grade_level__school_level='Senior High School').count()
with_strands = qs.exclude(strand__isnull=True).count()
without_strands = qs.filter(strand__isnull=True).count()

print("SUBJECT DATA VERIFICATION")
print("=" * 70)
print(f"total_subjects: {total}")
print(f"elementary: {elementary}")
print(f"jhs: {jhs}")
print(f"shs: {shs}")
print(f"subjects_with_strands: {with_strands}")
print(f"subjects_without_strands: {without_strands}")
print()

invalid = []
for s in qs:
    if s.grade_level is None:
        continue
    if s.grade_level.school_level in ['Elementary', 'Junior High School'] and s.category != 'Learning Area':
        invalid.append((s.code, s.name, s.grade_level.school_level, s.category, s.strand.code if s.strand else None, 'non_learning_area'))
    elif s.grade_level.school_level == 'Senior High School' and s.category == 'Learning Area':
        invalid.append((s.code, s.name, s.grade_level.school_level, s.category, s.strand.code if s.strand else None, 'shs_learning_area'))
    if s.strand and s.grade_level.school_level in ['Elementary', 'Junior High School']:
        invalid.append((s.code, s.name, s.grade_level.school_level, s.category, s.strand.code if s.strand else None, 'elementary_or_jhs_with_strand'))
    if s.strand and s.grade_level.school_level == 'Senior High School' and not s.strand.is_active:
        invalid.append((s.code, s.name, s.grade_level.school_level, s.category, s.strand.code if s.strand else None, 'inactive_shs_strand'))

print(f"legacy_or_invalid_records: {len(invalid)}")
if invalid:
    print()
    print("Legacy records requiring admin review:")
    print("-" * 70)
    for rec in invalid:
        strand_display = rec[4] if rec[4] else "(none)"
        print(f"Code: {rec[0]:15s} Name: {rec[1]:30s} Level: {rec[2]:20s}")
        print(f"  Category: {rec[3]:20s} Strand: {strand_display:15s} Reason: {rec[5]}")
        print()
else:
    print("No legacy/invalid records found.")
print("=" * 70)
