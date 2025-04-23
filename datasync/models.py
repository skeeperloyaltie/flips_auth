# datasync/models.py
from django.db import models
from monitor.models import *

class PredictedWaterLevels(models.Model):
    _id = models.CharField(max_length=24, unique=True)  # Assuming standard MongoDB ObjectId length
    timestamp = models.DateTimeField()
    predicted_level = models.FloatField()


# class Rigs(models.Model):
#     _id = models.CharField(max_length=24, unique=True)  # Assuming standard MongoDB ObjectId length
#     sensor_id = models.CharField(max_length=255, unique=True)
#     location = models.CharField(max_length=255)
#     latitude = models.FloatField(default=0.0)
#     longitude = models.FloatField(default=0.0)


# class WaterLevelData(models.Model):
#     _id = models.CharField(max_length=24, unique=True)  # Assuming standard MongoDB ObjectId length
#     timestamp = models.DateTimeField()
#     rig = models.CharField(max_length=255)
#     level = models.FloatField()
#     temperature = models.FloatField()
#     humidity = models.FloatField()


class WaterLevels(models.Model):
    _id = models.CharField(max_length=24, unique=True)  # Assuming standard MongoDB ObjectId length
    timestamp = models.DateTimeField()
    rig = models.CharField(max_length=255)
    level = models.FloatField()
    temperature = models.FloatField()
    humidity = models.FloatField()


class SyncActivity(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    table_name = models.CharField(max_length=255)
    records_updated = models.IntegerField()