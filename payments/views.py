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
from django.core.mail import EmailMessage
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import tempfile
import os
import logging
import stripe
import requests
from django.conf import settings
from retrying import retry

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)

class InitiatePaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        plan_id = request.data.get('plan')
        payment_type = request.data.get('payment_type')
        paybill_number = request.data.get('paybill_number')
        account_number = request.data.get('account_number')
        amount = request.data.get('amount')
        transaction_id = request.data.get('transaction_id')
        payment_intent_id = request.data.get('payment_intent_id')

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            logger.error(f"Invalid plan ID: {plan_id} for user {user.username}")
            return Response({"error": "Invalid subscription plan."}, status=status.HTTP_400_BAD_REQUEST)

        active_sub = UserSubscription.objects.filter(user=user, plan=plan, active=True).first()
        if active_sub and active_sub.is_active():
            logger.info(f"User {user.username} already subscribed to {plan.name}")
            return Response({"message": "You are already subscribed to this plan."}, status=status.HTTP_200_OK)

        unique_reference = str(uuid.uuid4())
        payment_data = {
            'user': user,
            'plan': plan,
            'payment_type': payment_type,
            'unique_reference': unique_reference,
            'amount': float(amount) if amount else plan.price,
            'status': 'pending',
        }

        if payment_type == 'card' and payment_intent_id:
            try:
                payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
                if payment_intent.status == 'succeeded':
                    payment_data.update({
                        'status': 'verified',
                        'is_verified': True,
                        'verified_at': timezone.now(),
                        'transaction_id': payment_intent.id
                    })
                else:
                    logger.error(f"PaymentIntent {payment_intent_id} not successful for user {user.username}")
                    return Response({"error": "Card payment failed."}, status=status.HTTP_400_BAD_REQUEST)
            except stripe.error.StripeError as e:
                logger.error(f"Stripe error for user {user.username}: {str(e)}")
                return Response({"error": "Card payment processing failed."}, status=status.HTTP_400_BAD_REQUEST)

        elif payment_type == 'paybill':
            if not all([paybill_number, account_number, amount, transaction_id]):
                logger.error(f"Missing Paybill fields for user {user.username}")
                return Response({"error": "All Paybill fields (paybill_number, account_number, amount, transaction_id) are required."}, status=status.HTTP_400_BAD_REQUEST)

            # Validate transaction_id format (10 alphanumeric characters)
            import re
            if not re.match(r'^[A-Z0-9]{10}$', transaction_id):
                logger.error(f"Invalid transaction ID format: {transaction_id} for user {user.username}")
                return Response({"error": "Transaction ID must be 10 alphanumeric characters (e.g., WSI9K8J2P3)."}, status=status.HTTP_400_BAD_REQUEST)

            payment_data.update({
                'paybill_number': paybill_number,
                'account_number': account_number,
                'transaction_id': transaction_id,
                'amount': float(amount)
            })

        payment = UserPayment.objects.create(**payment_data)
        logger.info(f"Payment initiated for user {user.username} (Ref: {unique_reference}, Type: {payment_type})")

        # For card payments, activate subscription immediately
        if payment_type == 'card' and payment.is_verified:
            subscription, created = UserSubscription.objects.get_or_create(
                user=user,
                plan=plan,
                defaults={'active': True, 'start_date': timezone.now()}
            )
            if not created:
                subscription.active = True
                subscription.start_date = timezone.now()
                subscription.save()

            user_profile, _ = UserProfile.objects.get_or_create(user=user)
            user_profile.subscription_status = True
            user_profile.subscription_plan = plan
            user_profile.subscription_level = plan.name
            user_profile.expiry_date = subscription.end_date
            user_profile.save()

            logger.info(f"Subscription activated for user {user.username} (Plan: {plan.name})")

        pdf_path = self.generate_invoice_pdf(payment)
        self.send_invoice_email(payment, pdf_path)
        os.unlink(pdf_path)

        return Response({
            "message": "Payment initiated successfully.",
            "unique_reference": unique_reference,
            "payment": UserPaymentSerializer(payment).data
        }, status=status.HTTP_201_CREATED)

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
        c.drawString(50, 650, f"Payment Type: {payment.get_payment_type_display()}")
        if payment.payment_type == 'paybill':
            c.drawString(50, 630, f"Paybill Number: {payment.paybill_number}")
            c.drawString(50, 610, f"Account Number: {payment.account_number}")
            c.drawString(50, 590, f"Transaction ID: {payment.transaction_id}")
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
        - Payment Type: {payment.get_payment_type_display()}
        """
        if payment.payment_type == 'paybill':
            message += f"""
        - Paybill Number: {payment.paybill_number}
        - Account Number: {payment.account_number}
        - Transaction ID: {payment.transaction_id}
        """
        message += "\nRegards,\nFLIPS Team"
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
        transaction_id = request.data.get('unique_reference')  # Front-end sends transaction_id as unique_reference
        user = request.user

        try:
            payment = UserPayment.objects.get(
                transaction_id=transaction_id,
                user=user,
                payment_type='paybill'
            )
        except UserPayment.DoesNotExist:
            logger.error(f"Payment not found for user {user.username} (Transaction ID: {transaction_id})")
            return Response({"error": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

        if payment.is_verified:
            logger.info(f"Payment already verified for user {user.username} (Transaction ID: {transaction_id})")
            return Response({"error": "Payment already verified."}, status=status.HTTP_400_BAD_REQUEST)

        # Verify with Daraja API
        try:
            is_valid = self.verify_mpesa_transaction(transaction_id)
            if not is_valid:
                logger.error(f"Invalid M-Pesa transaction for user {user.username}: {transaction_id}")
                return Response({"error": "Invalid transaction ID."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Daraja API error for user {user.username}: {str(e)}")
            return Response({"error": f"Transaction verification failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        payment.is_verified = True
        payment.status = "verified"
        payment.verified_at = timezone.now()
        payment.save()

        subscription, created = UserSubscription.objects.get_or_create(
            user=user,
            plan=payment.plan,
            defaults={'active': True, 'start_date': timezone.now()}
        )
        if not created:
            subscription.active = True
            subscription.start_date = timezone.now()
            subscription.save()

        user_profile, _ = UserProfile.objects.get_or_create(user=user)
        user_profile.subscription_status = True
        user_profile.subscription_plan = payment.plan
        user_profile.subscription_level = payment.plan.name
        user_profile.expiry_date = subscription.end_date
        user_profile.save()

        logger.info(f"Payment verified for user {user.username} (Transaction ID: {transaction_id})")
        return Response({
            "success": "Payment verified successfully.",
            "plan": payment.plan.name,
            "end_date": subscription.end_date
        }, status=status.HTTP_200_OK)

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def verify_mpesa_transaction(self, transaction_id):
        # Daraja API authentication
        auth_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        auth_response = requests.get(
            auth_url,
            auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET)
        )
        auth_response.raise_for_status()
        access_token = auth_response.json().get('access_token')

        # Transaction query
        query_url = "https://sandbox.safaricom.co.ke/mpesa/transactionstatus/v1/query"
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {
            "Initiator": settings.MPESA_INITIATOR_NAME,  # e.g., "testapi"
            "CommandID": "TransactionStatusQuery",
            "TransactionID": transaction_id,
            "PartyA": settings.MPESA_SHORTCODE,
            "IdentifierType": "4",  # Paybill
            "ResultURL": settings.MPESA_RESULT_URL,
            "QueueTimeOutURL": settings.MPESA_TIMEOUT_URL,
            "Remarks": "Verify payment",
            "Occasion": "Subscription"
        }
        response = requests.post(query_url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()

        logger.debug(f"Daraja API response for transaction {transaction_id}: {result}")
        return result.get('ResultCode') == '0'  # Success

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
        user_payments = UserPayment.objects.filter(user=request.user).order_by('-created_at')
        serializer = UserPaymentSerializer(user_payments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class PaymentPageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payment_methods = PaymentMethod.objects.all()
        plans = SubscriptionPlan.objects.all()
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
        return Response(serializer.data)

class CheckUserSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get('plan')
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            logger.error(f"Plan does not exist: {plan_id}")
            return Response({"error": "Plan does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        active_subscription = UserPayment.objects.filter(user=user, plan=plan, is_verified=True).exists()
        if active_subscription:
            return Response({"message": "User is actively subscribed to this plan."}, status=status.HTTP_200_OK)
        return Response({"message": "User has not purchased or subscribed to this plan."}, status=status.HTTP_200_OK)