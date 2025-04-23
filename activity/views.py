# activity_logger/views.py

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import UserActivity
from .serializers import UserActivitySerializer

class UserActivityListView(generics.ListAPIView):
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access the API

    def get_queryset(self):
        """
        Admins can view all user activities. Regular users can only view their own activities.
        """
        user = self.request.user
        
        # If the user is an admin (is_staff or is_superuser), return all activities
        if user.is_staff or user.is_superuser:
            return UserActivity.objects.all().order_by('-timestamp')

        # For non-admin users, return only their own activities
        user_profile = user.profile
        return UserActivity.objects.filter(user_profile=user_profile).order_by('-timestamp')
