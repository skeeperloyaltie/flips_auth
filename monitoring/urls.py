from django.urls import path
from .views import (
    MeasurementListCreateView, 
    water_level_endpoint, 
    humidity_endpoint, 
    temperature_endpoint, 
    linear_regression_endpoint, 
    get_all_data, 
    get_all_files,
    flood_monitoring_geojson,
    map_visualization_geojson
)

urlpatterns = [
    path('measurements/', MeasurementListCreateView.as_view(), name='measurements-list-create'),
    path('water-levels/', water_level_endpoint, name='water-levels'),
    path('humidity/', humidity_endpoint, name='humidity'),
    path('temperature/', temperature_endpoint, name='temperature'),
    path('linear-regression/', linear_regression_endpoint, name='linear-regression'),
    path('getdata/', get_all_data, name='get-data'),
    path('list-files/', get_all_files, name='list_all_files'),
    path('flood-monitoring/', flood_monitoring_geojson, name='flood-monitoring'),
    path('map-visualization/', map_visualization_geojson, name='map-visualization')
]
