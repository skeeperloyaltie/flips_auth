from rest_framework import serializers
from .models import SubscriptionPlan

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    is_promotion_active = serializers.SerializerMethodField()
    is_addon = serializers.BooleanField()  # Add the is_addon field

    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'price', 'description', 'is_promotion_active', 'is_addon']  # Include is_addon in fields

    def get_is_promotion_active(self, obj):
        # Example of a method that might check some condition
        return obj.price < 10  # Just an example condition
