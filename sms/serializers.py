from rest_framework import serializers
from .models import SMSConfig, SMSLog, LoginCode

class SMSConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSConfig
        fields = ['id', 'api_key', 'sender_id', 'created_at', 'updated_at']

class SMSLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSLog
        fields = ['id', 'subscriber', 'promotional_message', 'message_type', 'phone_number', 'status', 'response', 'sent_at']

class LoginCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginCode
        fields = ['id', 'phone_number', 'code', 'created_at', 'expires_at', 'is_used']