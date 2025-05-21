from django.db import models
from django.utils import timezone
import random
import string

class SMSConfig(models.Model):
    api_key = models.CharField(max_length=255)
    sender_id = models.CharField(max_length=11)  # TextSMS sender ID limit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.sender_id

class SMSLog(models.Model):
    MESSAGE_TYPE_CHOICES = (
        ('promotional', 'Promotional'),
        ('login_code', 'Login Code'),
    )
    subscriber = models.ForeignKey('newsletter.Subscriber', on_delete=models.CASCADE, null=True, blank=True)
    promotional_message = models.ForeignKey('newsletter.PromotionalMessage', on_delete=models.CASCADE, null=True, blank=True)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES)
    phone_number = models.CharField(max_length=13)
    status = models.CharField(max_length=50)  # e.g., 'sent', 'failed'
    response = models.TextField()  # Store API response
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.message_type} SMS to {self.phone_number} - {self.status}"

class LoginCode(models.Model):
    phone_number = models.CharField(max_length=13)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = ''.join(random.choices(string.digits, k=6))
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=10)
        super().save(*args, **kwargs)

    def is_valid(self):
        return not self.is_used and timezone.now() <= self.expires_at

    def __str__(self):
        return f"Login Code {self.code} for {self.phone_number}"