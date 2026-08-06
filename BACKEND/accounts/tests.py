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

    def test_authenticated_but_unauthorized_staff_cannot_access_restricted_user_list(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/auth/users/')
        self.assertEqual(response.status_code, 403)

    def test_superadmin_can_manage_users(self):
        superadmin = self.user_model.objects.create_user(username='superadmin_test', password='Pass1234!')
        UserProfile.objects.create(user=superadmin, role_name='SUPER_ADMIN')
        self.client.force_authenticate(user=superadmin)
        response = self.client.get('/api/auth/users/')
        self.assertEqual(response.status_code, 200)
