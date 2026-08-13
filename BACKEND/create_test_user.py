from django.contrib.auth import get_user_model
from accounts.models import UserProfile
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

User = get_user_model()

# Create test user
user, created = User.objects.get_or_create(
    username='testuser',
    defaults={
        'email': 'test@example.com',
        'is_active': True
    }
)

# Set password
user.set_password('Test1234!')
user.save()

# Create or update profile
profile, _ = UserProfile.objects.get_or_create(
    user=user,
    defaults={'role_name': 'SUPER_ADMIN'}
)

print(f"User created/updated: {user.username}")
print(f"Active: {user.is_active}")
print(f"Password: Test1234!")
print(f"Profile role: {profile.role_name}")
