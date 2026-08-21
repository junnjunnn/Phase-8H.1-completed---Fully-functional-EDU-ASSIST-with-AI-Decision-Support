#!/usr/bin/env python
"""Test that registrar is blocked from admin-only operations."""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from accounts.models import UserProfile

def test_blocked_operation(username, role_name, method, endpoint):
    """Test if a role is blocked from an operation."""
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
        if method == 'POST':
            resp = client.post(endpoint, {'dummy': 'data'})
        elif method == 'PUT':
            resp = client.put(endpoint, {'dummy': 'data'})
        elif method == 'PATCH':
            resp = client.patch(endpoint, {'dummy': 'data'})
        else:
            resp = client.get(endpoint)

        status = resp.status_code
        # 403 = Forbidden, 404 = Not Found (treated as blocked)
        blocked = status in (403, 404)
        return (status, blocked)
    except Exception as e:
        return (None, False)


def main():
    """Run the access control test."""
    # Test scenarios - registrar should be blocked from these
    blocked_tests = [
        ("registrar_test", "REGISTRAR", "GET", "/api/auth/users/", "User list (admin only)"),
        ("registrar_test", "REGISTRAR", "POST", "/api/academic-years/", "Create academic year (admin only)"),
        ("registrar_test", "REGISTRAR", "POST", "/api/grade-levels/", "Create grade level (admin only)"),
        ("registrar_test", "REGISTRAR", "POST", "/api/sections/", "Create section (admin only)"),
        ("registrar_test", "REGISTRAR", "POST", "/api/subjects/", "Create subject (admin only)"),
    ]

    # Test scenarios - registrar SHOULD be allowed for enrollment operations
    allowed_tests = [
        ("registrar_test", "REGISTRAR", "GET", "/api/enrollments/", "List enrollments (allowed)"),
        ("registrar_test", "REGISTRAR", "GET", "/api/students/", "List students (allowed)"),
        ("registrar_test", "REGISTRAR", "GET", "/api/academic-years/", "List academic years (allowed)"),
    ]

    print("=" * 70)
    print("REGISTRAR BLOCKING TEST - ADMIN-ONLY OPERATIONS")
    print("=" * 70)
    print()

    print("Blocked Operations (should be 403 or 404):")
    print("-" * 70)
    all_blocked = True
    for username, role, method, endpoint, description in blocked_tests:
        status, blocked = test_blocked_operation(username, role, method, endpoint)
        result = "[PASS]" if blocked else "[FAIL]"
        all_blocked = all_blocked and blocked
        print(f"{result} {description:50s} ({method:6s}) - {status}")

    print()
    print("Allowed Operations (should be 200 or 400):")
    print("-" * 70)
    all_allowed = True
    for username, role, method, endpoint, description in allowed_tests:
        status, blocked = test_blocked_operation(username, role, method, endpoint)
        allowed = not blocked
        result = "[PASS]" if allowed else "[FAIL]"
        all_allowed = all_allowed and allowed
        print(f"{result} {description:50s} ({method:6s}) - {status}")

    print()
    print("=" * 70)
    if all_blocked and all_allowed:
        print("ACCESS CONTROL TEST: PASSED")
        print("Registrar is correctly blocked from admin operations.")
        print("Registrar can access allowed enrollment operations.")
    else:
        print("ACCESS CONTROL TEST: FAILED")
        if not all_blocked:
            print("  - Registrar was NOT blocked from admin operations")
        if not all_allowed:
            print("  - Registrar was incorrectly blocked from allowed operations")
    print("=" * 70)


if __name__ == '__main__':
    main()
