import uuid
import base64
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import PaymentMethod, UserPayment
from subscription.models import SubscriptionPlan, UserSubscription
from userprofile.models import UserProfile
from .serializers import PaymentMethodSerializer, UserPaymentSerializer
from .utils import generate_invoice_pdf, send_invoice_email
import logging
import stripe
import requests
from django.conf import settings
from retrying import retry
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from django.core.mail import send_mail
import re
import os

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

            pdf_path = generate_invoice_pdf(payment)
            send_invoice_email(payment, pdf_path)
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

            try:
                user_profile = user.profile
                if user_profile.phone_number and user_profile.phone_number != phone_number:
                    logger.info(f"STK Push using non-profile phone number for user {user.username}: "
                                f"Provided {phone_number}, Profile {user_profile.phone_number}")
                else:
                    logger.info(f"STK Push using profile phone number for user {user.username}: {phone_number}")
            except UserProfile.DoesNotExist:
                logger.info(f"No UserProfile for user {user.username}, using phone number: {phone_number}")

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

                logger.info(f"Initiating STK Push for user {user.username} with phone {phone_number}")

                stk_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
                headers = {"Authorization": f"Bearer {access_token}"}
                payload = {
                    "BusinessShortCode": settings.MPESA_SHORTCODE,
                    "Password": password,
                    "Timestamp": timestamp,
                    "TransactionType": "CustomerPayBillOnline",
                    "Amount": int(float(amount)),
                    "PartyA": phone_number.replace('+', ''),
                    "PartyB": settings.MPESA_SHORTCODE,
                    "PhoneNumber": phone_number.replace('+', ''),
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

                pdf_path = generate_invoice_pdf(payment)
                send_invoice_email(payment, pdf_path)
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
                        defaults={
                            'active': True,
                            'start_date': timezone.now(),
                            'end_date': timezone.now() + timezone.timedelta(days=payment.plan.duration)
                        }
                    )
                    if not created:
                        subscription.active = True
                        subscription.start_date = timezone.now()
                        subscription.end_date = timezone.now() + timezone.timedelta(days=payment.plan.duration)
                        subscription.save()

                    user_profile, _ = UserProfile.objects.get_or_create(user=user)
                    user_profile.subscription_status = True
                    user_profile.subscription_plan = payment.plan
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
                    defaults={
                        'active': True,
                        'start_date': timezone.now(),
                        'end_date': timezone.now() + timezone.timedelta(days=payment.plan.duration)
                    }
                )
                if not created:
                    subscription.active = True
                    subscription.start_date = timezone.now()
                    subscription.end_date = timezone.now() + timezone.timedelta(days=payment.plan.duration)
                    subscription.save()

                user_profile, _ = UserProfile.objects.get_or_create(user=user)
                user_profile.subscription_status = True
                user_profile.subscription_plan = payment.plan
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

class CheckUserSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get('plan')
        user = request.user

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            logger.error(f"Plan does not exist: {plan_id} for user {user.username}")
            return Response({"error": "Plan does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        active_subscription = UserPayment.objects.filter(
            user=user,
            plan=plan,
            is_verified=True
        ).exists()

        if active_subscription:
            logger.info(f"User {user.username} is actively subscribed to plan {plan.name}")
            return Response({"message": "User is actively subscribed to this plan."}, status=status.HTTP_200_OK)
        else:
            logger.info(f"User {user.username} has no active subscription to plan {plan.name}")
            return Response({"message": "User has not purchased or subscribed to this plan."}, status=status.HTTP_200_OK)

@csrf_exempt
def mpesa_stk_callback(request):
    if request.method == 'POST':
        callback_data = json.loads(request.body.decode('utf-8'))

        body = callback_data.get('Body', {})
        stk_callback = body.get('stkCallback', {})
        checkout_request_id = stk_callback.get('CheckoutRequestID')

        result_code = stk_callback.get('ResultCode')
        result_desc = stk_callback.get('ResultDesc')

        metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
        mpesa_data = {item['Name']: item.get('Value') for item in metadata if 'Value' in item}

        try:
            payment = UserPayment.objects.get(transaction_id=checkout_request_id)

            if result_code == 0:
                payment.status = 'verified'
                payment.is_verified = True
                payment.verified_at = timezone.now()
                payment.amount = mpesa_data.get('Amount', payment.amount)
                payment.transaction_id = mpesa_data.get('MpesaReceiptNumber', checkout_request_id)
                payment.save()

                subscription, created = UserSubscription.objects.get_or_create(
                    user=payment.user,
                    plan=payment.plan,
                    defaults={
                        'active': True,
                        'start_date': timezone.now(),
                        'end_date': timezone.now() + timezone.timedelta(days=payment.plan.duration)
                    }
                )
                if not created:
                    subscription.active = True
                    subscription.start_date = timezone.now()
                    subscription.end_date = timezone.now() + timezone.timedelta(days=payment.plan.duration)
                    subscription.save()

                user_profile, _ = UserProfile.objects.get_or_create(user=payment.user)
                user_profile.subscription_status = True
                user_profile.subscription_plan = payment.plan
                user_profile.expiry_date = subscription.end_date
                user_profile.save()

                logger.info(f"STK callback verified payment and updated subscription for user {payment.user.username} with plan {payment.plan.name}")
                subject = "Payment Successful"
                message = f"Dear {payment.user.first_name},\n\nYour payment of KES {payment.amount} was successfully received.\nTransaction ID: {payment.transaction_id}."
            else:
                payment.status = 'failed'
                subject = "Payment Failed"
                message = f"Dear {payment.user.first_name},\n\nYour payment attempt failed.\nReason: {result_desc}\nPlease try again."

            payment.save()

            # Send email
            if hasattr(payment, 'user') and payment.user.email:
                send_mail(
                    subject,
                    message,
                    'info.flipsinteligence@gmail.com',  # Replace with your sender email
                    [payment.user.email],
                    fail_silently=False
                )

        except UserPayment.DoesNotExist:
            logger.error(f"CheckoutRequestID {checkout_request_id} not found.")

        return JsonResponse({"ResultCode": 0, "ResultDesc": "Received successfully"})

    return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
def mpesa_stk_timeout(request):
    if request.method == 'POST':
        timeout_data = json.loads(request.body.decode('utf-8'))

        logger.warning("M-Pesa timeout callback received: %s", timeout_data)

        # Get the CheckoutRequestID to identify the payment
        checkout_request_id = timeout_data.get('CheckoutRequestID')

        try:
            payment = UserPayment.objects.get(transaction_id=checkout_request_id)
            payment.status = 'timeout'
            payment.save()

            # Optionally notify the user via email
            if hasattr(payment, 'user') and payment.user.email:
                send_mail(
                    subject="Payment Timeout",
                    message=f"Dear {payment.user.first_name},\n\nYour M-Pesa payment attempt timed out. Please try again.",
                    from_email='info.flipsinteligence@gmail.com',
                    recipient_list=[payment.user.email],
                    fail_silently=False
                )

        except UserPayment.DoesNotExist:
            logger.error(f"Timeout: CheckoutRequestID {checkout_request_id} not found.")

        return JsonResponse({"ResultCode": 0, "ResultDesc": "Timeout received successfully"})

    return JsonResponse({"error": "Invalid request"}, status=400)