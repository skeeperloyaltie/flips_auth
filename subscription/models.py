import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField()
    planID = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_addon = models.BooleanField(default=False)
    duration_days = models.IntegerField(default=30)

    def __str__(self):
        return self.name

class UserSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='subscribers')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.end_date and self.active:
            self.end_date = timezone.now() + timezone.timedelta(days=self.plan.duration_days)
        super().save(*args, **kwargs)

    def is_active(self):
        return self.active and (self.end_date is None or self.end_date > timezone.now())

    def __str__(self):
        return f"{self.user.username}'s subscription to {self.plan.name}"