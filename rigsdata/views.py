from rest_framework.exceptions import PermissionDenied
import logging
from rest_framework import generics, permissions
from rest_framework.response import Response
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import F
from monitor.models import WaterLevelData
from userprofile.models import UserProfile
from .serializers import WaterLevelDataSerializer

# Configure logging
logger = logging.getLogger(__name__)


class WaterLevelDataListView(generics.ListAPIView):
    """
    API View to fetch water level data based on the user's subscription plan.
    """
    serializer_class = WaterLevelDataSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Returns the filtered queryset based on the user's subscription plan.
        """
        user = self.request.user
        current_time = now()

        try:
            # Retrieve the user's profile
            profile = UserProfile.objects.select_related('subscription_plan').get(user=user)
            subscription_plan = profile.subscription_plan.name if profile.subscription_plan else "No Plan"
            logger.info(f"User {user.username} has subscription plan: {subscription_plan}")
        except UserProfile.DoesNotExist:
            logger.warning(f"UserProfile not found for {user.username}.")
            raise PermissionDenied("You do not have a valid profile or subscription.")

        # Define subscription-based limits
        if user.is_staff:
            logger.info(f"Admin User: {user.username} accessing all data.")
            return WaterLevelData.objects.filter(timestamp__gte=current_time - timedelta(days=180))

        elif profile.subscription_plan and profile.subscription_plan.name.lower() == 'government':
            logger.info(f"Government User: {user.username} accessing 100 latest records.")
            return WaterLevelData.objects.filter(timestamp__gte=current_time - timedelta(hours=6)).order_by('-timestamp')[:100]

        elif profile.subscription_plan and profile.subscription_plan.name.lower() == 'corporate':
            logger.info(f"Corporate User: {user.username} accessing limited data with CTA.")
            return WaterLevelData.objects.filter(timestamp__gte=current_time - timedelta(hours=2)).order_by('-timestamp')[:50]

        elif profile.subscription_plan and profile.subscription_plan.name.lower() == 'free':
            logger.info(f"Free User: {user.username} accessing minimal data with CTA.")
            return WaterLevelData.objects.filter(timestamp__gte=current_time - timedelta(minutes=30)).order_by('-timestamp')[:10]

        else:
            logger.warning(f"User {user.username} does not have sufficient access.")
            return WaterLevelData.objects.none()

    def list(self, request, *args, **kwargs):
        """
        Handles the GET request and returns formatted data with a CTA if applicable.
        """
        queryset = self.get_queryset()

        if queryset.exists():
            # Retrieve joined fields from both WaterLevelData and Rig tables
            data = queryset.values(
                rig_sensor_id=F('rig__sensor_id'),
                rig_location=F('rig__location'),
                rig_latitude=F('rig__latitude'),
                rig_longitude=F('rig__longitude'),
                water_level=F('level'),
                temperature_data=F('temperature'),
                humidity_data=F('humidity'),
                timestamp_=F('timestamp')
            )

            formatted_data = {
                "columns": ["Rig Sensor ID", "Location", "Latitude", "Longitude", "Water Level", "Temperature", "Humidity", "Timestamp"],
                "rows": list(data)
            }

            # Add Call-To-Action (CTA) for non-government users
            profile = UserProfile.objects.get(user=request.user)
            subscription_plan = profile.subscription_plan.name if profile.subscription_plan else "No Plan"
            logger.info(f"User {request.user.username} with plan {subscription_plan} accessed data.")

            if profile.subscription_plan and profile.subscription_plan.name.lower() in ['free', 'corporate']:
                formatted_data["cta"] = {
                    "message": "Upgrade your plan to access more data and features.",
                    "upgrade_url": "/subscriptions/upgrade/"
                }

            logger.info(f"Data returned for {request.user.username}: {formatted_data}")
            return Response(formatted_data)

        logger.warning(f"No data access for {request.user.username}.")
        return Response({"detail": "No data available. Please check your subscription or contact admin."}, status=403)
