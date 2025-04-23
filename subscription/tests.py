from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import SubscriptionPlan, UserSubscription, PesapalTransaction


class SubscriptionAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.client = APIClient()
        self.client.login(username="testuser", password="testpassword")

        self.plan = SubscriptionPlan.objects.create(
            name="Test Plan", price=10.00, description="Sample plan description"
        )

    def test_subscribe(self):
        response = self.client.post(
            "/subscription/subscribe/", {"planId": self.plan.id}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            UserSubscription.objects.filter(user=self.user, plan=self.plan).count(), 1
        )

    def test_check_user_subscription(self):
        UserSubscription.objects.create(user=self.user, plan=self.plan, active=True)
        response = self.client.get("/subscription/status/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["isSubscribed"])

    def test_get_dashboard_url(self):
        UserSubscription.objects.create(user=self.user, plan=self.plan, active=True)
        response = self.client.get("/subscription/get-dashboard-url/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("url", response.data)
