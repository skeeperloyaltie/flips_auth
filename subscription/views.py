from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .models import SubscriptionPlan, UserSubscription
from payments.models import UserPayment
from .serializers import SubscriptionPlanSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
import logging

logger = logging.getLogger(__name__)

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import SubscriptionPlan, UserSubscription
from payments.models import UserPayment
from .serializers import SubscriptionPlanSerializer
from rest_framework.permissions import IsAuthenticated
import logging

logger = logging.getLogger(__name__)

class SubscriptionPlanListCreateView(generics.ListCreateAPIView):
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SubscriptionPlan.objects.all()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_user_subscription(request):
    user = request.user
    subscription = UserSubscription.objects.filter(user=user, active=True).first()

    if subscription and subscription.is_active():
        return Response({
            'isSubscribed': True,
            'planName': subscription.plan.name,
            'endDate': subscription.end_date
        }, status=status.HTTP_200_OK)
    return Response({'isSubscribed': False, 'message': 'No active subscription found.'}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def subscribe(request):
    plan_id = request.data.get('planId')
    user = request.user
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)

    # Check existing subscription
    current_subscription = UserSubscription.objects.filter(user=user, active=True).first()
    if current_subscription and current_subscription.is_active():
        if current_subscription.plan.id == plan_id:
            return Response({'message': 'You are already subscribed to this plan.'}, status=status.HTTP_200_OK)
        else:
            current_subscription.active = False
            current_subscription.save()

    # Subscription is handled via payment; redirect to payment flow
    return Response({'message': 'Please complete payment to activate subscription.', 'plan_id': plan_id}, status=status.HTTP_202_ACCEPTED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_url(request):
    user = request.user
    subscription = UserSubscription.objects.filter(user=user, active=True).first()

    if subscription and subscription.is_active():
        plan_name = subscription.plan.name.lower().replace(' ', '-')
        return Response({'url': f'{plan_name}/index.html'}, status=status.HTTP_200_OK)
    return Response({'url': 'no-subscription/index.html'}, status=status.HTTP_400_BAD_REQUEST)




import logging
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import SubscriptionPlan
from payments.models import UserPayment

# Configure logging
logger = logging.getLogger(__name__)

class SubscriptionDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        logger.info(f"User {user.username} (ID: {user.id}) accessing subscription details.")

        # Fetch the user's profile to get subscription details
        user_profile = user.profile  # Accessing the UserProfile associated with the user

        if user_profile.subscription_plan:
            plan = user_profile.subscription_plan
            logger.debug(f"User {user.username} has subscription plan: {plan.name}")

            payment_verified = UserPayment.objects.filter(user=user, plan=plan, is_verified=True).exists()
            logger.debug(f"Payment verified for User {user.username}: {payment_verified}")

            if payment_verified:
                # Return details of the user's specific plan if payment is verified
                logger.info(f"User {user.username} has a verified payment for plan: {plan.name}.")
                return Response(self.format_plan_details([plan])[0], status=status.HTTP_200_OK)
            else:
                logger.warning(f"Payment pending for User {user.username} for plan: {plan.name}.")
                return Response({"message": "Payment is pending for the current subscription."},
                                status=status.HTTP_403_FORBIDDEN)
        else:
            logger.warning(f"No active subscription found for User {user.username}.")
            return Response({"message": "No active subscription found."},
                            status=status.HTTP_404_NOT_FOUND)

    def format_plan_details(self, plans):
        plan_details = []
        for plan in plans:
            services = ["Basic Access"] if plan.name == "Free" else ["Real-time Alerts", "Basic Analytics", "Limited Historical Data"] if plan.name == "Corporate" else ["Advanced Analytics", "Full Historical Data", "Custom Reports", "Real-time Alerts"]
            historical_data_days = 1 if plan.name == "Free" else 7 if plan.name == "Corporate" else 14
            report_count = "N/A" if plan.name == "Free" else "Weekly" if plan.name == "Corporate" else "Monthly"

            details = {
                "tier": plan.name,
                "services": services,
                "usage_limits": {
                    "historical_data_days": historical_data_days,
                    "report_count": report_count
                },
                "pricing": f"KES {plan.price}/month" if plan.price > 0 else "Free"
            }
            plan_details.append(details)
        
        logger.debug(f"Formatted plan details: {plan_details}")
        return plan_details


import logging
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import SubscriptionPlan
from payments.models import UserPayment
from .serializers import SubscriptionPlanSerializer

logger = logging.getLogger(__name__)

class UpgradePromptView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        logger.debug(f"User {user.username} (ID: {user.id}) attempting to access upgrade options.")

        # Fetch all verified payments for the user
        verified_payments = UserPayment.objects.filter(user=user, is_verified=True)

        if verified_payments.exists():
            logger.debug(f"User {user.username} has verified payments: {verified_payments.count()} found.")

            # Get the latest payment's associated plan
            latest_payment = verified_payments.last()
            current_plan = latest_payment.plan
            
            logger.debug(f"Current plan for user {user.username}: {current_plan.name}")

            # Allow viewing upgrade options for all plans
            available_upgrades = SubscriptionPlan.objects.filter(price__gt=current_plan.price)
            logger.info(f"User {user.username} is eligible for upgrades: {available_upgrades.count()} plans available.")
            serializer = SubscriptionPlanSerializer(available_upgrades, many=True)
            return Response({
                "available_upgrades": serializer.data
            }, status=status.HTTP_200_OK)

        else:
            logger.warning(f"No verified payments found for User {user.username}. Showing available plans excluding 'Free'.")
            # If the user has no verified payments, show all plans excluding "Free" as upgrade options
            available_upgrades = SubscriptionPlan.objects.exclude(name="Free")
            serializer = SubscriptionPlanSerializer(available_upgrades, many=True)
            return Response({
                "available_upgrades": serializer.data
            }, status=status.HTTP_200_OK)

    def get_addons_for_government_user(self, user):
        logger.debug(f"Fetching addons for government user: {user.username}")
        # Define what addons are available for government users
        addons = SubscriptionPlan.objects.filter(is_addon=True)  # Assuming is_addon is a field in your SubscriptionPlan model
        logger.debug(f"Found {addons.count()} addons for government user: {user.username}")
        serializer = SubscriptionPlanSerializer(addons, many=True)
        return serializer.data



