from django.core.management.base import BaseCommand
from subscription.models import SubscriptionPlan
import uuid

class Command(BaseCommand):
    help = "Clears existing subscription plans and adds initial subscription plans to the database"

    def handle(self, *args, **options):
        SubscriptionPlan.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS("Successfully deleted all existing subscription plans"))

        plans = [
            {
                "name": "free",
                "price": 0.00,
                "description": (
                    "Basic live data dashboard with limited functionality.\n"
                    "- Access to one sensor only.\n"
                    "- No access to historical data.\n"
                    "- Basic alerts (once a day notifications).\n"
                    "- Upgrade prompts available on the dashboard."
                ),
                "planID": uuid.uuid4(),
                "duration_days": 30,
            },
            {
                "name": "corporate",
                "price": 10000.00,
                "description": (
                    "Suitable for well-established organizations.\n"
                    "- Access to 7-14 days of historical data.\n"
                    "- Real-time alerts (SMS, email notifications).\n"
                    "- Weekly report generation.\n"
                    "- Basic analytics and visualization.\n"
                    "Add-ons:\n"
                    "- Additional rig/sensor: KES 2,000/month\n"
                    "- Custom reports: KES 2,500/report\n"
                    "- API access and basic GIS layers: KES 5,000/month\n"
                    "- Internal system integration: KES 3,000/month."
                ),
                "planID": uuid.uuid4(),
                "duration_days": 30,
            },
            {
                "name": "government",
                "price": 40000.00,
                "description": (
                    "Comprehensive features for large enterprises.\n"
                    "- 14-30 day trial period with full access.\n"
                    "- Unlimited user accounts and collaboration.\n"
                    "- Access to advanced historical data (up to 5 years).\n"
                    "- Custom report generation and predictive analytics.\n"
                    "Usage-Based Scaling:\n"
                    "- Additional rig/sensor: KES 7,400/month\n"
                    "- Custom complex reports: KES 20,000/report\n"
                    "- Predictive models with AI insights: KES 30,000 - KES 50,000/month\n"
                    "- Advanced GIS layers: KES 7,500 - KES 22,500/month.\n"
                    "Additional Services:\n"
                    "- 24/7 support with dedicated account manager: KES 12,000/month\n"
                    "- Custom API integrations: KES 15,000/month\n"
                    "- Onboarding and training package: KES 25,000 (one-time fee).\n"
                    "Discounts:\n"
                    "- 15-25% off for annual subscriptions."
                ),
                "planID": uuid.uuid4(),
                "duration_days": 30,
            },
        ]

        for plan in plans:
            SubscriptionPlan.objects.create(**plan)
            self.stdout.write(self.style.SUCCESS(f'Successfully added: {plan["name"]}'))