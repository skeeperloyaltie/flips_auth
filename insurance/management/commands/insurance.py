from django.core.management.base import BaseCommand
from insurance.models import InsurancePlan

class Command(BaseCommand):
    help = "Initialize predefined insurance plans into the database."

    def handle(self, *args, **kwargs):
        # Define insurance plans
        plans = [
            {
                "name": "Essential Plan",
                "description": "Basic coverage for low-income households.",
                "premium": 5.00,
                "coverage_limit": 5000.00,
                "claim_limit": 1,
                "features": "Covers property damage. No coverage for personal belongings.",
                "target_audience": "Low-income households in flood-prone areas",
            },
            {
                "name": "Standard Plan",
                "description": "Standard coverage for small families.",
                "premium": 15.00,
                "coverage_limit": 15000.00,
                "claim_limit": 2,
                "features": "Covers property, essential belongings, and relocation costs up to $1,000.",
                "target_audience": "Individuals and small families",
            },
            {
                "name": "Comprehensive Plan",
                "description": "Comprehensive coverage for middle-income families.",
                "premium": 30.00,
                "coverage_limit": 30000.00,
                "claim_limit": 3,
                "features": "Covers property, belongings, relocation costs, and basic medical coverage.",
                "target_audience": "Professionals and middle-income families",
            },
            {
                "name": "Business Plan",
                "description": "Designed for small-to-medium businesses.",
                "premium": 100.00,
                "coverage_limit": 100000.00,
                "claim_limit": 2,
                "features": "Covers property damage, equipment losses, and business interruption for 2 weeks.",
                "target_audience": "Small-to-medium businesses in flood-prone areas",
            },
            {
                "name": "Enterprise Plan",
                "description": "High-value coverage for large businesses and organizations.",
                "premium": 300.00,
                "coverage_limit": 500000.00,
                "claim_limit": 1,
                "features": "Includes extended business interruption and emergency resources.",
                "target_audience": "Large businesses, factories, and government organizations",
            },
            {
                "name": "Family Protection Plan",
                "description": "Specialized plan for large families.",
                "premium": 50.00,
                "coverage_limit": 50000.00,
                "claim_limit": 2,
                "features": "Includes relocation costs and educational expense coverage.",
                "target_audience": "Large families in flood-prone areas",
            },
            {
                "name": "Low-Income Assistance Plan",
                "description": "Government-subsidized plan for vulnerable households.",
                "premium": 2.00,
                "coverage_limit": 2000.00,
                "claim_limit": 1,
                "features": "Covers essential property damage and relocation costs.",
                "target_audience": "Vulnerable and low-income households",
            },
            {
                "name": "VIP Plan",
                "description": "High-end coverage for luxury properties and belongings.",
                "premium": 500.00,
                "coverage_limit": 1000000.00,
                "claim_limit": 1,
                "features": "Includes flood-proofing consultation and emergency response.",
                "target_audience": "High-net-worth individuals and businesses",
            },
            {
                "name": "Government Plan",
                "description": "Comprehensive coverage for public infrastructure.",
                "premium": 0.00,  # Custom pricing
                "coverage_limit": 10000000.00,
                "claim_limit": 1,
                "features": "Includes disaster recovery and infrastructure repair services.",
                "target_audience": "Government agencies in flood-prone regions",
            },
        ]

        # Add plans to the database
        for plan_data in plans:
            plan, created = InsurancePlan.objects.get_or_create(
                name=plan_data["name"],
                defaults={
                    "description": plan_data["description"],
                    "premium": plan_data["premium"],
                    "coverage_limit": plan_data["coverage_limit"],
                    "claim_limit": plan_data["claim_limit"],
                    "features": plan_data["features"],
                    "target_audience": plan_data["target_audience"],
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Added plan: {plan.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Plan already exists: {plan.name}"))
