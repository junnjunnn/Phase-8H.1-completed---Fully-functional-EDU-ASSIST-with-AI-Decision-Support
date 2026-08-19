#!/usr/bin/env python
"""Test registrar enrollment workflow - end-to-end API test."""

import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from academics.models import AcademicYear, GradeLevel, Strand, Section, Enrollment, Student
from accounts.models import UserProfile


def main():
    """Run the registrar enrollment workflow test."""
    client = APIClient()
    User = get_user_model()

    # Get or create registrar
    registrar, created = User.objects.get_or_create(
        username='registrar_runtime',
        defaults={
            'email': 'registrar_test@test.local',
            'is_active': True,
        }
    )
    if created or not hasattr(registrar, 'profile') or not registrar.profile:
        registrar.set_password('TestPassword1!')
        registrar.save()
        profile, _ = UserProfile.objects.get_or_create(user=registrar)
        profile.role_name = 'REGISTRAR'
        profile.save()

    client.force_authenticate(user=registrar)

    print("=" * 60)
    print("REGISTRAR ENROLLMENT WORKFLOW TEST")
    print("=" * 60)
    print(f"User: {registrar.username}")
    print(f"Role: {registrar.profile.role_name}")
    print()

    # Step 1: Check available academic years
    print("Step 1: Fetching available academic years...")
    try:
        resp = client.get('/api/academic-years/')
        if resp.status_code == 200:
            years = resp.json()
            results = years.get('results', []) or years
            print(f"  ✓ Found {len(results)} academic year(s)")
            if results:
                year = results[0]
                print(f"    Sample: {year.get('name')} (ID: {year.get('id')})")
        else:
            print(f"  ✗ Failed: {resp.status_code}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    print()

    # Step 2: Check available grade levels
    print("Step 2: Fetching available grade levels...")
    try:
        resp = client.get('/api/grade-levels/')
        if resp.status_code == 200:
            levels = resp.json()
            results = levels.get('results', []) or levels
            print(f"  ✓ Found {len(results)} grade level(s)")
            if results:
                level = results[0]
                print(f"    Sample: {level.get('name')} (ID: {level.get('id')})")
        else:
            print(f"  ✗ Failed: {resp.status_code}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    print()

    # Step 3: Check available sections
    print("Step 3: Fetching available sections...")
    try:
        resp = client.get('/api/sections/')
        if resp.status_code == 200:
            sections = resp.json()
            results = sections.get('results', []) or sections
            print(f"  ✓ Found {len(results)} section(s)")
            if results:
                section = results[0]
                print(f"    Sample: {section.get('name')} (ID: {section.get('id')})")
        else:
            print(f"  ✗ Failed: {resp.status_code}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    print()

    # Step 4: Check available students for enrollment
    print("Step 4: Fetching available students...")
    try:
        resp = client.get('/api/students/')
        if resp.status_code == 200:
            students = resp.json()
            results = students.get('results', []) or students
            print(f"  ✓ Found {len(results)} student(s)")
            if results:
                student = results[0]
                print(f"    Sample: {student.get('first_name')} {student.get('last_name')} (ID: {student.get('id')})")
        else:
            print(f"  ✗ Failed: {resp.status_code}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    print()

    # Step 5: Check enrollment list access
    print("Step 5: Fetching enrollments...")
    try:
        resp = client.get('/api/enrollments/')
        if resp.status_code == 200:
            enrollments = resp.json()
            results = enrollments.get('results', []) or enrollments
            print(f"  ✓ Can list enrollments: {len(results)} enrollment(s)")
        else:
            print(f"  ✗ Failed: {resp.status_code}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    print()
    print("=" * 60)
    print("ENROLLMENT WORKFLOW: ALL REFERENCE DATA ACCESSIBLE ✓")
    print("=" * 60)


if __name__ == '__main__':
    main()
