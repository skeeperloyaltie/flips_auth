# datasync/views.py

from rest_framework import viewsets
from .models import PredictedWaterLevels, Rigs, WaterLevelData, WaterLevels
from .serializers import (
    PredictedWaterLevelsSerializer,
    RigsSerializer,
    WaterLevelDataSerializer,
    WaterLevelsSerializer
)

class PredictedWaterLevelsViewSet(viewsets.ModelViewSet):
    queryset = PredictedWaterLevels.objects.using('default').all()  # Ensure using PostgreSQL
    serializer_class = PredictedWaterLevelsSerializer

class RigsViewSet(viewsets.ModelViewSet):
    queryset = Rigs.objects.using('default').all()  # Ensure using PostgreSQL
    serializer_class = RigsSerializer

class WaterLevelDataViewSet(viewsets.ModelViewSet):
    queryset = WaterLevelData.objects.using('default').all()  # Ensure using PostgreSQL
    serializer_class = WaterLevelDataSerializer

class WaterLevelsViewSet(viewsets.ModelViewSet):
    queryset = WaterLevels.objects.using('default').all()  # Ensure using PostgreSQL
    serializer_class = WaterLevelsSerializer