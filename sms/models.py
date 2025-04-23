# water/models.py
from django.db import models

class WaterLevel(models.Model):
    level = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Level: {self.level} at {self.timestamp}"
