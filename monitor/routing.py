from django.urls import path
from .consumers import RealTimeDataConsumer

websocket_urlpatterns = [
    path('ws/realtime-data/', RealTimeDataConsumer.as_asgi()),
]
