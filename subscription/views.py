import logging
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import SubscriptionPlan, UserSubscription
from payments.models import UserPayment
from .serializers import SubscriptionPlanSerializer
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
import uuid


logger = logging.getLogger(__name__)

class SubscriptionPlanListCreateView(generics.ListCreateAPIView):
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [IsAuthenticated]
    queryset = SubscriptionPlan.objects.all()

class SubscriptionPlanDetailView(generics.RetrieveAPIView):
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [IsAuthenticated]
    queryset = SubscriptionPlan.objects.all()
    lookup_field = 'id'

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_user_subscription(request):
    user = request.user
    subscription = UserSubscription.objects.filter(user=user, active=True).first()
    if subscription and subscription.is_active():
        return Response({
            'isSubscribed': True,
            'planName': subscription.plan.name,
            'endDate': subscription.end_date.isoformat()  # Ensure ISO format for frontend
        }, status=status.HTTP_200_OK)
    return Response({
        'isSubscribed': False,
        'message': 'No active subscription found.'
    }, status=status.HTTP_200_OK)

from decimal import Decimal
import logging
import tempfile
import os

logger = logging.getLogger(__name__)

from decimal import Decimal
import logging
import uuid
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import SubscriptionPlan, UserSubscription
from payments.models import UserPayment
from payments.utils import generate_invoice_pdf, send_invoice_email  # Import utility functions
from rest_framework.permissions import IsAuthenticated
import os

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def subscribe(request):
    plan_id = request.data.get('planId')
    user = request.user
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)

    logger.info(f"Processing subscription for user {user.username}, plan_id={plan_id}, plan_name={plan.name}, plan_price={plan.price}, price_type={type(plan.price)}")

    # Check for existing active subscription
    current_subscription = UserSubscription.objects.filter(user=user, active=True).first()
    if current_subscription and current_subscription.is_active():
        if current_subscription.plan.id == plan_id:
            return Response({
                'message': 'You are already subscribed to this plan.'
            }, status=status.HTTP_200_OK)
        current_subscription.active = False
        current_subscription.save()

    # Check if the plan is free
    is_free_plan = plan.price == 0 or plan.price == Decimal('0.00')

    if is_free_plan:
        # Create subscription for free plan
        subscription = UserSubscription.objects.create(
            user=user,
            plan=plan,
            active=True,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=14)
        )

        # Create payment record for free plan
        unique_reference = str(uuid.uuid4())
        transaction_id = f"FREE-{unique_reference[:10].upper()}"  # Generate a unique transaction ID
        payment = UserPayment.objects.create(
            user=user,
            plan=plan,
            payment_type='free',
            unique_reference=unique_reference,
            transaction_id=transaction_id,
            amount=0.0,
            status='verified',
            is_verified=True,
            verified_at=timezone.now(),
            paybill_number='',
            account_number='',
        )
        logger.info(f"Free payment record created for user {user.username}, plan {plan.name}, unique_reference={unique_reference}, transaction_id={transaction_id}")

        # Generate and send invoice
        try:
            pdf_path = generate_invoice_pdf(payment)
            send_invoice_email(payment, pdf_path)
            os.unlink(pdf_path)
            logger.info(f"Invoice sent for free subscription for user {user.username}, plan {plan.name}")
        except Exception as e:
            logger.error(f"Failed to generate or send invoice for user {user.username}: {str(e)}")
            # Optionally, you can decide whether to fail the subscription or proceed
            # Here, we proceed but log the error
            pass

        logger.info(f"Free subscription created for user {user.username} with plan {plan.name}, active={subscription.active}, start_date={subscription.start_date}, end_date={subscription.end_date}")
        return Response({
            'message': 'Successfully subscribed to the free plan for 14 days.',
            'plan_id': plan_id,
            'subscription_id': subscription.id,
            'payment_reference': unique_reference
        }, status=status.HTTP_201_CREATED)
    else:
        # For paid plans, do not create subscription or payment yet
        logger.info(f"Paid plan selected for user {user.username}, plan {plan.name}. Awaiting payment initiation.")
        return Response({
            'message': 'Please complete payment to activate subscription.',
            'plan_id': plan_id
        }, status=status.HTTP_202_ACCEPTED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_url(request):
    user = request.user
    subscription = UserSubscription.objects.filter(user=user, active=True).first()
    if subscription and subscription.is_active():
        plan_name = subscription.plan.name.lower().replace(' ', '-')
        return Response({
            'url': f'/dashboard/{plan_name}/index.html'  # Updated to relative path
        }, status=status.HTTP_200_OK)
    return Response({
        'url': '/dashboard/no-subscription/index.html'
    }, status=status.HTTP_400_BAD_REQUEST)

class SubscriptionDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        logger.info(f"User {user.username} accessing subscription details.")
        subscription = UserSubscription.objects.filter(user=user, active=True).first()

        if subscription and subscription.is_active():
            plan = subscription.plan
            payment_verified = UserPayment.objects.filter(
                user=user, plan=plan, is_verified=True
            ).exists()
            if payment_verified:
                services = (
                    ["Basic Access"] if plan.name == "free" else
                    ["Real-time Alerts", "Basic Analytics", "Limited Historical Data"] if plan.name == "corporate" else
                    ["Advanced Analytics", "Full Historical Data", "Custom Reports", "Real-time Alerts"]
                )
                historical_data_days = 1 if plan.name == "free" else 7 if plan.name == "corporate" else 14
                report_count = "N/A" if plan.name == "free" else "Weekly" if plan.name == "corporate" else "Monthly"

                details = {
                    "tier": plan.name,
                    "services": services,
                    "usage_limits": {
                        "historical_data_days": historical_data_days,
                        "report_count": report_count
                    },
                    "pricing": f"KES {plan.price}/month" if plan.price > 0 else "Free",
                    "start_date": subscription.start_date.isoformat(),
                    "end_date": subscription.end_date.isoformat() if subscription.end_date else None
                }
                logger.info(f"Subscription details for user {user.username}: {details}")
                return Response(details, status=status.HTTP_200_OK)
            logger.warning(f"Payment pending for user {user.username} for plan {plan.name}.")
            return Response({
                "message": "Payment is pending for the current subscription."
            }, status=status.HTTP_403_FORBIDDEN)
        logger.warning(f"No active subscription for user {user.username}.")
        return Response({
            "message": "No active subscription found."
        }, status=status.HTTP_404_NOT_FOUND)

class UpgradePromptView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        logger.debug(f"User {user.username} accessing upgrade options.")
        verified_payments = UserPayment.objects.filter(user=user, is_verified=True)

        if verified_payments.exists():
            latest_payment = verified_payments.latest('created_at')
            current_plan = latest_payment.plan
            available_upgrades = SubscriptionPlan.objects.filter(price__gt=current_plan.price)
            logger.info(f"User {user.username} eligible for {available_upgrades.count()} upgrades.")
            serializer = SubscriptionPlanSerializer(available_upgrades, many=True)
            return Response({
                "available_upgrades": serializer.data
            }, status=status.HTTP_200_OK)

        available_upgrades = SubscriptionPlan.objects.exclude(name="free")
        logger.warning(f"No verified payments for user {user.username}. Showing all plans except 'free'.")
        serializer = SubscriptionPlanSerializer(available_upgrades, many=True)
        return Response({
            "available_upgrades": serializer.data
        }, status=status.HTTP_200_OK)