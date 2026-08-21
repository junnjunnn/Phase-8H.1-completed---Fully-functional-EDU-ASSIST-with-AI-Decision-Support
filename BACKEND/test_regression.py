#!/usr/bin/env python
"""Quick regression test for role-based permissions."""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from accounts.models import UserProfile

def test_role_access(username, role_name, endpoint, should_allow=True):
    """Test if a role can access an endpoint."""
    client = APIClient()
    User = get_user_model()

    # Get or create user
    user, _ = User.objects.get_or_create(
        username=username,
        defaults={'is_active': True, 'first_name': role_name}
    )
    profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'role_name': role_name})

    client.force_authenticate(user=user)

    try:
        resp = client.get(endpoint)
        status = resp.status_code
        allowed = status in (200, 400)  # 200 = success, 400 = validation error (but not 403)
        result = "[PASS]" if allowed == should_allow else "[FAIL]"
        return (status, allowed == should_allow, result)
    except Exception as e:
        return (None, False, f"ERROR: {e}")


def main():
    """Run the regression test."""
    # Test scenarios
    test_cases = [
        # (username, role, endpoint, should_allow, description)
        ("teacher_test", "TEACHER", "/api/academic-years/", True, "Teacher can read academic years"),
        ("guidance_test", "GUIDANCE", "/api/academic-years/", True, "Guidance can read academic years"),
        ("registrar_test", "REGISTRAR", "/api/academic-years/", True, "Registrar can read academic years (FIXED)"),
        ("admin_test", "SUPER_ADMIN", "/api/academic-years/", True, "Admin can read academic years"),

        ("registrar_test", "REGISTRAR", "/api/students/", True, "Registrar can read students"),
        ("teacher_test", "TEACHER", "/api/students/", True, "Teacher can read students"),
        ("guidance_test", "GUIDANCE", "/api/students/", True, "Guidance can read students"),

        ("registrar_test", "REGISTRAR", "/api/enrollments/", True, "Registrar can read enrollments"),
        ("teacher_test", "TEACHER", "/api/enrollments/", True, "Teacher can read enrollments"),
        ("guidance_test", "GUIDANCE", "/api/enrollments/", True, "Guidance can read enrollments"),
    ]

    print("=" * 70)
    print("ROLE-BASED ACCESS CONTROL REGRESSION TEST")
    print("=" * 70)
    print()
    print("Testing Role Access:")
    print("-" * 70)

    all_pass = True
    for username, role, endpoint, should_allow, description in test_cases:
        status, passed, result = test_role_access(username, role, endpoint, should_allow)
        all_pass = all_pass and passed
        print(f"{result} {description:50s} ({status})")

    print()
    print("=" * 70)
    if all_pass:
        print("REGRESSION TEST: PASSED")
    else:
        print("REGRESSION TEST: FAILED")
    print("=" * 70)


if __name__ == '__main__':
    main()
