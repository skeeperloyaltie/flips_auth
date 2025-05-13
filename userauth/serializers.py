import logging
import re
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers
from userprofile.models import UserProfile

# Configure logging
logger = logging.getLogger(__name__)

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = (
            'phone_number', 'category', 'bio', 'profile_picture',
            'subscription_status', 'subscription_level', 'billing_address',
            'birthday', 'subscription_plan', 'expiry_date',
            'privacy_policy_accepted', 'privacy_policy_accepted_date'
        )

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'password', 'profile'
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def validate_email(self, value):
        if not value:
            logger.warning("Email validation failed: Email is required.")
            raise serializers.ValidationError("Email is required.")
        if User.objects.filter(email=value).exists():
            logger.warning("Email validation failed: Email already exists.")
            raise serializers.ValidationError("Email already exists.")
        return value

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
        logger.debug(f"Creating user with data: {validated_data}")
        profile_data = validated_data.pop('profile')
        # Ensure privacy_policy_accepted is False by default if not provided
        profile_data.setdefault('privacy_policy_accepted', False)
        profile_data.setdefault('privacy_policy_accepted_date', None)

        with transaction.atomic():
            user = User.objects.create_user(**validated_data)
            UserProfile.objects.create(user=user, **profile_data)
            logger.info(f"User {user.username} created successfully with profile.")
        return user

    def to_representation(self, instance):
        profile_data = {
            'phone_number': instance.profile.phone_number,
            'category': instance.profile.category,
            'bio': instance.profile.bio,
            'profile_picture': instance.profile.profile_picture.url if instance.profile.profile_picture else '',
            'subscription_status': instance.profile.subscription_status,
            'subscription_level': instance.profile.subscription_level,
            'billing_address': instance.profile.billing_address,
            'birthday': instance.profile.birthday,
            'subscription_plan': instance.profile.subscription_plan.id if instance.profile.subscription_plan else None,
            'expiry_date': instance.profile.expiry_date,
            'privacy_policy_accepted': instance.profile.privacy_policy_accepted,
            'privacy_policy_accepted_date': instance.profile.privacy_policy_accepted_date,
        }

        return {
            'id': instance.id,
            'username': instance.username,
            'email': instance.email,
            'profile': profile_data
        }