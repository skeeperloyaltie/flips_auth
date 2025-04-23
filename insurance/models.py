from django.db import models
from userprofile.models import UserProfile


class InsurancePlan(models.Model):
    """
    Represents an insurance plan with details about coverage, pricing, and additional features.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    premium = models.DecimalField(max_digits=10, decimal_places=2)  # Monthly premium amount
    coverage_limit = models.DecimalField(max_digits=12, decimal_places=3)  # Maximum coverage amount
    claim_limit = models.PositiveIntegerField(null=True, blank=True)  # Maximum number of claims allowed
    features = models.TextField(null=True, blank=True)  # Additional features of the plan
    target_audience = models.CharField(max_length=255, null=True, blank=True)  # Target audience
    duration_months = models.PositiveIntegerField(default=12)  # Duration of the plan in months

    def __str__(self):
        return self.name


class InsuranceProfile(models.Model):
    """
    Represents insurance-specific details for a user.
    """
    user_profile = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='insurance_profile'
    )
    insured = models.BooleanField(default=False)  # Indicates if the user is insured
    active_plan = models.ForeignKey(
        InsurancePlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='insured_users'
    )
    active_policies = models.PositiveIntegerField(default=0)  # Number of active policies
    last_claim_date = models.DateField(null=True, blank=True)  # Date of the last claim
    total_claimed = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # Total claimed amount

    def __str__(self):
        return f"InsuranceProfile for {self.user_profile.user.username}"


class InsuranceClaim(models.Model):
    """
    Represents claims filed by insured users.
    """
    insurance_profile = models.ForeignKey(
        InsuranceProfile,
        on_delete=models.CASCADE,
        related_name='claims'
    )
    claim_amount = models.DecimalField(max_digits=12, decimal_places=2)  # Amount claimed
    claim_date = models.DateField(auto_now_add=True)  # Date the claim was filed
    status = models.CharField(
        max_length=20,
        choices=[
            ('Pending', 'Pending'),
            ('Approved', 'Approved'),
            ('Rejected', 'Rejected'),
        ],
        default='Pending'
    )
    description = models.TextField(blank=True, null=True)  # Description or reason for the claim

    def __str__(self):
        return f"Claim {self.id} for {self.insurance_profile.user_profile.user.username}"


class InsurancePayment(models.Model):
    """
    Tracks payments for insurance policies.
    """
    insurance_profile = models.ForeignKey(
        InsuranceProfile,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)  # Payment amount
    payment_date = models.DateTimeField(auto_now_add=True)  # Date of payment
    reference_number = models.CharField(max_length=100, unique=True)  # Unique payment reference

    def __str__(self):
        return f"Payment {self.reference_number} for {self.insurance_profile.user_profile.user.username}"
