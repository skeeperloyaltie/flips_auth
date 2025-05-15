from rest_framework import serializers
from .models import SubscriptionPlan

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    is_promotion_active = serializers.SerializerMethodField()
    is_addon = serializers.BooleanField()  # Add the is_addon field

    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'price', 'description', 'planID', 'is_promotion_active', 'duration_days', 'is_addon']


    def get_is_promotion_active(self, obj):
        # Example of a method that might check some condition
        return obj.price < 10  # Just an example condition
