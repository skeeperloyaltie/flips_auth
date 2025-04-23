from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from userprofile.models import UserProfile
from subscription.models import SubscriptionPlan
from django.db import transaction
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class Command(BaseCommand):
    help = "Creates a superuser with a corresponding UserProfile"

    def handle(self, *args, **options):
        username = "admin"
        email = "gugod254@gmail.com"
        password = "13917295!GdaguGg"
        phone_number = "+254700000000"  # Optional default

        if User.objects.filter(username=username).exists():
            logger.info(f"Superuser '{username}' already exists. Skipping creation.")
            self.stdout.write(self.style.WARNING(f"Superuser '{username}' already exists."))
            return

        try:
            with transaction.atomic():
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password,
                    is_active=True,
                    is_staff=True,
                    is_superuser=True
                )

                subscription_plan = SubscriptionPlan.objects.first()
                UserProfile.objects.create(
                    user=user,
                    phone_number=phone_number,
                    subscription_status=True,
                    subscription_level="Admin" if not subscription_plan else subscription_plan.name,
                    category="Professional",
                    bio=f"Administrator account for {username}",
                    subscription_plan=subscription_plan
                )

                self.stdout.write(self.style.SUCCESS(f"Successfully created superuser '{username}'"))
                logger.info(f"Superuser '{username}' created successfully.")

        except Exception as e:
            logger.error(f"Error creating superuser: {str(e)}")
            self.stderr.write(self.style.ERROR(f"Error creating superuser: {str(e)}"))
