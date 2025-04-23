# # rigsdata/admin.py
# from django.contrib import admin
# from monitor.models import WaterLevelData, Rig  # Register models from monitor

# @admin.register(WaterLevelData)
# class WaterLevelDataAdmin(admin.ModelAdmin):
#     list_display = ['rig', 'level', 'temperature', 'humidity', 'timestamp']
#     search_fields = ['rig__sensor_id', 'timestamp']

# @admin.register(Rig)
# class RigAdmin(admin.ModelAdmin):
#     list_display = ['sensor_id', 'location', 'latitude', 'longitude']
#     search_fields = ['sensor_id']
