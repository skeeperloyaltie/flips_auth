from django.db import models
from django.contrib.auth.models import User
from subscription.models import SubscriptionPlan

class PaymentMethod(models.Model):
    name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=100, blank=True)
    paybill_number = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name

class UserPayment(models.Model):
    PAYMENT_TYPES = (
        ('card', 'Card'),
        ('paybill', 'M-Pesa Paybill'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE, null=True, blank=True)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, default='paybill')
    unique_reference = models.CharField(max_length=100, unique=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paybill_number = models.CharField(max_length=100, blank=True, null=True)
    account_number = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=50, default="pending")
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan.name} - {self.payment_type}"