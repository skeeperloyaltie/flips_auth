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
import logging

# Set up logging
# Set up logging
logger = logging.getLogger(__name__)

class HealthCheckView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            # Check database connectivity by executing a simple query
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result[0] != 1:
                    logger.error("Database health check failed: Invalid query result")
                    return Response(
                        {"status": "error", "message": "Database check failed"},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE
                    )

            # Log successful health check
            logger.debug("Health check successful: Server and database are operational")
            return Response(
                {"status": "ok", "message": "Server and database are healthy"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return Response(
                {"status": "error", "message": f"Health check failed: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            profile = UserProfile.objects.get(user=request.user)
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            logger.error(f"UserProfile not found for user: {request.user.username}")
            return Response({'error': 'User profile not found'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        try:
            profile = UserProfile.objects.get(user=request.user)
            serializer = UserProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"UserProfile updated for user: {request.user.username}")
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UserProfile.DoesNotExist:
            logger.error(f"UserProfile not found for user: {request.user.username}")
            return Response({'error': 'User profile not found'}, status=status.HTTP_404_NOT_FOUND)

class UpdateUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        user = request.user
        serializer = UpdateUserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"User details updated for user: {user.username}")
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
                logger.warning(f"Invalid old password attempt for user: {request.user.username}")
                return Response({'old_password': 'Wrong password.'}, status=status.HTTP_400_BAD_REQUEST)

            request.user.set_password(new_password)
            request.user.save()
            logger.info(f"Password updated for user: {request.user.username}")
            return Response({'message': 'Password updated successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        serializer = DeleteAccountSerializer(data=request.data)
        if serializer.is_valid():
            confirm = serializer.data.get('confirm')

            if confirm:
                username = request.user.username
                request.user.delete()
                logger.info(f"Account deleted for user: {username}")
                return Response({'message': 'Account deleted successfully'}, status=status.HTTP_200_OK)
            else:
                logger.warning(f"Account deletion not confirmed for user: {request.user.username}")
                return Response({'error': 'Account deletion not confirmed'}, status=status.HTTP_400_BAD_REQUEST)
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

                # Update the reset URL to point to the frontend confirm page
                reset_url = f"https://flipsintel.org/login/passwordconfirm.html?uidb64={uid}&token={token}"

                try:
                    send_mail(
                        'Password Reset Request',
                        f'Hello {user.username},\n\nClick the link below to reset your password:\n{reset_url}\n\nIf you did not request this, please ignore this email.',
                        'gugod254@gmail.com',  # Replace with your email
                        [email],
                        fail_silently=False,
                    )
                    logger.info(f"Password reset email sent to: {email}")
                    return Response({'message': 'Password reset email sent'}, status=status.HTTP_200_OK)
                except Exception as e:
                    logger.error(f"Failed to send password reset email to {email}: {str(e)}")
                    return Response({'error': 'Failed to send email'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                logger.warning(f"Password reset requested for non-existent email: {email}")
                # Return success to prevent email enumeration
                return Response({'message': 'Password reset email sent'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        uidb64 = request.data.get('uidb64')
        token = request.data.get('token')
        new_password = serializer.validated_data.get('new_password')

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            logger.warning(f"Invalid uidb64 during password reset: {uidb64}")
            return Response({'error': 'Invalid reset link'}, status=status.HTTP_400_BAD_REQUEST)

        if user is not None and PasswordResetTokenGenerator().check_token(user, token):
            user.set_password(new_password)
            user.save()
            logger.info(f"Password reset successful for user: {user.username} (email: {user.email})")
            return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)
        else:
            logger.warning(f"Invalid token during password reset for user: {user.username if user else 'unknown'}")
            return Response({'error': 'Invalid or expired reset link'}, status=status.HTTP_400_BAD_REQUEST)
        

class VerifyResetTokenView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        uidb64 = request.query_params.get('uidb64')
        token = request.query_params.get('token')

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            if PasswordResetTokenGenerator().check_token(user, token):
                return Response({'email': user.email}, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid or expired reset link'}, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'error': 'Invalid reset link'}, status=status.HTTP_400_BAD_REQUEST)
        
# userprofile/views.py
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import PrivacyPolicyAcceptance, UserProfile
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class AcceptPrivacyPolicyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logger.debug(f"Accept privacy policy attempt. User: {request.user}, Authenticated: {request.user.is_authenticated}, Token: {request.META.get('HTTP_AUTHORIZATION')}")
        try:
            # Create or update PrivacyPolicyAcceptance record
            PrivacyPolicyAcceptance.objects.create(
                user=request.user,
                email=request.user.email,
                accepted=True,
                accepted_date=timezone.now(),
                policy_version="1.0"
            )
            # Update UserProfile.privacy_policy_accepted
            try:
                profile = UserProfile.objects.get(user=request.user)
                profile.privacy_policy_accepted = True
                profile.save()
                logger.info(f"UserProfile.privacy_policy_accepted updated for user: {request.user.username}")
            except UserProfile.DoesNotExist:
                logger.error(f"UserProfile not found for user: {request.user.username}")
                return Response({'error': 'User profile not found'}, status=status.HTTP_404_NOT_FOUND)

            logger.info(f"Privacy policy accepted by user: {request.user.username}, email: {request.user.email}")
            return Response({'message': 'Privacy policy accepted'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error accepting privacy policy for user: {request.user.username}: {str(e)}")
            return Response({'error': 'Failed to accept privacy policy'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)