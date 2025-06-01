from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, PrivacyPolicyAcceptance
from subscription.models import SubscriptionPlan

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    subscription_plan_id = serializers.PrimaryKeyRelatedField(
        queryset=SubscriptionPlan.objects.all(), source='subscription_plan', required=False, allow_null=True
    )
    has_accepted_privacy_policy = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'user', 'profile_picture', 'subscription_status',
            'billing_address', 'phone_number', 'category', 'bio', 'birthday',
            'subscription_plan_id', 'expiry_date', 'has_accepted_privacy_policy'
        ]

    def get_has_accepted_privacy_policy(self, obj):
        return PrivacyPolicyAcceptance.objects.filter(user=obj.user, accepted=True).exists()

class UpdateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class UpdatePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Password must contain at least one digit.")
        if not any(char.isalpha() for char in value):
            raise serializers.ValidationError("Password must contain at least one letter.")
        return value

class DeleteAccountSerializer(serializers.Serializer):
    confirm = serializers.BooleanField(required=True)

class SendPasswordResetEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(max_length=128, write_only=True)

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Password must contain at least one digit.")
        if not any(char.isalpha() for char in value):
            raise serializers.ValidationError("Password must contain at least one letter.")
        return value