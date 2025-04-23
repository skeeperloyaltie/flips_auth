from rest_framework import serializers
from .models import PaymentMethod, UserPayment
from subscription.models import SubscriptionPlan  # Import SubscriptionPlan


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id', 'name', 'account_number', 'paybill_number']


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan  # Reference SubscriptionPlan from subscriptions
        fields = ['id', 'name', 'price', 'description', 'planID']


class UserPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPayment
        fields = ['id', 'payment_method', 'plan', 'unique_reference', 'amount', 'is_verified', 'created_at', 'verified_at']
        read_only_fields = ['user', 'unique_reference', 'is_verified', 'created_at', 'verified_at']