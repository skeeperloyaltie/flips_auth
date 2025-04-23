from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Measurement
from .serializers import MeasurementSerializer
from django.http import JsonResponse
from sklearn.linear_model import LinearRegression
import numpy as np
import pandas as pd
import os
import netCDF4 as nc
import rasterio
from PIL import Image
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt


class MeasurementListCreateView(generics.ListCreateAPIView):
    queryset = Measurement.objects.all()
    serializer_class = MeasurementSerializer
    permission_classes = [IsAuthenticated]

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def water_level_endpoint(request):
    measurements = Measurement.objects.values('timestamp', 'water_level')
    return JsonResponse(list(measurements), safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def humidity_endpoint(request):
    measurements = Measurement.objects.values('timestamp', 'humidity')
    return JsonResponse(list(measurements), safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def temperature_endpoint(request):
    measurements = Measurement.objects.values('timestamp', 'temperature')
    return JsonResponse(list(measurements), safe=False)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def linear_regression_endpoint(request):
    # Fetch the data
    data = Measurement.objects.all().values('timestamp', 'water_level', 'humidity', 'temperature')

    # Convert data to a DataFrame for easier manipulation
    df = pd.DataFrame(data)

    # Check if 'timestamp' exists and contains valid data
    if 'timestamp' not in df.columns or df['timestamp'].isnull().all():
        return JsonResponse({'error': 'No timestamp data available'}, status=400)

    # Convert timestamp to datetime and handle missing data
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    # Drop any rows where timestamp conversion failed
    df.dropna(subset=['timestamp'], inplace=True)

    if df.empty:
        return JsonResponse({'error': 'No valid data to perform linear regression'}, status=400)

    # Define features and target
    features = df[['timestamp', 'humidity', 'temperature']].values
    target = df['water_level'].values

    # Fit the model
    model = LinearRegression()
    model.fit(features, target)

    # Predict
    predictions = model.predict(features)

    # Add predictions to the DataFrame
    df['predicted_water_level'] = predictions

    # Return the predictions
    response_data = {
        'timestamps': df['timestamp'].tolist(),
        'actual_water_levels': df['water_level'].tolist(),
        'predicted_water_levels': df['predicted_water_level'].tolist()
    }

    return JsonResponse(response_data, safe=False)


def read_all_data():
    data_dir = os.path.join(settings.BASE_DIR, 'data')
    all_data = {}

    for root, dirs, files in os.walk(data_dir):
        if files:
            folder_name = os.path.relpath(root, data_dir)
            all_data[folder_name] = []

            for file in files:
                file_path = os.path.join(root, file)
                file_extension = os.path.splitext(file)[1].lower()

                try:
                    if file_extension == '.csv':
                        all_data[folder_name].append({
                            'file_name': file,
                            'data': 'CSV file detected, reading skipped'
                        })
                    elif file_extension == '.nc':
                        all_data[folder_name].append({
                            'file_name': file,
                            'data': 'NetCDF file detected, reading skipped'
                        })
                    elif file_extension in ['.tif', '.tiff']:
                        all_data[folder_name].append({
                            'file_name': file,
                            'data': 'TIFF file detected, reading skipped'
                        })
                    elif file_extension in ['.png', '.jpeg', '.jpg']:
                        all_data[folder_name].append({
                            'file_name': file,
                            'data': 'Image file detected, reading skipped'
                        })
                    elif file_extension in ['.xlsx']:
                        all_data[folder_name].append({
                            'file_name': file,
                            'data': 'Excel file detected, reading skipped'
                        })
                    else:
                        print(f"Skipping unsupported file type: {file_path}")
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    return all_data

@csrf_exempt
def get_all_data(request):
    data = read_all_data()
    return JsonResponse(data, safe=False)

import os
from django.conf import settings
from django.http import JsonResponse

def list_all_files():
    data_dir = os.path.join(settings.BASE_DIR, 'data')
    all_files = {}

    for root, dirs, files in os.walk(data_dir):
        if files:
            # Get the folder name relative to the data_dir
            folder_name = os.path.relpath(root, data_dir)
            all_files[folder_name] = []

            for file in files:
                file_path = os.path.join(root, file)
                all_files[folder_name].append(file_path)

    return all_files

# Example usage in a Django view
def get_all_files(request):
    data = list_all_files()
    return JsonResponse(data, safe=False)

from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Measurement
from django.core.cache import cache

def serialize_to_geojson(measurements):
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }
    for measurement in measurements:
        geojson["features"].append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [measurement.longitude, measurement.latitude]
            },
            "properties": {
                "id": measurement.id,
                "water_level": measurement.water_level,
                "humidity": measurement.humidity,
                "temperature": measurement.temperature
            }
        })
    return geojson

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def flood_monitoring_geojson(request):
    # Check cache first
    cached_data = cache.get('flood_geojson')
    if cached_data:
        return JsonResponse(cached_data, safe=False)
    
    measurements = Measurement.objects.filter(water_level__gt=10).only('id', 'water_level', 'latitude', 'longitude', 'humidity', 'temperature')
    geojson = serialize_to_geojson(measurements)
    
    # Cache the response for 10 minutes
    cache.set('flood_geojson', geojson, 600)
    
    return JsonResponse(geojson, safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def map_visualization_geojson(request):
    # Check cache first
    cached_data = cache.get('map_geojson')
    if cached_data:
        return JsonResponse(cached_data, safe=False)
    
    measurements = Measurement.objects.all().only('id', 'water_level', 'latitude', 'longitude', 'humidity', 'temperature')
    geojson = serialize_to_geojson(measurements)
    
    # Cache the response for 10 minutes
    cache.set('map_geojson', geojson, 600)
    
    return JsonResponse(geojson, safe=False)


