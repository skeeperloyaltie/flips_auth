from django.db import models
from django.core.validators import RegexValidator

class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    phone_regex = RegexValidator(
        regex=r'^\+254\d{9}$',
        message="Phone number must be in the format: '+2547XXXXXXXX'"
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=13,
        unique=True,
        blank=True,
        null=True
    )
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

class PromotionalMessage(models.Model):
    subject = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    sms_sent = models.BooleanField(default=False)  # Track if SMS was sent
    email_sent = models.BooleanField(default=False)  # Track if email was sent

    def __str__(self):
        return self.subject