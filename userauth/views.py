import logging
import uuid
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.mail import send_mail
from django.urls import reverse
from django.db import transaction
from rest_framework import generics, permissions, status, views
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .serializers import UserSerializer
from .models import VerificationToken
from userprofile.models import UserProfile

User = get_user_model()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def perform_create(self, serializer):
        try:
            logger.debug(f"Received user creation data: {self.request.data}")
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            logger.debug(f"Validated data for user creation: {validated_data}")

            user = serializer.save(is_active=False)
            # Removed get_or_create; signal in models.py handles UserProfile creation
            logger.info(f"User {user.username} created successfully.")

            token = str(uuid.uuid4())
            VerificationToken.objects.create(user=user, token=token)
            verification_link = self.request.build_absolute_uri(reverse('verify-email', args=[token]))
            send_mail(
                'Verify your email',
                f'Click on the link to verify your email: {verification_link}',
                settings.EMAIL_FROM,
                [user.email],
            )
            logger.info(f"Verification email sent to {user.email} for user {user.username}.")

            auth_token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': auth_token.key,
                'message': 'User created successfully. Please verify your email.'
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Unexpected error during user creation: {str(e)}", exc_info=True)
            raise

from django.utils import timezone
from datetime import timedelta

class VerifyEmailView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, token, format=None):
        try:
            verification_token = VerificationToken.objects.get(token=token)
            if verification_token.created_at < timezone.now() - timedelta(hours=24):
                verification_token.delete()
                logger.warning(f'Expired verification token: {token}')
                return Response({'status': 'Token expired'}, status=status.HTTP_400_BAD_REQUEST)
            user = verification_token.user
            user.is_active = True
            user.save()
            verification_token.delete()
            logger.info(f'Email verified for user {user.username}.')
            return Response({'status': 'Email verified successfully.'}, status=status.HTTP_200_OK)
        except VerificationToken.DoesNotExist:
            logger.warning(f'Invalid verification token: {token}')
            return Response({'status': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, format=None):
        data = request.data
        logger.debug(f"Login data received: {data}")
        email = data.get('username', None)  # Treat 'username' as email
        password = data.get('password', None)

        if not email or not password:
            logger.warning('Login attempt with missing email or password.')
            return Response({'error': 'Email and password required'}, status=status.HTTP_400_BAD_REQUEST)

        # Find user by email (case-insensitive)
        try:
            user = User.objects.get(email__iexact=email)
            logger.debug(f"User found: {user.username}, Email: {user.email}")
        except User.DoesNotExist:
            logger.warning(f'No user found for email: {email}')
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        # Authenticate using username
        authenticated_user = authenticate(username=user.username, password=password)
        logger.debug(f'User authentication result: {authenticated_user}')

        if authenticated_user is None:
            logger.warning(f'Authentication failed for email: {email}, username: {user.username}, password_correct: {user.check_password(password)}')
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        # Allow login regardless of is_active, but indicate verification status
        token, created = Token.objects.get_or_create(user=user)
        needs_privacy_policy = not user.profile.privacy_policy_accepted
        is_verified = user.is_active  # True if verified, False if not
        logger.info(f'User {email} logged in successfully. Verified: {is_verified}, Needs privacy policy: {needs_privacy_policy}')

        return Response({
            'token': token.key,
            'needs_privacy_policy': needs_privacy_policy,
            'is_verified': is_verified
        }, status=status.HTTP_200_OK)

class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

class GoogleLoginView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        token = request.data.get('token')
        try:
            idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), 'YOUR_CLIENT_ID_HERE')
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')

            email = idinfo['email']
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')

            user, created = User.objects.get_or_create(
                email=email,
                defaults={'username': email.split('@')[0], 'first_name': first_name, 'last_name': last_name, 'is_active': True}
            )

            if created:
                # Signal in models.py will create UserProfile
                logger.info(f'New user created with Google sign-in: {email}')
            else:
                logger.info(f'User {email} logged in with Google sign-in.')

            token, _ = Token.objects.get_or_create(user=user)
            needs_privacy_policy = not user.profile.privacy_policy_accepted
            logger.info(f'Google login for {email}. Needs privacy policy: {needs_privacy_policy}')
            return Response({
                'token': token.key,
                'needs_privacy_policy': needs_privacy_policy
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            logger.error(f'Google token verification failed: {e}')
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def logout(request):
    try:
        logger.debug(f"Logout requested for user: {request.user.username}")
        request.user.auth_token.delete()
        logger.info(f'User {request.user.username} logged out successfully.')
        return Response(status=status.HTTP_200_OK)
    except (AttributeError, Token.DoesNotExist):
        logger.warning(f'Logout attempt failed for user: {request.user.username}')
        return Response(status=status.HTTP_400_BAD_REQUEST)

class ResendVerificationEmailView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        user = request.user
        logger.debug(f"Resend verification email requested by user: {user.username}")

        if user.is_active:
            logger.info(f"User {user.username} is already verified.")
            return Response({'message': 'Account is already verified.'}, status=status.HTTP_400_BAD_REQUEST)

        # Delete any existing verification tokens for the user
        VerificationToken.objects.filter(user=user).delete()

        # Create a new verification token
        token = str(uuid.uuid4())
        VerificationToken.objects.create(user=user, token=token)

        # Send verification email
        verification_link = request.build_absolute_uri(reverse('verify-email', args=[token]))
        try:
            send_mail(
                'Verify your email',
                f'Click on the link to verify your email: {verification_link}',
                settings.EMAIL_FROM,
                [user.email],
                fail_silently=False,
            )
            logger.info(f"Verification email resent to {user.email} for user {user.username}.")
            return Response({'message': 'Verification email sent.'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
            return Response({'error': 'Failed to send verification email.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)