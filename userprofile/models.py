from django.db import models
from django.contrib.auth.models import User
from subscription.models import SubscriptionPlan

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    subscription_status = models.BooleanField(default=False)
    subscription_level = models.CharField(max_length=50, null=True, blank=True)
    billing_address = models.TextField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    category = models.CharField(max_length=20, choices=[
        ('Student', 'Student'),
        ('Professional', 'Professional'),
        ('Associate', 'Associate'),
    ], default='Student')
    bio = models.TextField(max_length=500, blank=True)
    birthday = models.DateField(null=True, blank=True)
    subscription_plan = models.ForeignKey(
        SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True, related_name='user_profiles'
    )
    expiry_date = models.DateTimeField(null=True, blank=True)
    privacy_policy_accepted = models.BooleanField(default=False)
    privacy_policy_accepted_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.username