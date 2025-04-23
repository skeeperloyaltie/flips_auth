# datasync/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PredictedWaterLevelsViewSet,
    RigsViewSet,
    WaterLevelDataViewSet,
    WaterLevelsViewSet
)

router = DefaultRouter()
router.register(r'predicted_water_levels', PredictedWaterLevelsViewSet)
router.register(r'rigs', RigsViewSet)
router.register(r'water_level_data', WaterLevelDataViewSet)
router.register(r'water_levels', WaterLevelsViewSet)

urlpatterns = [
    path('', include(router.urls)),
]