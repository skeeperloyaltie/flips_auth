from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
import requests
import logging

logger = logging.getLogger(__name__)

class APIStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        endpoints = {
            "login": "http://127.0.0.1:8000/api/login/",
            "user_info": "http://127.0.0.1:8000/api/user-info/",
            "logout": "http://127.0.0.1:8000/api/logout/"
        }
        status = {}
        for key, url in endpoints.items():
            try:
                response = requests.get(url, timeout=5)  # Adding timeout for the request
                status[key] = {'status_code': response.status_code, 'ok': response.ok}
                logger.debug(f"{key} response: {response.status_code}, OK: {response.ok}")
            except requests.RequestException as e:
                status[key] = {'error': str(e)}
                logger.error(f"Error accessing {key} at {url}: {str(e)}")

        return JsonResponse(status)
