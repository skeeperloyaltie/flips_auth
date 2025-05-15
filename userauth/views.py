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
            UserProfile.objects.get_or_create(
                user=user,
                defaults={'privacy_policy_accepted': False}  # Explicitly set
            )
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

# Rest of the views remain unchanged
class VerifyEmailView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, token, format=None):
        try:
            verification_token = VerificationToken.objects.get(token=token)
            user = verification_token.user
            user.is_active = True
            user.save()
            verification_token.delete()
            logger.info(f'Email verified for user {user.username}.')
            return Response({'status': 'Email verified successfully.'}, status=status.HTTP_200_OK)
        except VerificationToken.DoesNotExist:
            logger.warning(f'Invalid verification token: {token}')
            return Response({'status': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import views, permissions, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
import logging

logger = logging.getLogger(__name__)

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import views, permissions, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
import logging

logger = logging.getLogger(__name__)

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

        # Authenticate using email or username
        user = authenticate(email=email, password=password) or authenticate(username=user.username, password=password)
        logger.debug(f'User authentication result: {user}')

        if user is None:
            logger.warning(f'Invalid login credentials for email: {email}')
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            logger.info(f'Login attempt for non-active user: {email}')
            return Response({'error': 'Account is not verified. Please check your email.'}, status=status.HTTP_403_FORBIDDEN)

        token, created = Token.objects.get_or_create(user=user)
        needs_privacy_policy = not user.profile.privacy_policy_accepted
        logger.info(f'User {email} logged in successfully. Needs privacy policy: {needs_privacy_policy}')
        return Response({
            'token': token.key,
            'needs_privacy_policy': needs_privacy_policy
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
                UserProfile.objects.create(user=user)
                logger.info(f'New user created with Google sign-in: {email}')
            else:
                logger.info(f'User {email} logged in with Google sign-in.')

            token, _ = Token.objects.get_or_create(user=user)
            needs_privacy_policy = not PrivacyPolicyAcceptance.objects.filter(user=user, accepted=True).exists()
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