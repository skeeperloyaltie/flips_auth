from django.urls import path
from .views import APIStatusView

urlpatterns = [
    path('status/', APIStatusView.as_view(), name='api_status'),
]
