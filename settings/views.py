from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from userprofile.models import UserProfile
from subscription.models import SubscriptionPlan, UserSubscription
from userprofile.serializers import UserProfileSerializer, UpdateUserSerializer
from subscription.serializers import SubscriptionPlanSerializer

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def settings_view(request):
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    user_subscriptions = UserSubscription.objects.filter(user=user, active=True)
    print(request.user.get_all_permissions())

    if request.method == 'GET':
        # Serialize user profile
        profile_serializer = UserProfileSerializer(user_profile)
        
        # Serialize active subscriptions
        subscriptions_serializer = SubscriptionPlanSerializer([sub.plan for sub in user_subscriptions], many=True)
        
        # Handle case if there are no active subscriptions
        if user_subscriptions.exists():
            # Check for recommended plans (any higher than the first active plan)
            current_plan_price = user_subscriptions[0].plan.price
            recommended_plans = SubscriptionPlan.objects.filter(price__gt=current_plan_price)
        else:
            # If no active subscriptions, recommend all plans
            recommended_plans = SubscriptionPlan.objects.all()
        
        recommended_serializer = SubscriptionPlanSerializer(recommended_plans, many=True)

        return Response({
            'profile': profile_serializer.data,
            'active_subscriptions': subscriptions_serializer.data,
            'recommended_plans': recommended_serializer.data
        })
    
    elif request.method == 'PUT':
        # Update user profile settings
        serializer = UpdateUserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
