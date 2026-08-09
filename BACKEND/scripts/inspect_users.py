import os
import django
import sys
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.contrib.auth import get_user_model
from accounts.models import UserProfile
from rest_framework.test import APIClient
import pprint

User = get_user_model()
print('TOTAL_USERS', User.objects.count())
print('SUPER_ADMIN', UserProfile.objects.filter(role_name='SUPER_ADMIN').count())
print('SCHOOL_ADMIN', UserProfile.objects.filter(role_name='SCHOOL_ADMIN').count())
print('TEACHER', UserProfile.objects.filter(role_name='TEACHER').count())
print('GUIDANCE', UserProfile.objects.filter(role_name='GUIDANCE').count())

sa = UserProfile.objects.filter(role_name='SUPER_ADMIN').first()
if sa:
    print('SUPER_ADMIN_USER', sa.user.id, sa.user.username, sa.user.first_name, sa.user.last_name, sa.user.is_active)
    c = APIClient()
    c.force_authenticate(user=sa.user)
    r = c.get('/api/auth/users/')
    print('API_STATUS', r.status_code)
    try:
        pprint.pprint(r.data[:50])
    except Exception:
        pprint.pprint(r.data)
else:
    print('No SUPER_ADMIN user found')
