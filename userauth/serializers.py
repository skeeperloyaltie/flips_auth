import logging
import re
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers
from userprofile.models import UserProfile
from subscription.models import SubscriptionPlan

# Configure logging
logger = logging.getLogger(__name__)

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'phone_number', 'category', 'bio', 'profile_picture',
            'subscription_status', 'billing_address',
            'birthday', 'subscription_plan', 'expiry_date',
            'privacy_policy_accepted'
        )  # Removed 'privacy_policy_accepted_date' as it's not in UserProfile model

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False, partial=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'first_name', 'last_name', 'profile')
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'username': {'required': False},  # Username is derived from email
            'first_name': {'required': False},
            'last_name': {'required': False}
        }

    def validate_email(self, value):
        if not value:
            logger.warning("Email validation failed: Email is required.")
            raise serializers.ValidationError("Email is required.")
        if User.objects.filter(email__iexact=value).exists():
            logger.warning(f"Email validation failed: Email {value} already exists.")
            raise serializers.ValidationError("Email already exists.")
        return value.lower()  # Normalize email to lowercase

    def validate_password(self, value):
        logger.debug(f"Validating password: {value}")
        if len(value) < 8:
            logger.warning("Password validation failed: Password is too short.")
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        if not re.search(r'\d', value):
            logger.warning("Password validation failed: No digit found.")
            raise serializers.ValidationError("Password must contain at least one digit.")
        if not re.search(r'[A-Z]', value):
            logger.warning("Password validation failed: No uppercase letter found.")
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r'[a-z]', value):
            logger.warning("Password validation failed: No lowercase letter found.")
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
        if not re.search(r'\W', value):
            logger.warning("Password validation failed: No special character found.")
            raise serializers.ValidationError("Password must contain at least one special character.")
        return value

    def create(self, validated_data):
        logger.debug(f"Creating user with validated data: {validated_data}")
        profile_data = validated_data.pop('profile', {})
        
        with transaction.atomic():
            # Derive username from email if not provided
            username = validated_data.get('username', validated_data['email'].split('@')[0])
            # Create User
            user = User(
                username=username,
                email=validated_data.get('email'),
                first_name=validated_data.get('first_name', ''),
                last_name=validated_data.get('last_name', ''),
            )
            user.set_password(validated_data['password'])
            user.is_active = False  # Set is_active=False as per CreateUserView
            user.save()  # Triggers post_save signal to create UserProfile

            # Update UserProfile created by the signal
            try:
                profile = user.profile
                # Update fields from profile_data if provided
                for field, value in profile_data.items():
                    if value is not None:  # Only update non-None values
                        setattr(profile, field, value)
                profile.privacy_policy_accepted = False  # Ensure default as per CreateUserView
                profile.save()
                logger.info(f"User {user.username} created successfully with updated profile.")
            except UserProfile.DoesNotExist:
                logger.error(f"UserProfile not found for user {user.username} after creation")
                raise serializers.ValidationError("Failed to create or update user profile.")

        return user

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        profile = UserProfileSerializer(instance.profile).data
        representation['profile'] = profile
        return representation