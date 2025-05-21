from rest_framework import serializers
from .models import Subscriber, PromotionalMessage

class SubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscriber
        fields = ['id', 'email', 'phone_number', 'subscribed_at']

class PromotionalMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromotionalMessage
        fields = ['id', 'subject', 'message', 'created_at', 'sent_at', 'sms_sent', 'email_sent']