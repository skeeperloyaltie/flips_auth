# monitor/urls.py
from django.urls import path
from .views import SensorDataAPIView, GraphDataAPIView, water_level_list, rig_list, get_rigs, CriticalPointAPIView, \
    PredictedDataAPIView, ModelPerformanceAPIView, get_rig_location

urlpatterns = [
    path('sensor-data/', SensorDataAPIView.as_view(), name='sensor_data'),
    path('water-levels/', water_level_list, name='water_level_list'),
    path('rigs/', rig_list, name='rig_list'),
    path('graph-data/', GraphDataAPIView.as_view(), name='graph_data'),
    path('get-rigs/', get_rigs, name='get-rigs'),
    path('critical-point/', CriticalPointAPIView.as_view(), name='critical_point'),
    path('predicted-data/', PredictedDataAPIView.as_view(), name='predicted_data'),  # Add this line
    path("performance/", ModelPerformanceAPIView.as_view(), name="model-performance"),
    path('rig-locations/', get_rig_location, name='rig-locations'),

]