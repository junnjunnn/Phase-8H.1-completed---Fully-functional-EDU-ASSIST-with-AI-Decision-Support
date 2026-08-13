from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient

from accounts.models import UserProfile


class UserListPermissionTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()

        # school admin
        self.school_admin = self.user_model.objects.create_user(username='school_admin', password='AdminPass1!')
        UserProfile.objects.create(user=self.school_admin, role_name='SCHOOL_ADMIN')

        # teacher
        self.teacher = self.user_model.objects.create_user(username='teacher_user', password='Teacher1!')
        UserProfile.objects.create(user=self.teacher, role_name='TEACHER')

        # guidance
        self.guidance = self.user_model.objects.create_user(username='guidance_user', password='Guide1!')
        UserProfile.objects.create(user=self.guidance, role_name='GUIDANCE')

        # registrar
        self.registrar = self.user_model.objects.create_user(username='registrar_user', password='Registrar1!')
        UserProfile.objects.create(user=self.registrar, role_name='REGISTRAR')

    def test_school_admin_get_users(self):
        self.client.force_authenticate(user=self.school_admin)
        resp = self.client.get('/api/auth/users/')
        self.assertEqual(resp.status_code, 200)

    def test_teacher_get_users_allowed(self):
        self.client.force_authenticate(user=self.teacher)
        resp = self.client.get('/api/auth/users/')
        self.assertEqual(resp.status_code, 200)

    def test_guidance_get_users_allowed(self):
        self.client.force_authenticate(user=self.guidance)
        resp = self.client.get('/api/auth/users/')
        self.assertEqual(resp.status_code, 200)

    def test_anonymous_cannot_get_users(self):
        resp = self.client.get('/api/auth/users/')
        self.assertIn(resp.status_code, (401, 403))

    def test_registrar_cannot_get_users(self):
        self.client.force_authenticate(user=self.registrar)
        resp = self.client.get('/api/auth/users/')
        self.assertIn(resp.status_code, (403, 401))

    def test_registrar_can_access_students(self):
        self.client.force_authenticate(user=self.registrar)
        resp = self.client.get('/api/students/')
        self.assertEqual(resp.status_code, 200)

    def test_teacher_cannot_post_create_user(self):
        self.client.force_authenticate(user=self.teacher)
        resp = self.client.post('/api/auth/users/', {'username': 'newuser', 'password': 'P@ssword1', 'role_name': 'TEACHER'})
        self.assertIn(resp.status_code, (403, 400))
