# prediction/models.py
from django.db import models
from django.contrib.auth.models import User

class TimeSlot(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __str__(self):
        return f"TimeSlot from {self.start_time} to {self.end_time} for {self.user.username}"

class PredictionResult(models.Model):
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    result_data = models.JSONField()

    def __str__(self):
        return f"PredictionResult for TimeSlot {self.time_slot.id}"
