#userprofile/views.py 
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .serializers import (
    UserProfileSerializer, UpdateUserSerializer,
    UpdatePasswordSerializer, DeleteAccountSerializer,
    SendPasswordResetEmailSerializer, ResetPasswordSerializer
)
from .models import UserProfile
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = UserProfile.objects.get(user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    def put(self, request):
        profile = UserProfile.objects.get(user=request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        user = request.user
        serializer = UpdateUserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdatePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        serializer = UpdatePasswordSerializer(data=request.data)
        if serializer.is_valid():
            old_password = serializer.data.get('old_password')
            new_password = serializer.data.get('new_password')

            if not request.user.check_password(old_password):
                return Response({'old_password': 'Wrong password.'}, status=status.HTTP_400_BAD_REQUEST)

            request.user.set_password(new_password)
            request.user.save()
            return Response({'status': 'Password updated successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        serializer = DeleteAccountSerializer(data=request.data)
        if serializer.is_valid():
            confirm = serializer.data.get('confirm')

            if confirm:
                user = request.user
                user.delete()
                return Response({'status': 'Account deleted successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'status': 'Account deletion not confirmed'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SendPasswordResetEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SendPasswordResetEmailSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.data.get('email')
            user = User.objects.filter(email=email).first()
            if user:
                token = PasswordResetTokenGenerator().make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))

                reset_url = f"http://127.0.0.1:8000/userprofile/password-reset-confirm?uid={uid}&token={token}"

                send_mail(
                    'Password Reset Request',
                    f'Click the link below to reset your password:\n{reset_url}',
                    'gugod254@gmail.com',  # Replace with your email
                    [email],
                )
            return Response({'status': 'Password reset email sent'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.shortcuts import render, redirect
from .serializers import ResetPasswordSerializer

class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        uidb64 = request.query_params.get('uid')
        token = request.query_params.get('token')

        if not uidb64 or not token:
            return Response({'status': 'Missing uid or token in query parameters'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and PasswordResetTokenGenerator().check_token(user, token):
            # Render the HTML page for password reset
            return render(request, 'login/password_reset_confirm.html', {'uidb64': uidb64, 'token': token})

        return Response({'status': 'Invalid link'}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        uidb64 = request.data.get('uidb64')
        token = request.data.get('token')

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and PasswordResetTokenGenerator().check_token(user, token):
            serializer = ResetPasswordSerializer(data=request.data)
            if serializer.is_valid():
                new_password = serializer.validated_data.get('new_password')
                user.set_password(new_password)
                user.save()
                return redirect('/static/index.html')  # Redirect to the success page

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': 'Invalid link'}, status=status.HTTP_400_BAD_REQUEST)





# Serializers
from rest_framework import serializers

class SendPasswordResetEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

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