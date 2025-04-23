from django.core.management.base import BaseCommand
from payments.models import UserPayment
from userprofile.models import UserProfile
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Audit and reconcile UserPayment records with UserProfile subscriptions'

    def handle(self, *args, **kwargs):
        payments = UserPayment.objects.filter(is_verified=True)
        logger.info(f"Starting audit for {payments.count()} verified payments.")

        for payment in payments:
            user_profile = UserProfile.objects.filter(user=payment.user).first()
            if not user_profile:
                logger.error(f"UserProfile missing for user {payment.user.username}")
                continue

            # Check if the profile matches the payment subscription
            if user_profile.subscription_plan != payment.plan:
                logger.warning(f"Mismatch for user {payment.user.username}: "
                               f"Payment plan: {payment.plan.name}, Profile plan: {user_profile.subscription_plan.name if user_profile.subscription_plan else 'None'}")

                # Reconcile profile
                user_profile.subscription_plan = payment.plan
                user_profile.subscription_status = True
                user_profile.expiry_date = payment.verified_at + timezone.timedelta(days=30)
                user_profile.save()

                logger.info(f"Reconciled subscription for user {payment.user.username}")
