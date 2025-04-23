# monitor/urls.py
from django.urls import path
from .views import NeuralNetworkAPIView

urlpatterns = [
    path('neural-network/', NeuralNetworkAPIView.as_view(), name='neural_network_api'),
]