#!/usr/bin/env python
"""Test registrar access to academic reference endpoints after permission fix."""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from accounts.models import UserProfile


def main():
    """Run the registrar access test."""
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

    # Test academic endpoints
    paths = [
        '/api/auth/me/',
        '/api/students/',
        '/api/enrollments/',
        '/api/academic-years/',
        '/api/grade-levels/',
        '/api/subjects/',
        '/api/sections/',
    ]

    print(f"REGISTRAR_OK: {registrar.username}")
    print(f"ROLE: {registrar.profile.role_name}")
    print()

    for path in paths:
        try:
            resp = client.get(path)
            print(f"ALLOW: {path} ({resp.status_code})")
        except Exception as e:
            print(f"ERROR: {path} - {e}")


if __name__ == '__main__':
    main()
