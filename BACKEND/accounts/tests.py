from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient, APITestCase

from .models import UserProfile


class AuthenticationAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(username='teacher_test', password='Pass1234!')
        self.profile = UserProfile.objects.create(user=self.user, role_name='TEACHER')

    def test_login_success(self):
        response = self.client.post('/api/auth/login/', {'username': 'teacher_test', 'password': 'Pass1234!'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['username'], 'teacher_test')

    def test_login_inactive_user(self):
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])
        response = self.client.post('/api/auth/login/', {'username': 'teacher_test', 'password': 'Pass1234!'}, format='json')
        self.assertEqual(response.status_code, 401)
        self.assertIn('detail', response.data)

    def test_me_endpoint_requires_authentication(self):
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 401)

    def test_me_endpoint_returns_current_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'teacher_test')

    def test_protected_students_endpoint_requires_authentication(self):
        response = self.client.get('/api/students/')
        self.assertEqual(response.status_code, 401)

    def test_teacher_can_list_users(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/auth/users/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.data, list) or response.data.get('results') is not None)

    def test_guidance_can_list_users(self):
        guidance = self.user_model.objects.create_user(username='guidance_test', password='Pass1234!')
        UserProfile.objects.create(user=guidance, role_name='GUIDANCE')
        self.client.force_authenticate(user=guidance)
        response = self.client.get('/api/auth/users/')
        self.assertEqual(response.status_code, 200)

    def test_school_admin_can_list_users(self):
        school_admin = self.user_model.objects.create_user(username='school_admin_test', password='Pass1234!')
        UserProfile.objects.create(user=school_admin, role_name='SCHOOL_ADMIN')
        self.client.force_authenticate(user=school_admin)
        response = self.client.get('/api/auth/users/')
        self.assertEqual(response.status_code, 200)

    def test_anonymous_cannot_list_users(self):
        response = self.client.get('/api/auth/users/')
        self.assertIn(response.status_code, (401, 403))

    def test_teacher_cannot_create_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/auth/users/', {
            'username': 'new_teacher',
            'password': 'Pass1234!',
            'role_name': 'TEACHER',
        }, format='json')
        self.assertEqual(response.status_code, 403)

    def test_school_admin_can_create_user(self):
        school_admin = self.user_model.objects.create_user(username='school_admin_create', password='Pass1234!')
        UserProfile.objects.create(user=school_admin, role_name='SCHOOL_ADMIN')
        self.client.force_authenticate(user=school_admin)
        response = self.client.post('/api/auth/users/', {
            'username': 'created_teacher',
            'password': 'Pass1234!',
            'role_name': 'TEACHER',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['detail'], 'User created.')

    def test_current_user_can_update_profile(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch('/api/auth/me/', {'first_name': 'Ada', 'last_name': 'Lovelace', 'email': 'ada@example.com', 'username': 'ada'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['first_name'], 'Ada')
        self.assertEqual(response.data['email'], 'ada@example.com')
        self.assertEqual(response.data['username'], 'ada')

    def test_current_user_can_update_profile(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch('/api/auth/me/', {'first_name': 'Ada', 'last_name': 'Lovelace', 'email': 'ada@example.com', 'username': 'ada'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['first_name'], 'Ada')
        self.assertEqual(response.data['email'], 'ada@example.com')
        self.assertEqual(response.data['username'], 'ada')

    def test_current_user_can_change_password(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/auth/change-password/', {
            'current_password': 'Pass1234!',
            'new_password': 'NewPass123!',
            'confirm_password': 'NewPass123!',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass123!'))
