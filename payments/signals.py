# payments/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserPayment
from django.utils import timezone
import requests
from django.conf import settings

@receiver(post_save, sender=UserPayment)
def sync_user_subscription(sender, instance, **kwargs):
    if instance.is_verified and instance.verified_at:
        data = {
            'user_id': instance.user.id,
            'plan_id': instance.plan.id,
            'status': 'active'
        }
        try:
            response = requests.post(f'{settings.SUBSCRIPTION_API_URL}/api/subscribe/', json=data)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            # Handle the exception (e.g., log it, retry later, notify admins)
            print(f"Failed to update subscription for user {instance.user.username}: {e}")