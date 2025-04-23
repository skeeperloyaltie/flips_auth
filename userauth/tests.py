from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient

class UserRegistrationTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_user_without_email(self):
        response = self.client.post('/register/', {
            'username': 'testuser',
            'password': 'testpassword'
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)

    def test_register_user_with_email(self):
        response = self.client.post('/register/', {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword'
        }, format='json')
        self.assertEqual(response.status_code, 201)
