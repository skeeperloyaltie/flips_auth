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

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            logger.error(f"Invalid plan ID: {plan_id} for user {user.username}")
            return Response({"error": "Invalid subscription plan."}, status=status.HTTP_400_BAD_REQUEST)

        active_sub = UserSubscription.objects.filter(user=user, plan=plan, active=True).first()
        if active_sub and active_sub.is_active():
            logger.info(f"User {user.username} already subscribed to {plan.name}")
            return Response({"message": "You are already subscribed to this plan."}, status=status.HTTP_200_OK)

        if payment_type == 'card':
            try:
                payment_intent = stripe.PaymentIntent.create(
                    amount=int(plan.price * 100),  # Convert to cents
                    currency='kes',
                    metadata={'user_id': user.id, 'plan_id': plan_id}
                )
                logger.info(f"Stripe PaymentIntent created for user {user.username}: {payment_intent.id}")
                return Response({
                    "message": "Card payment initiated.",
                    "client_secret": payment_intent.client_secret,
                    "payment_intent_id": payment_intent.id
                }, status=status.HTTP_200_OK)
            except stripe.error.StripeError as e:
                logger.error(f"Stripe error for user {user.username}: {str(e)}")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        elif payment_type == 'paybill':
            if not all([paybill_number, account_number, amount, transaction_id]):
                logger.error(f"Missing Paybill fields for user {user.username}")
                return Response({"error": "All Paybill fields (paybill_number, account_number, amount, transaction_id) are required."}, status=status.HTTP_400_BAD_REQUEST)

            import re
            if not re.match(r'^[A-Z0-9]{10}$', transaction_id):
                logger.error(f"Invalid transaction ID format: {transaction_id} for user {user.username}")
                return Response({"error": "Transaction ID must be 10 alphanumeric characters (e.g., WSI9K8J2P3)."}, status=status.HTTP_400_BAD_REQUEST)

            if float(amount) != float(plan.price):
                logger.error(f"Amount mismatch for user {user.username}: {amount} != {plan.price}")
                return Response({"error": "Amount must match plan price."}, status=status.HTTP_400_BAD_REQUEST)

            unique_reference = transaction_id
            payment_data = {
                'user': user,
                'plan': plan,
                'payment_type': 'paybill',
                'unique_reference': unique_reference,
                'transaction_id': transaction_id,
                'paybill_number': paybill_number,
                'account_number': account_number,
                'amount': float(amount),
                'status': 'pending',
            }

            payment = UserPayment.objects.create(**payment_data)
            logger.info(f"Paybill payment initiated for user {user.username} (Ref: {unique_reference})")

            pdf_path = self.generate_invoice_pdf(payment)
            self.send_invoice_email(payment, pdf_path)
            os.unlink(pdf_path)

            return Response({
                "message": "Paybill payment initiated successfully. Please verify your payment.",
                "unique_reference": unique_reference,
                "payment": UserPaymentSerializer(payment).data
            }, status=status.HTTP_201_CREATED)

        elif payment_type == 'stk_push':
            if not account_number:
                logger.error(f"Missing phone number for STK Push for user {user.username}")
                return Response({"error": "Phone number is required for STK Push."}, status=status.HTTP_400_BAD_REQUEST)

            # Normalize and validate phone number
            phone_number = account_number.strip()
            import re
            # Match formats: +2547XXXXXXXX, 07XXXXXXXX, 7XXXXXXXX
            if re.match(r'^\+2547[0-1][0-9]{7}$', phone_number):
                pass  # Already in correct format
            elif re.match(r'^07[0-1][0-9]{7}$', phone_number):
                phone_number = '+254' + phone_number[1:]
            elif re.match(r'^7[0-1][0-9]{7}$', phone_number):
                phone_number = '+254' + phone_number
            else:
                logger.error(f"Invalid phone number format: {phone_number} for user {user.username}")
                return Response({
                    "error": "Phone number must be in format +2547XXXXXXXX, 07XXXXXXXX, or 7XXXXXXXX."
                }, status=status.HTTP_400_BAD_REQUEST)

            # Verify phone number matches UserProfile (optional, for security)
            try:
                user_profile = user.profile
                if user_profile.phone_number and user_profile.phone_number != phone_number:
                    logger.warning(f"Phone number mismatch for user {user.username}: "
                                 f"Provided {phone_number}, Profile {user_profile.phone_number}")
                    return Response({
                        "error": "Provided phone number does not match your profile."
                    }, status=status.HTTP_400_BAD_REQUEST)
            except UserProfile.DoesNotExist:
                logger.warning(f"No UserProfile for user {user.username}")

            if float(amount) != float(plan.price):
                logger.error(f"Amount mismatch for user {user.username}: {amount} != {plan.price}")
                return Response({"error": "Amount must match plan price."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                # Get OAuth token
                auth_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
                auth_response = requests.get(
                    auth_url,
                    auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET)
                )
                auth_response.raise_for_status()
                access_token = auth_response.json().get('access_token')

                # Generate timestamp and password for STK Push
                timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
                password = base64.b64encode(
                    (settings.MPESA_SHORTCODE + settings.MPESA_PASSKEY + timestamp).encode()
                ).decode()

                # Log the phone number used
                logger.info(f"Initiating STK Push for user {user.username} with phone {phone_number}")

                # Initiate STK Push
                stk_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
                headers = {"Authorization": f"Bearer {access_token}"}
                payload = {
                    "BusinessShortCode": settings.MPESA_SHORTCODE,
                    "Password": password,
                    "Timestamp": timestamp,
                    "TransactionType": "CustomerPayBillOnline",
                    "Amount": int(float(amount)),  # Ensure integer amount
                    "PartyA": phone_number.replace('+', ''),  # e.g., 254700123456
                    "PartyB": settings.MPESA_SHORTCODE,
                    "PhoneNumber": phone_number.replace('+', ''),  # Same as PartyA
                    "CallBackURL": settings.MPESA_RESULT_URL,
                    "AccountReference": f"FLIPS_{plan.id}",
                    "TransactionDesc": f"Payment for {plan.name}"
                }

                response = requests.post(stk_url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                logger.debug(f"STK Push response for user {user.username}: {result}")

                if result.get('ResponseCode') != '0':
                    logger.error(f"STK Push failed for user {user.username}: {result.get('ResponseDescription')}")
                    return Response({
                        "error": f"STK Push failed: {result.get('ResponseDescription')}"
                    }, status=status.HTTP_400_BAD_REQUEST)

                checkout_request_id = result.get('CheckoutRequestID')
                unique_reference = checkout_request_id

                payment_data = {
                    'user': user,
                    'plan': plan,
                    'payment_type': 'stk_push',
                    'unique_reference': unique_reference,
                    'transaction_id': checkout_request_id,
                    'paybill_number': settings.MPESA_SHORTCODE,
                    'account_number': phone_number,
                    'amount': float(amount),
                    'status': 'pending',
                }

                payment = UserPayment.objects.create(**payment_data)
                logger.info(f"STK Push payment initiated for user {user.username} (Ref: {unique_reference})")

                pdf_path = self.generate_invoice_pdf(payment)
                self.send_invoice_email(payment, pdf_path)
                os.unlink(pdf_path)

                return Response({
                    "message": f"STK Push initiated successfully to {phone_number}. Please check your phone to complete the payment.",
                    "unique_reference": unique_reference,
                    "payment": UserPaymentSerializer(payment).data
                }, status=status.HTTP_201_CREATED)

            except requests.exceptions.RequestException as e:
                logger.error(f"Daraja API error for STK Push for user {user.username}: {str(e)}")
                return Response({"error": f"Failed to initiate STK Push: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.error(f"Invalid payment type for user {user.username}: {payment_type}")
        return Response({"error": "Invalid payment type."}, status=status.HTTP_400_BAD_REQUEST)


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
        if payment.payment_type in ['paybill', 'stk_push']:
            c.drawString(50, 630, f"Paybill Number: {payment.paybill_number}")
            c.drawString(50, 610, f"Account Number: {payment.account_number}")
            if payment.payment_type == 'paybill':
                c.drawString(50, 590, f"Transaction ID: {payment.transaction_id}")
            else:
                c.drawString(50, 590, f"Checkout Request ID: {payment.transaction_id}")
        c.save()
        return pdf_path

    def send_invoice_email(self, payment, pdf_path):
        subject = "FLIPS Payment Invoice"
        message = f"""
            Dear {payment.user.get_full_name() or payment.user.username},

            Thank you for initiating your payment for the {payment.plan.name} plan. Please find your invoice attached.

            Payment Details:
            - Plan: {payment.plan.name}
            - Amount: KES {payment.amount}
            - Invoice ID: {payment.unique_reference}
            - Payment Type: {payment.get_payment_type_display()}
            """
                    if payment.payment_type in ['paybill', 'stk_push']:
                        message += f"""
            - Paybill Number: {payment.paybill_number}
            - Account Number: {payment.account_number}
            """
            if payment.payment_type == 'paybill':
                message += f"- Transaction ID: {payment.transaction_id}\n"
            else:
                message += f"- Checkout Request ID: {payment.transaction_id}\n"
                message += "Please check your phone to complete the STK Push payment.\n"
            message += "Please verify your payment using the Transaction ID in the verification portal.\n"
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
        unique_reference = request.data.get('unique_reference')
        user = request.user

        try:
            payment = UserPayment.objects.get(
                unique_reference=unique_reference,
                user=user
            )
        except UserPayment.DoesNotExist:
            logger.error(f"Payment not found for user {user.username} (Ref: {unique_reference})")
            return Response({"error": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

        if payment.is_verified:
            logger.info(f"Payment already verified for user {user.username} (Ref: {unique_reference})")
            return Response({"message": "Payment already verified."}, status=status.HTTP_400_BAD_REQUEST)

        if payment.payment_type == 'card':
            try:
                payment_intent = stripe.PaymentIntent.retrieve(payment.transaction_id)
                if payment_intent.status == 'succeeded':
                    payment.is_verified = True
                    payment.status = 'verified'
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

                    logger.info(f"Card payment verified for user {user.username} (Ref: {unique_reference})")
                    return Response({
                        "success": "Card payment verified successfully.",
                        "plan": payment.plan.name,
                        "end_date": subscription.end_date.isoformat()
                    }, status=status.HTTP_200_OK)
                else:
                    logger.error(f"Card payment not succeeded for user {user.username}: {payment_intent.status}")
                    return Response({"error": "Card payment not completed."}, status=status.HTTP_400_BAD_REQUEST)
            except stripe.error.StripeError as e:
                logger.error(f"Stripe error for user {user.username}: {str(e)}")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        elif payment.payment_type in ['paybill', 'stk_push']:
            try:
                is_valid = self.verify_mpesa_transaction(payment.transaction_id)
                if not is_valid:
                    logger.error(f"Invalid M-Pesa transaction for user {user.username}: {payment.transaction_id}")
                    return Response({"error": "Invalid transaction ID."}, status=status.HTTP_400_BAD_REQUEST)

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

                logger.info(f"{payment.payment_type.capitalize()} payment verified for user {user.username} (Ref: {unique_reference})")
                return Response({
                    "success": f"{payment.payment_type.capitalize()} payment verified successfully.",
                    "plan": payment.plan.name,
                    "end_date": subscription.end_date.isoformat()
                }, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error(f"Daraja API error for user {user.username}: {str(e)}")
                return Response({"error": f"Transaction verification failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.error(f"Invalid payment type for user {user.username}: {payment.payment_type}")
        return Response({"error": "Invalid payment type."}, status=status.HTTP_400_BAD_REQUEST)

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def verify_mpesa_transaction(self, transaction_id):
        auth_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        auth_response = requests.get(
            auth_url,
            auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET)
        )
        auth_response.raise_for_status()
        access_token = auth_response.json().get('access_token')

        query_url = "https://sandbox.safaricom.co.ke/mpesa/transactionstatus/v1/query"
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {
            "Initiator": settings.MPESA_INITIATOR_NAME,
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
        return result.get('ResultCode') == '0'

class PaymentMethodListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payment_methods = PaymentMethod.objects.all()
        serializer = PaymentMethodSerializer(payment_methods, many=True)
        return Response(serializer.data)
    
class UserSubscriptionStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        subscription = UserSubscription.objects.filter(user=user, active=True).first()
        if subscription and subscription.is_active():
            return Response({
                "isSubscribed": True,
                "plan": subscription.plan.name,
                "end_date": subscription.end_date.isoformat()
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