from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['user', 'profile_picture', 'subscription_status', 'subscription_level', 'billing_address', 'phone_number', 'category', 'bio']

class UpdateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class UpdatePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

class DeleteAccountSerializer(serializers.Serializer):
    confirm = serializers.BooleanField(required=True)

class SendPasswordResetEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
from rest_framework import serializers
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(max_length=128, write_only=True)

    def validate_new_password(self, value):
        # Example password validation logic
        if len(value) < 8:  # Ensure password is at least 8 characters long
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        
        if not any(char.isdigit() for char in value):  # Check for at least one digit
            raise serializers.ValidationError("Password must contain at least one digit.")
        
        if not any(char.isalpha() for char in value):  # Check for at least one letter
            raise serializers.ValidationError("Password must contain at least one letter.")

        # Additional checks can be added here (e.g., special characters)

        return value
