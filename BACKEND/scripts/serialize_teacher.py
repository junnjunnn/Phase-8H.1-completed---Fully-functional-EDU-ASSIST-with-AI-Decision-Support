import os, sys, json
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
from accounts.models import UserProfile
from accounts.serializers import UserSerializer

User = get_user_model()
profile = UserProfile.objects.filter(role_name='TEACHER').select_related('user').first()
if not profile:
    print(json.dumps({'error':'no teacher profile found'}))
    sys.exit(1)
user = profile.user
serializer = UserSerializer(user)
import pprint
pprint.pprint(serializer.data)
