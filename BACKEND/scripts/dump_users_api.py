import os, sys, json
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
from accounts.models import UserProfile
from rest_framework.test import APIClient

User = get_user_model()
sa_profile = UserProfile.objects.filter(role_name='SUPER_ADMIN').select_related('user').first()
if not sa_profile:
    print(json.dumps({'error':'no superadmin found'}))
    sys.exit(1)
client = APIClient()
client.force_authenticate(user=sa_profile.user)
resp = client.get('/api/auth/users/')
try:
    print(json.dumps(resp.data, indent=2, default=str))
except Exception:
    print(repr(resp.data))
