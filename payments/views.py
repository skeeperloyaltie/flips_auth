import uuid
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import PaymentMethod, UserPayment
from subscription.models import SubscriptionPlan, UserSubscription
from userprofile.models import UserProfile
from .serializers import PaymentMethodSerializer, UserPaymentSerializer, SubscriptionPlanSerializer
from django.core.mail import EmailMessage
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import tempfile
import os
import logging
import stripe
from django.conf import settings

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY  # Add to settings.py

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
        payment_type = request.data.get('payment_type', 'mpesa')
        payment_method_id = request.data.get('payment_method')
        payment_intent_id = request.data.get('payment_intent_id')  # For card payments

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            logger.error(f"Invalid subscription plan ID: {plan_id}")
            return Response({"error": "Invalid subscription plan."}, status=status.HTTP_400_BAD_REQUEST)

        # Check active subscription
        active_sub = UserSubscription.objects.filter(user=user, plan=plan, active=True).first()
        if active_sub and active_sub.is_active():
            logger.info(f"User {user.username} already subscribed to plan {plan.name}")
            return Response({"message": "You are already subscribed to this plan."}, status=status.HTTP_200_OK)

        unique_reference = str(uuid.uuid4())
        payment_data = {
            'user': user,
            'plan': plan,
            'payment_type': payment_type,
            'unique_reference': unique_reference,
            'amount': plan.price,
            'status': 'pending',
        }

        if payment_type == 'card' and payment_intent_id:
            try:
                payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
                if payment_intent.status == 'succeeded':
                    payment_data['status'] = 'verified'
                    payment_data['is_verified'] = True
                    payment_data['verified_at'] = timezone.now()
                    payment_data['transaction_id'] = payment_intent.id
                else:
                    logger.error(f"PaymentIntent {payment_intent_id} not successful for user {user.username}")
                    return Response({"error": "Card payment failed."}, status=status.HTTP_400_BAD_REQUEST)
            except stripe.error.StripeError as e:
                logger.error(f"Stripe error for user {user.username}: {str(e)}")
                return Response({"error": "Card payment processing failed."}, status=status.HTTP_400_BAD_REQUEST)
        elif payment_type == 'mpesa':
            try:
                payment_method = PaymentMethod.objects.get(id=payment_method_id) if payment_method_id else None
                payment_data['payment_method'] = payment_method
            except PaymentMethod.DoesNotExist:
                logger.error(f"Invalid payment method ID: {payment_method_id}")
                return Response({"error": "Invalid payment method."}, status=status.HTTP_400_BAD_REQUEST)

        # Create payment record
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

        # Generate and send invoice
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
                logger.info(f"Payment already verified for user {request.user.username} (Ref: {unique_reference})")
                return Response({"error": "Payment already verified."}, status=status.HTTP_400_BAD_REQUEST)

            # For card payments, verification is automatic
            if payment.payment_type == 'card':
                logger.info(f"Card payment already verified for user {request.user.username} (Ref: {unique_reference})")
                return Response({"success": "Card payment already verified."}, status=status.HTTP_200_OK)

            # Verify M-Pesa payment
            payment.is_verified = True
            payment.status = "verified"
            payment.verified_at = timezone.now()
            payment.save()

            # Create or update UserSubscription
            subscription, created = UserSubscription.objects.get_or_create(
                user=payment.user,
                plan=payment.plan,
                defaults={'active': True, 'start_date': timezone.now()}
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

            logger.info(f"Payment verified and subscription activated for user {payment.user.username} (Ref: {unique_reference})")

            return Response({
                "success": "Payment verified successfully.",
                "plan": payment.plan.name,
                "end_date": subscription.end_date
            }, status=status.HTTP_200_OK)

        except UserPayment.DoesNotExist:
            logger.error(f"Payment not found for user {request.user.username} (Ref: {unique_reference})")
            return Response({"error": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error verifying payment for user {request.user.username}: {str(e)}")
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