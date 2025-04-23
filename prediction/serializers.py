# prediction/serializers.py
from rest_framework import serializers
from .models import TimeSlot, PredictionResult

class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = ['id', 'user', 'start_time', 'end_time']

class PredictionResultSerializer(serializers.ModelSerializer):
    time_slot = TimeSlotSerializer()

    class Meta:
        model = PredictionResult
        fields = ['id', 'time_slot', 'result_data']
