# insurance/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from userprofile.models import UserProfile
from .models import InsuranceProfile

@receiver(post_save, sender=UserProfile)
def create_insurance_profile(sender, instance, created, **kwargs):
    if created:
        InsuranceProfile.objects.create(user_profile=instance)
