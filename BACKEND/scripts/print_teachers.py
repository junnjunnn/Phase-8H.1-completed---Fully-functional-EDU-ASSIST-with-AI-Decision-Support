import os, sys, json
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
from accounts.models import UserProfile
User = get_user_model()

teachers = []
for p in UserProfile.objects.filter(role_name='TEACHER').select_related('user'):
    u = p.user
    teachers.append({'id': u.id, 'username': u.username, 'first_name': u.first_name, 'last_name': u.last_name, 'is_active': u.is_active, 'role_name': p.role_name})
output = {'count': len(teachers), 'teachers': teachers}
print(json.dumps(output, indent=2, default=str))
