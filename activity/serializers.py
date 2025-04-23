# activity_logger/serializers.py

from rest_framework import serializers
from .models import UserActivity

class UserActivitySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user_profile.user.username', read_only=True)  # Include username from User

    class Meta:
        model = UserActivity
        fields = ['username', 'path', 'method', 'timestamp', 'ip_address', 'user_agent']  # Define the fields to expose
