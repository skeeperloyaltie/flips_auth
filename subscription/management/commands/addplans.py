from django.core.management.base import BaseCommand
from subscription.models import SubscriptionPlan
import uuid

class Command(BaseCommand):
    help = 'Adds initial subscription plans to the database'

    def handle(self, *args, **options):
        SubscriptionPlan.objects.all().delete()  # Clear existing data
        plans = [
            {'name': 'Free Plan', 'price': 0.00, 'description': 'Basic access with limited features.', 'unique_id': uuid.uuid4()},
            {'name': 'Starter Plan', 'price': 12.00, 'description': 'Ideal for small teams.', 'unique_id': uuid.uuid4()},
            {'name': 'Business Plan', 'price': 299.00, 'description': 'Advanced features for growing businesses.', 'unique_id': uuid.uuid4()},
            {'name': 'Ultimate Plan', 'price': 599.00, 'description': 'All features and priority support.', 'unique_id': uuid.uuid4()},
        ]

        for plan in plans:
            SubscriptionPlan.objects.create(**plan)

        self.stdout.write(self.style.SUCCESS('Successfully added subscription plans'))
