# rigsdata/serializers.py
from rest_framework import serializers
from monitor.models import WaterLevelData, Rig  # Import from monitor app

class WaterLevelDataSerializer(serializers.ModelSerializer):
    rig_sensor_id = serializers.CharField(source='rig.sensor_id')  # Fetch sensor_id from related rig

    class Meta:
        model = WaterLevelData
        fields = ['rig_sensor_id', 'level', 'temperature', 'humidity', 'timestamp']

class RigSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rig
        fields = ['sensor_id', 'location', 'latitude', 'longitude']
