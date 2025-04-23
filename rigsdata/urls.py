# rigsdata/urls.py
from django.urls import path
from .views import WaterLevelDataListView

urlpatterns = [
    path('waterlevels/', WaterLevelDataListView.as_view(), name='waterlevel-list'),
]
