# datasync/serializers.py

from rest_framework import serializers
from .models import PredictedWaterLevels, Rigs, WaterLevelData, WaterLevels

class PredictedWaterLevelsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PredictedWaterLevels
        fields = '__all__'

class RigsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rigs
        fields = '__all__'

class WaterLevelDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaterLevelData
        fields = '__all__'

class WaterLevelsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaterLevels
        fields = '__all__'