from django.contrib import admin
from .models import (
    Rig,
    WaterLevelData,
    SyncActivity,
    WaterLevels,
    CriticalThreshold,
    PredictedWaterLevels,  # Import the model
)
from django.utils.timezone import localtime


@admin.register(Rig)
class RigAdmin(admin.ModelAdmin):
    list_display = ('sensor_id', 'location', 'latitude', 'longitude')
    search_fields = ('sensor_id', 'location')

import csv
from django.http import HttpResponse

def export_waterleveldata_as_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=water_level_data.csv'

    writer = csv.writer(response)
    writer.writerow(['Rig', 'Level', 'Temperature', 'Humidity', 'Timestamp', 'Latitude', 'Longitude'])

    for obj in queryset:
        writer.writerow([
            obj.rig.sensor_id,
            obj.level,
            obj.temperature,
            obj.humidity,
            obj.timestamp,
            obj.latitude,
            obj.longitude
        ])

    return response

export_waterleveldata_as_csv.short_description = "Export Selected Water Level Data to CSV"


@admin.register(WaterLevelData)
class WaterLevelDataAdmin(admin.ModelAdmin):
    list_display = ('rig', 'level', 'temperature', 'humidity', 'get_local_timestamp')
    search_fields = ('rig__sensor_id',)
    list_filter = ('timestamp',)
    ordering = ('-timestamp',)
    actions = [export_waterleveldata_as_csv]  # 👈 Add this line

    def get_local_timestamp(self, obj):
        return localtime(obj.timestamp).strftime('%Y-%m-%d %H:%M:%S %Z')
    get_local_timestamp.short_description = 'Timestamp (Local)'


@admin.register(SyncActivity)
class SyncActivityAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'table_name', 'records_updated')
    list_filter = ('table_name', 'timestamp')


@admin.register(WaterLevels)
class WaterLevelsAdmin(admin.ModelAdmin):
    list_display = ('rig', 'level', 'temperature', 'humidity', 'timestamp')
    search_fields = ('rig',)
    list_filter = ('timestamp',)


@admin.register(CriticalThreshold)
class CriticalThresholdAdmin(admin.ModelAdmin):
    list_display = ('water_level_threshold', 'temperature_threshold', 'humidity_threshold')


# Register the PredictedWaterLevels model
@admin.register(PredictedWaterLevels)
class PredictedWaterLevelsAdmin(admin.ModelAdmin):
    list_display = ('rig', 'predicted_level', 'model_name', 'accuracy', 'get_local_timestamp')
    search_fields = ('rig__sensor_id', 'model_name')
    list_filter = ('timestamp', 'model_name')
    ordering = ('-timestamp',)  # Order by timestamp descending

    def get_local_timestamp(self, obj):
        return localtime(obj.timestamp).strftime('%Y-%m-%d %H:%M:%S %Z')
    get_local_timestamp.short_description = 'Timestamp (Local)'
