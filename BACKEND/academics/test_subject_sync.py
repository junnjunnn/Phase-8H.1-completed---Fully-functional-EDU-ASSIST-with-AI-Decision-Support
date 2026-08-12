from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient

from accounts.models import UserProfile
from academics.models import Subject, GradeLevel


class SubjectSyncTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()
        self.admin = self.user_model.objects.create_user(username='admin_subjects', password='AdminPass1!')
        UserProfile.objects.create(user=self.admin, role_name='SCHOOL_ADMIN')

        self.grade = GradeLevel.objects.create(name='Grade X', code='GX', school_level='High', order=10)

    def test_create_subject_and_list(self):
        self.client.force_authenticate(user=self.admin)
        data = {'code': 'BIO1', 'name': 'Biology 1', 'category': 'Learning Area', 'grade_level': self.grade.id}
        resp = self.client.post('/api/subjects/', data)
        self.assertEqual(resp.status_code, 201)

        # now GET list and ensure subject present
        list_resp = self.client.get('/api/subjects/')
        self.assertEqual(list_resp.status_code, 200)
        names = [s['name'] for s in list_resp.data.get('results', list_resp.data)]
        self.assertIn('Biology 1', names)
