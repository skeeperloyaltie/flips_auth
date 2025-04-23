# activity_logger/models.py

from django.db import models
from django.utils.timezone import now
from userprofile.models import UserProfile  # Import the UserProfile model

class UserActivity(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)  # Link to UserProfile
    path = models.CharField(max_length=255)  # Requested URL path
    method = models.CharField(max_length=10)  # HTTP method (GET, POST, etc.)
    timestamp = models.DateTimeField(default=now)  # When the request was made
    ip_address = models.GenericIPAddressField(null=True, blank=True)  # Store the user's IP
    user_agent = models.TextField(blank=True)  # Store user agent details

    def __str__(self):
        return f"Activity by {self.user_profile.user.username} on {self.timestamp}"
