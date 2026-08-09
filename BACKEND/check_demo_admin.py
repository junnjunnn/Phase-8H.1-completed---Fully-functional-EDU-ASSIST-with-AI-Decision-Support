import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_sqlite')
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model, authenticate

print('DJANGO_SETTINGS_MODULE:', os.environ['DJANGO_SETTINGS_MODULE'])
print('DATABASES:', settings.DATABASES)

User = get_user_model()
try:
    user = User.objects.get(username='demo_admin')
    print('found user:', user.username)
    print('is_active:', user.is_active)
    print('is_staff:', user.is_staff)
    print('is_superuser:', user.is_superuser)
    print('password raw:', user.password)
    print('check_password DemoAdmin123! ->', user.check_password('DemoAdmin123!'))
    user2 = authenticate(username='demo_admin', password='DemoAdmin123!')
    print('authenticate returned', user2)
except User.DoesNotExist:
    print('demo_admin does not exist')
