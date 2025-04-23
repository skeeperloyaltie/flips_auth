# activity_logger/middleware.py

from .models import UserActivity
from django.utils.timezone import now
from django.utils.deprecation import MiddlewareMixin

class UserActivityLoggerMiddleware(MiddlewareMixin):
    """
    Middleware to log each user's activity (path, method, IP, etc.) to the database.
    This applies to all apps in the Django project.
    """
    
    # Allowed paths that do not need logging
    EXCLUDED_PATHS = ['/static/', '/health-check/']

    def process_request(self, request):
        # Skip logging for unauthenticated users and excluded paths
        if not request.user.is_authenticated or any(request.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return
        
        user_profile = request.user.profile
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Create a new UserActivity record
        UserActivity.objects.create(
            user_profile=user_profile,
            path=request.path,
            method=request.method,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=now()
        )

    def get_client_ip(self, request):
        """Helper function to get the IP address of the user making the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
