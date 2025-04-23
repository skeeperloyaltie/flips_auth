from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User

class UserProfileTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_get_user_profile(self):
        response = self.client.get('/api/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_user_profile(self):
        data = {'subscription_level': 'Premium'}
        response = self.client.put('/api/profile/update/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['subscription_level'], 'Premium')

    def test_update_password(self):
        data = {'old_password': '12345', 'new_password': 'newpassword123'}
        response = self.client.put('/api/profile/password/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

# Additional tests for other functionality can be added similarly