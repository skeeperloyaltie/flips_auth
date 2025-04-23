# activity_logger/urls.py

from django.urls import path
from .views import UserActivityListView

urlpatterns = [
    path('activities/', UserActivityListView.as_view(), name='user-activity-list'),
]
