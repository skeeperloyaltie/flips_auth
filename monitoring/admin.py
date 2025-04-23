from django.contrib import admin
from .models import Measurement

@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'water_level', 'humidity', 'temperature')
    list_filter = ('timestamp',)
    search_fields = ('timestamp',)
