from django.db import models

# Create your models here.
from django.db import models

class Measurement(models.Model):
    timestamp = models.DateTimeField()
    water_level = models.FloatField()
    humidity = models.FloatField()
    temperature = models.FloatField()
    latitude = models.FloatField(null=True, blank=True)  # New Field
    longitude = models.FloatField(null=True, blank=True)  # New Field

    def __str__(self):
        return f"{self.timestamp} - Water Level: {self.water_level}, Humidity: {self.humidity}, Temperature: {self.temperature}"
