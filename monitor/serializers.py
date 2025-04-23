# monitor/serializers.py
from rest_framework import serializers
from .models import Rig, WaterLevelData

class RigSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rig
        fields = ['sensor_id', 'location', 'latitude', 'longitude']


from django.utils.timezone import is_naive, make_aware

class WaterLevelDataSerializer(serializers.ModelSerializer):
    rig = serializers.SlugRelatedField(
        slug_field='sensor_id',
        queryset=Rig.objects.all()
    )
    waterLevel = serializers.FloatField(source='level', required=True)

    class Meta:
        model = WaterLevelData
        fields = ['rig', 'waterLevel', 'temperature', 'humidity', 'timestamp']

    def validate_timestamp(self, value):
        # Ensure the timestamp is timezone-aware
        if is_naive(value):
            value = make_aware(value)
        return value
