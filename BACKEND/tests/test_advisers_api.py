from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


class AdvisersApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # create users
        self.teacher = User.objects.create_user(username='t1', password='pass', first_name='Teach', last_name='One')
        self.teacher.profile.role_name = 'TEACHER'
        self.teacher.profile.save()

        self.admin = User.objects.create_user(username='a1', password='pass', first_name='Admin', last_name='One')
        self.admin.profile.role_name = 'SCHOOL_ADMIN'
        self.admin.profile.save()

        self.other = User.objects.create_user(username='u1', password='pass', first_name='User', last_name='One')
        self.other.profile.role_name = 'GUIDANCE'
        self.other.profile.save()

        # login as teacher (authorized staff)
        self.client.force_authenticate(user=self.teacher)

    def test_advisers_list_returns_teachers_and_admins(self):
        resp = self.client.get('/api/auth/advisers/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        ids = {item['id'] for item in data}
        self.assertIn(self.teacher.pk, ids)
        self.assertIn(self.admin.pk, ids)
        self.assertNotIn(self.other.pk, ids)
