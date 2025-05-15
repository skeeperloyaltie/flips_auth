# In middleware.py
from rest_framework import status
from rest_framework.response import Response

class RestrictUnverifiedUsersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Skip for unauthenticated users or specific views
        if not request.user.is_authenticated or view_func.__name__ in ['LoginView', 'ResendVerificationEmailView', 'VerifyEmailView']:
            return None

        # Restrict access for unverified users
        if not request.user.is_active:
            restricted_paths = ['/profile/', '/subscriptions/']  # Define restricted endpoints
            if any(request.path.startswith(path) for path in restricted_paths):
                logger.warning(f"Unverified user {request.user.username} attempted to access restricted path: {request.path}")
                return Response(
                    {'error': 'Please verify your email to access this feature.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        return None