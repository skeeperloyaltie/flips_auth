import uuid
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import PaymentMethod, UserPayment
from subscription.models import SubscriptionPlan, UserSubscription
from .serializers import PaymentMethodSerializer, UserPaymentSerializer, SubscriptionPlanSerializer
from subscription.views import get_dashboard_url
import os
from django.core.mail import EmailMessage
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import tempfile
from django.utils import timezone
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import UserPayment
from userprofile.models import UserProfile
from subscription.models import SubscriptionPlan
from subscription.views import get_dashboard_url
import logging



from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import UserPayment, SubscriptionPlan  # Ensure SubscriptionPlan is imported
from userprofile.models import UserProfile




import uuid
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import PaymentMethod, UserPayment
from subscription.models import SubscriptionPlan
from .serializers import PaymentMethodSerializer, UserPaymentSerializer, SubscriptionPlanSerializer
from django.core.mail import EmailMessage
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

import uuid
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import PaymentMethod, UserPayment
from subscription.models import SubscriptionPlan, UserSubscription
from userprofile.models import UserProfile
from .serializers import PaymentMethodSerializer, UserPaymentSerializer
import logging
from django.core.mail import EmailMessage
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import tempfile
import os

logger = logging.getLogger(__name__)

class PaymentMethodsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payment_methods = PaymentMethod.objects.all()
        serializer = PaymentMethodSerializer(payment_methods, many=True)
        return Response(serializer.data)

    def post(self, request):
        user = request.user
        plan_id = request.data.get('plan')
        payment_method_id = request.data.get('payment_method')

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            return Response({"error": "Invalid subscription plan."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payment_method = PaymentMethod.objects.get(id=payment_method_id) if payment_method_id else None
        except PaymentMethod.DoesNotExist:
            return Response({"error": "Invalid payment method."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if user already has an active subscription for this plan
        active_sub = UserSubscription.objects.filter(user=user, plan=plan, active=True).first()
        if active_sub and active_sub.is_active():
            return Response({"message": "You are already subscribed to this plan."}, status=status.HTTP_200_OK)

        # Create payment record
        unique_reference = str(uuid.uuid4())
        payment = UserPayment.objects.create(
            user=user,
            payment_method=payment_method,
            plan=plan,
            unique_reference=unique_reference,
            amount=plan.price,
            status="pending",
        )

        logger.info(f"Payment initiated for user {user.username} (Ref: {unique_reference}).")
        self.generate_and_send_invoice(payment)

        return Response({
            "message": "Payment initiated successfully.",
            "unique_reference": unique_reference,
            "payment": UserPaymentSerializer(payment).data
        }, status=status.HTTP_201_CREATED)

    def generate_and_send_invoice(self, payment):
        pdf_path = self.generate_invoice_pdf(payment)
        self.send_invoice_email(payment, pdf_path)
        os.unlink(pdf_path)

    def generate_invoice_pdf(self, payment):
        pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, 750, "Payment Invoice")
        c.setFont("Helvetica", 12)
        c.drawString(50, 730, f"Invoice ID: {payment.unique_reference}")
        c.drawString(50, 710, f"Plan: {payment.plan.name}")
        c.drawString(50, 690, f"Amount: KES {payment.amount}")
        c.drawString(50, 670, f"User: {payment.user.username}")
        c.save()
        return pdf_path

    def send_invoice_email(self, payment, pdf_path):
        subject = "Payment Invoice"
        message = f"""
        Dear {payment.user.get_full_name() or payment.user.username},

        Thank you for initiating your payment. Please find your invoice attached.

        Payment Details:
        - Plan: {payment.plan.name}
        - Amount: KES {payment.amount}
        - Invoice ID: {payment.unique_reference}

        Regards,
        FLIPS Team
        """
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email="flipsintelligence@gmail.com",
            to=[payment.user.email],
        )
        email.attach_file(pdf_path)
        email.send()
        logger.info(f"Invoice email sent to {payment.user.email} for payment {payment.unique_reference}")

class VerifyPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        unique_reference = request.data.get('unique_reference')
        try:
            payment = UserPayment.objects.get(unique_reference=unique_reference, user=request.user)

            if payment.is_verified:
                return Response({"error": "Payment already verified."}, status=status.HTTP_400_BAD_REQUEST)

            # Verify payment
            payment.is_verified = True
            payment.status = "verified"
            payment.verified_at = timezone.now()
            payment.save()

            # Create or update UserSubscription
            subscription, created = UserSubscription.objects.get_or_create(
                user=payment.user,
                plan=payment.plan,
                defaults={'active': True}
            )
            if not created:
                subscription.active = True
                subscription.start_date = timezone.now()
                subscription.save()

            # Update UserProfile
            user_profile, _ = UserProfile.objects.get_or_create(user=payment.user)
            user_profile.subscription_status = True
            user_profile.subscription_plan = payment.plan
            user_profile.subscription_level = payment.plan.name
            user_profile.expiry_date = subscription.end_date
            user_profile.save()

            logger.info(f"Payment verified and subscription activated for user {payment.user.username} (Ref: {unique_reference}).")

            return Response({
                "success": "Payment verified successfully.",
                "plan": payment.plan.name,
                "end_date": subscription.end_date
            }, status=status.HTTP_200_OK)

        except UserPayment.DoesNotExist:
            return Response({"error": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error verifying payment: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserSubscriptionStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        subscription = UserSubscription.objects.filter(user=user, active=True).first()
        if subscription and subscription.is_active():
            return Response({
                "isSubscribed": True,
                "plan": subscription.plan.name,
                "end_date": subscription.end_date
            }, status=status.HTTP_200_OK)
        return Response({"isSubscribed": False}, status=status.HTTP_200_OK)




class UserPaymentHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Fetch payment history for the authenticated user.
        """
        user_payments = UserPayment.objects.filter(user=request.user).order_by('-created_at')
        serializer = UserPaymentSerializer(user_payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class PaymentPageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payment_methods = PaymentMethod.objects.all()
        plans = SubscriptionPlan.objects.all()  # Fetch SubscriptionPlans from subscriptions app

        payment_methods_serializer = PaymentMethodSerializer(payment_methods, many=True)
        plans_serializer = SubscriptionPlanSerializer(plans, many=True)

        return Response({
            'payment_methods': payment_methods_serializer.data,
            'plans': plans_serializer.data
        })


class VerificationPageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_payments = UserPayment.objects.filter(user=request.user, is_verified=False)
        serializer = UserPaymentSerializer(user_payments, many=True)
        return Response(serializer.data)  # Return the list of user payments directly


class CheckUserSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get('plan')
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            return Response({"error": "Plan does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        # Check if the user has an active subscription to this plan
        active_subscription = UserPayment.objects.filter(user=user, plan=plan, is_verified=True).exists()
        if active_subscription:
            return Response({"message": "User is actively subscribed to this plan."}, status=status.HTTP_200_OK)

        return Response({"message": "User has not purchased or subscribed to this plan."}, status=status.HTTP_200_OK)




class UserPaymentHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Fetch payment history for the authenticated user.
        """
        user_payments = UserPayment.objects.filter(user=request.user).order_by('-created_at')
        serializer = UserPaymentSerializer(user_payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
