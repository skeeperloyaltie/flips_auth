from rest_framework import serializers
from .models import PaymentMethod, UserPayment
from subscription.models import SubscriptionPlan
from .serializers import SubscriptionPlanSerializer

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id', 'name', 'account_number', 'paybill_number']

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'price', 'description', 'planID']

class UserPaymentSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    payment_method = PaymentMethodSerializer(read_only=True)

    class Meta:
        model = UserPayment
        fields = [
            'id', 'payment_method', 'plan', 'payment_type', 'unique_reference',
            'transaction_id', 'amount', 'paybill_number', 'account_number',
            'status', 'is_verified', 'created_at', 'verified_at'
        ]
        read_only_fields = [
            'user', 'unique_reference', 'transaction_id', 'status',
            'is_verified', 'created_at', 'verified_at', 'paybill_number', 'account_number'
        ]