from django.db import models
from django.contrib.auth.models import User
from subscription.models import SubscriptionPlan
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    subscription_status = models.BooleanField(default=False)
    billing_address = models.TextField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    privacy_policy_accepted = models.BooleanField(default=False)
    category = models.CharField(
        max_length=20,
        choices=[('Student', 'Student'), ('Professional', 'Professional'), ('Associate', 'Associate')],
        default='Student'
    )
    bio = models.TextField(max_length=500, blank=True)
    birthday = models.DateField(null=True, blank=True)
    subscription_plan = models.ForeignKey(
        SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True, related_name='user_profiles'
    )
    expiry_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.username

class PrivacyPolicyAcceptance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='privacy_policy_acceptances')
    email = models.EmailField()
    accepted = models.BooleanField(default=True)
    accepted_date = models.DateTimeField(auto_now_add=True)
    policy_version = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - Accepted: {self.accepted} on {self.accepted_date}"

@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    if created:
        # Get or create the default free plan
        try:
            free_plan = SubscriptionPlan.objects.get(name='free')
        except SubscriptionPlan.DoesNotExist:
            # Create a default free plan if it doesn't exist
            free_plan = SubscriptionPlan.objects.create(
                name='free',
                price=0.00,
                duration=14,  # 14 days
                description='Free plan with limited access'
            )
        
        UserProfile.objects.get_or_create(
            user=instance,
            defaults={
                'privacy_policy_accepted': False,
                'subscription_plan': free_plan,
                'subscription_status': True,
                'expiry_date': timezone.now() + timezone.timedelta(days=14)
            }
        )