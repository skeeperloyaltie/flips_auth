from django.urls import path
from .views import create_time_slot, get_predictions

urlpatterns = [
    path('create-time-slot/', create_time_slot, name='create_time_slot'),
    path('get-predictions/', get_predictions, name='get_predictions'),
]
