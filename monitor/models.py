from django.db import models
import uuid
from django.db import models
from shapely.geometry import Point, Polygon
import uuid
# from django.contrib.gis.geos import GEOSGeometry, Polygon as DjangoPolygon

import uuid
from django.db import models
from django.contrib.gis.geos import Point as GeoPoint, GEOSGeometry
from django.contrib.gis.db import models as geomodels

class RigArea(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    area_polygon = geomodels.PolygonField()

    class Meta:
        db_table = 'rig_areas'

    def __str__(self):
        return self.name

    def contains_point(self, longitude, latitude):
        """Check if a point is within the area polygon."""
        point = GeoPoint(longitude, latitude)  # Use GeoPoint here
        return self.area_polygon.contains(point)


class Rig(models.Model):
    sensor_id = models.CharField(max_length=255, unique=True)
    location = models.CharField(max_length=100, default="Unknown")
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    area = models.ForeignKey(RigArea, on_delete=models.SET_NULL, null=True, blank=True, related_name="rigs")

    class Meta:
        db_table = 'rigs'

    def __str__(self):
        return self.sensor_id

    def save(self, *args, **kwargs):
        # Validate if the rig's coordinates are within the assigned area polygon
        if self.area and not self.area.contains_point(self.longitude, self.latitude):
            raise ValueError("Rig coordinates are outside the assigned area polygon.")

        super().save(*args, **kwargs)  # Call the original save method


class WaterLevelData(models.Model):
    _id = models.CharField(max_length=24, editable=False, unique=True, null=True, blank=True)
    rig = models.ForeignKey(Rig, on_delete=models.CASCADE)
    level = models.FloatField(default=0.0)
    temperature = models.FloatField(default=0.0)
    humidity = models.FloatField(default=0.0)
    timestamp = models.DateTimeField()
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)

    class Meta:
        db_table = 'waterleveldata'

    def __str__(self):
        return f"{self.rig.sensor_id} - {self.timestamp}"

    def save(self, *args, **kwargs):
        if not self._id:
            self._id = str(uuid.uuid4()).replace('-', '')[:24]
        super(WaterLevelData, self).save(*args, **kwargs)


class PredictedWaterLevels(models.Model):
    rig = models.ForeignKey(Rig, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    predicted_level = models.FloatField()
    model_name = models.CharField(max_length=50)
    accuracy = models.FloatField()

    class Meta:
        db_table = 'predictedwaterlevels'

    def __str__(self):
        return f"{self.timestamp} - {self.predicted_level} - {self.model_name} - {self.accuracy}"

class WaterLevels(models.Model):
    timestamp = models.DateTimeField()
    rig = models.CharField(max_length=255)
    level = models.FloatField(default=0.0)
    temperature = models.FloatField(default=0.0)
    humidity = models.FloatField(default=0.0)

    class Meta:
        db_table = 'waterlevels'

    def __str__(self):
        return f"{self.rig} - {self.timestamp}"

class SyncActivity(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    table_name = models.CharField(max_length=255)
    records_updated = models.IntegerField(default=0)

    class Meta:
        db_table = 'syncactivity'

    def __str__(self):
        return f"{self.timestamp} - {self.table_name} - {self.records_updated}"

class CriticalThreshold(models.Model):
    water_level_threshold = models.FloatField(help_text="Critical water level threshold in mm.")
    temperature_threshold = models.FloatField(help_text="Critical temperature threshold in °C.")
    humidity_threshold = models.FloatField(help_text="Critical humidity threshold in %.")

    class Meta:
        db_table = 'criticalthresholds'

    def __str__(self):
        return f"Water Level: {self.water_level_threshold} mm, Temperature: {self.temperature_threshold} °C, Humidity: {self.humidity_threshold} %"