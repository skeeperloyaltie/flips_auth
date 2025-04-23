from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import SubscriptionPlan, UserSubscription, PesapalTransaction


class PaymentAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.plan = SubscriptionPlan.objects.create(name="Test Plan", price=10.0)
        self.client = APIClient()
        self.client.login(username="testuser", password="testpassword")

    def test_create_payment_intent(self):
        response = self.client.post(
            "/create-payment-intent/", {"planId": self.plan.id}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("payment_url", response.json())
        self.assertIn("payment_id", response.json())

    def test_payment_callback_success(self):
        transaction = PesapalTransaction.objects.create(
            user=self.user, plan=self.plan, payment_id="123", status="PENDING"
        )
        response = self.client.post(
            "/payment-callback/",
            {
                "pesapal_transaction_tracking_id": "123",
                "user_id": self.user.id,
                "plan_id": self.plan.id,
                "status": "COMPLETED",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, "COMPLETED")

    def test_payment_callback_failure(self):
        transaction = PesapalTransaction.objects.create(
            user=self.user, plan=self.plan, payment_id="123", status="PENDING"
        )
        response = self.client.post(
            "/payment-callback/",
            {
                "pesapal_transaction_tracking_id": "123",
                "user_id": self.user.id,
                "plan_id": self.plan.id,
                "status": "FAILED",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, "FAILED")
