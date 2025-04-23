from django.urls import path
from .views import endpoint_status_view

urlpatterns = [
    path('endpointstatus/', endpoint_status_view, name='endpoint-status'),
]
