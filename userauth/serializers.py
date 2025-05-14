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

import logging
import re
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers
from userprofile.models import UserProfile
from userprofile.serializers import UserProfileSerializer

logger = logging.getLogger(__name__)

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False, partial=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'first_name', 'last_name', 'profile')
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False}
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
        profile_data = validated_data.pop('profile', {})
        with transaction.atomic():
            user = User.objects.create_user(**validated_data)
            UserProfile.objects.create(user=user, **profile_data)
            logger.info(f"User {user.username} created successfully with profile.")
        return user

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        profile = UserProfileSerializer(instance.profile).data
        representation['profile'] = profile
        return representation