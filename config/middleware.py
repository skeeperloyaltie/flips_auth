from django.utils.timezone import activate
from .models import TimezoneSetting

class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            timezone_setting = TimezoneSetting.objects.first()
            if timezone_setting:
                activate(timezone_setting.timezone)
            else:
                activate('UTC')  # Default fallback
        except Exception:
            activate('UTC')  # Handle errors gracefully
        return self.get_response(request)
