import logging
import uuid
from django.contrib.auth import authenticate, get_user_model
from django.core.mail import send_mail
from django.urls import reverse
from django.db import transaction
from rest_framework import generics, permissions, status, views
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from .serializers import UserSerializer
from .models import VerificationToken
from userprofile.models import UserProfile
from userprofile.serializers import UserProfileSerializer

User = get_user_model()

# Configure logging
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
            UserProfile.objects.get_or_create(user=user, defaults={'privacy_policy_accepted': False})  # Add this
            logger.info(f"User {user.username} created successfully.")

            token = str(uuid.uuid4())
            VerificationToken.objects.create(user=user, token=token)
            verification_link = self.request.build_absolute_uri(reverse('verify-email', args=[token]))
            send_mail(
                'Verify your email',
                f'Click on the link to verify your email: {verification_link}',
                'FlipsOrganization',
                [user.email],
            )
            logger.info(f"Verification email sent to {user.email} for user {user.username}.")
        except Exception as e:
            logger.error(f"Unexpected error during user creation: {str(e)}", exc_info=True)
            raise

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

class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, format=None):
        data = request.data
        logger.debug(f"Login data received: {data}")
        username = data.get('username', None)
        password = data.get('password', None)

        if not username or not password:
            logger.warning('Login attempt with missing username or password.')
            return Response({'error': 'Username and password required'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)
        logger.debug(f'User authentication result: {user}')

        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            try:
                profile = UserProfile.objects.get(user=user)
                needs_privacy_policy = not profile.privacy_policy_accepted
            except UserProfile.DoesNotExist:
                logger.warning(f"No UserProfile found for user: {username}")
                needs_privacy_policy = True  # Assume policy not accepted if profile is missing
            logger.info(f'User {username} logged in successfully.')
            return Response({
                'token': token.key,
                'needs_privacy_policy': needs_privacy_policy
            }, status=status.HTTP_200_OK)

        logger.warning(f'Invalid login credentials for user: {username}')
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_400_BAD_REQUEST)

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
                # Create UserProfile with default privacy_policy_accepted=False
                UserProfile.objects.create(user=user, privacy_policy_accepted=False)
                logger.info(f'New user created with Google sign-in: {email}')
            else:
                logger.info(f'User {email} logged in with Google sign-in.')

            token, _ = Token.objects.get_or_create(user=user)
            try:
                profile = UserProfile.objects.get(user=user)
                needs_privacy_policy = not profile.privacy_policy_accepted
            except UserProfile.DoesNotExist:
                logger.warning(f"No UserProfile found for Google user: {email}")
                needs_privacy_policy = True
            return Response({
                'token': token.key,
                'needs_privacy_policy': needs_privacy_policy
            })
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