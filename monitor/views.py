# monitor/views.py
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from userprofile.models import UserProfile
from .models import PredictedWaterLevels, Rig, WaterLevelData, CriticalThreshold
from .serializers import RigSerializer, WaterLevelDataSerializer
import json
from datetime import datetime, timedelta
import logging
from .ml_utils import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_time_threshold(user_profile):
    """Determines the time threshold based on the subscription plan."""
    current_time = now()
    if user_profile.subscription_plan == 'government':
        return current_time - timedelta(minutes=10)
    elif user_profile.subscription_plan == 'corporate':
        return current_time - timedelta(hours=2)
    elif user_profile.subscription_plan == 'free':
        return current_time - timedelta(minutes=30)
    return None

from django.utils.timezone import is_naive, make_aware
from django.utils.dateparse import parse_datetime

class SensorDataAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            logger.info(f"Received data: {data}")

            sensor_id = data.get('sensorID')
            if not sensor_id:
                return Response({'error': 'Sensor ID is required'}, status=status.HTTP_400_BAD_REQUEST)

            rig = Rig.objects.filter(sensor_id=sensor_id).first()
            if not rig:
                return Response({'error': f'Rig with sensor_id {sensor_id} does not exist'}, status=status.HTTP_404_NOT_FOUND)

            # Validate and use the timestamp from the request
            raw_timestamp = data.get('timestamp')
            if not raw_timestamp:
                return Response({'error': 'Timestamp is required'}, status=status.HTTP_400_BAD_REQUEST)

            # Parse the timestamp
            timestamp = parse_datetime(raw_timestamp)
            if timestamp is None:
                return Response({'error': 'Invalid timestamp format'}, status=status.HTTP_400_BAD_REQUEST)

            # Ensure the timestamp is timezone-aware
            if is_naive(timestamp):
                timestamp = make_aware(timestamp)

            data['timestamp'] = timestamp  # Use the corrected timestamp
            data['rig'] = rig.sensor_id  # Ensure the rig is validated from DB

            serializer = WaterLevelDataSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': 'Data sent to server'}, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except json.JSONDecodeError:
            return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return Response({'error': 'Internal Server Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def water_level_list(request):
    user_profile = request.user.profile
    time_threshold = get_time_threshold(user_profile)
    
    if not time_threshold:
        return Response({'error': 'Invalid subscription plan'}, status=status.HTTP_400_BAD_REQUEST)
    
    water_levels = WaterLevelData.objects.filter(timestamp__gte=time_threshold)
    serializer = WaterLevelDataSerializer(water_levels, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rig_list(request):
    rigs = Rig.objects.all()
    serializer = RigSerializer(rigs, many=True)
    return Response(serializer.data)


def get_rigs(request):
    # Retrieve all rigs from the database
    rigs = Rig.objects.all()

    # Prepare a list of rig data, including dynamically fetched locations
    data = [
        {
            "rig_id": rig.id,
            "sensor_id": rig.sensor_id,
            "location": rig.location,
            "latitude": rig.latitude,
            "longitude": rig.longitude
        }
        for rig in rigs
    ]

    return JsonResponse(data, safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_rig_location(request):
    """
    Retrieves the location (latitude and longitude) of each rig.
    """
    # Fetch all rigs and their latitude/longitude
    rigs = Rig.objects.all().values('sensor_id', 'latitude', 'longitude')
    data = [{"sensor_id": rig['sensor_id'], "latitude": rig['latitude'], "longitude": rig['longitude']} for rig in rigs]
    return Response(data, status=status.HTTP_200_OK)

from django.utils.timezone import now
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
import logging
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils.timezone import now
from datetime import timedelta
import logging

# Initialize logger
logger = logging.getLogger(__name__)

class GraphDataAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user_profile = request.user.profile
            current_time = now()

            # Log fetching attempt
            logger.info(f"Fetching water levels for user: {request.user.username}")

            # Retrieve all rigs and map them by sensor_id for easier access
            rigs = Rig.objects.all()
            rig_map = {rig.sensor_id: rig for rig in rigs}

            logger.info(f"User subscription plan: {user_profile.subscription_plan}")

            # Determine time threshold based on subscription plan
            time_threshold = self.get_time_threshold(user_profile.subscription_plan, request.user.is_staff, current_time)
            logger.info(f'User subscription: {user_profile.subscription_plan} and this is a staff? {request.user.is_staff}')
            if time_threshold is None:
                logger.error("Invalid subscription plan.")
                return Response({'error': 'Invalid subscription plan'}, status=status.HTTP_400_BAD_REQUEST)

            # Filter water level data based on the determined time threshold
            filtered_levels = WaterLevelData.objects.filter(timestamp__gte=time_threshold)

            # Serialize and format the filtered data
            serializer = WaterLevelDataSerializer(filtered_levels, many=True)
            formatted_data = self.format_for_highcharts(serializer.data, rig_map)

            # Prepare the response data
            response_data = {'current_data': formatted_data}

            # Include prediction data for government users
            if user_profile.subscription_plan == 'government' and filtered_levels.exists():
                prediction_response = self.prepare_prediction_data(filtered_levels, rigs)
                response_data.update(prediction_response)

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in GraphDataAPIView: {str(e)}")
            return Response({'error': 'An error occurred while processing the request.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_time_threshold(self, subscription_plan, is_staff, current_time):
        """
        Determine the time threshold for data retrieval based on subscription plan and staff status.
        """
        if subscription_plan and subscription_plan.name == 'government' or is_staff:
            logger.info("Setting time threshold to 1 day for government or staff user.")
            return current_time - timedelta(minutes=60)  # longest threshold, e.g., 1 day

        if subscription_plan and subscription_plan.name == 'corporate':
            logger.info("Setting time threshold to 2 hours for corporate user.")
            return current_time - timedelta(hours=2)
        elif subscription_plan and subscription_plan.name == 'free':
            logger.info("Setting time threshold to 30 minutes for free user.")
            return current_time - timedelta(minutes=30)

        logger.warning("Invalid subscription plan encountered.")
        return None


    def format_for_highcharts(self, data, rig_map):
        """
        Format data for Highcharts by organizing it into structured arrays for each rig.
        """
        formatted_data = {}

        for item in data:
            rig_name = rig_map.get(item['rig']).sensor_id if rig_map.get(item['rig']) else item['rig']
            if rig_name not in formatted_data:
                formatted_data[rig_name] = {
                    'timestamps': [],
                    'levels': [],
                    'temperatures': [],
                    'humidities': []
                }

            # Choose the level field, prioritizing `waterLevel` if available
            water_level = item.get('waterLevel', item.get('level'))
            formatted_data[rig_name]['timestamps'].append(item['timestamp'])
            formatted_data[rig_name]['levels'].append(water_level)
            formatted_data[rig_name]['temperatures'].append(item['temperature'])
            formatted_data[rig_name]['humidities'].append(item['humidity'])

        return formatted_data

    def prepare_prediction_data(self, filtered_levels, rigs):
        """
        Prepare predicted levels and model accuracy data for government users.
        """
        # Prepare data for model training
        data_for_training = list(filtered_levels.values('timestamp', 'temperature', 'humidity', 'level'))

        # Train models and obtain accuracies
        models, accuracies, accuracy_percentages = train_models(data_for_training)
        latest_entry = filtered_levels.latest('timestamp')

        # Prepare prediction input based on latest entry
        prediction_data = {
            'timestamp': latest_entry.timestamp.toordinal(),
            'temperature': latest_entry.temperature,
            'humidity': latest_entry.humidity
        }

        # Predict levels for each rig using trained models
        predicted_levels = {}
        for model_name, model in models.items():
            predicted_level = predict(model, prediction_data)
            predicted_levels[model_name] = {rig.sensor_id: predicted_level for rig in rigs}

        return {
            'predicted_data': predicted_levels,
            'model_accuracies': accuracies,
            'accuracy_percentages': accuracy_percentages
        }




# New Endpoint
class CriticalPointAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            critical_threshold = CriticalThreshold.objects.latest('id')  # Get the latest threshold settings
        except CriticalThreshold.DoesNotExist:
            return Response({'error': 'Critical thresholds are not set'}, status=status.HTTP_400_BAD_REQUEST)

        current_time = now()
        time_threshold = current_time - timedelta(hours=3)  # Consider data from the last hour

        water_levels = WaterLevelData.objects.filter(timestamp__gte=time_threshold)
        if not water_levels.exists():
            return Response({'error': 'No water level data found in the specified period'}, status=status.HTTP_404_NOT_FOUND)

        avg_level = sum(water_levels.values_list('level', flat=True)) / water_levels.count()
        avg_temp = sum(water_levels.values_list('temperature', flat=True)) / water_levels.count()
        avg_humid = sum(water_levels.values_list('humidity', flat=True)) / water_levels.count()

        response_data = {
            'average_water_level': avg_level,
            'average_temperature': avg_temp,
            'average_humidity': avg_humid,
        }

        # Determine alert level
        alert_level = 'Normal'
        if avg_level > critical_threshold.water_level_threshold or avg_temp > critical_threshold.temperature_threshold or avg_humid > critical_threshold.humidity_threshold:
            time_threshold_critical = current_time - timedelta(minutes=10)
            critical_levels = WaterLevelData.objects.filter(timestamp__gte=time_threshold_critical)

            avg_level_critical = sum(critical_levels.values_list('level', flat=True)) / critical_levels.count()
            avg_temp_critical = sum(critical_levels.values_list('temperature', flat=True)) / critical_levels.count()
            avg_humid_critical = sum(critical_levels.values_list('humidity', flat=True)) / critical_levels.count()

            if avg_level_critical > critical_threshold.water_level_threshold or avg_temp_critical > critical_threshold.temperature_threshold or avg_humid_critical > critical_threshold.humidity_threshold:
                if avg_level_critical > critical_threshold.water_level_threshold * 1.2 or avg_temp_critical > critical_threshold.temperature_threshold * 1.2 or avg_humid_critical > critical_threshold.humidity_threshold * 1.2:
                    alert_level = 'Critical'
                else:
                    alert_level = 'Warning'
            else:
                alert_level = 'Danger'

        response_data['alert_level'] = alert_level
        return Response(response_data, status=status.HTTP_200_OK)
    
    
from django.utils.timezone import now
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
import logging
import pandas as pd
from datetime import timedelta

logger = logging.getLogger(__name__)

class PredictedDataAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Assume time_threshold and rigs setup as per the user's subscription plan
        current_time = now()
        time_threshold = current_time - timedelta(minutes=10)

        # Fetch water level data within the time range
        rigs = Rig.objects.all()

        filtered_levels = WaterLevelData.objects.filter(timestamp__gte=time_threshold).order_by('-timestamp')
        
        if not filtered_levels.exists():
            logger.info("No water level data found for the specified time range.")
            return Response({'error': 'No water level data found'}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the filtered data and convert it to a DataFrame
        serializer = WaterLevelDataSerializer(filtered_levels, many=True)
        data_for_training = pd.DataFrame(serializer.data)
        
        # Check if either `waterLevel` or `level` is present, prioritize `waterLevel`
        if 'waterLevel' in data_for_training.columns:
            column_to_use = 'waterLevel'
        elif 'level' in data_for_training.columns:
            column_to_use = 'level'
        else:
            logger.error("Data missing 'waterLevel' or 'level' column for training.")
            return Response({'error': 'Data missing "waterLevel" or "level" column'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Rename the column to `waterLevel` for consistency
        data_for_training.rename(columns={column_to_use: 'waterLevel'}, inplace=True)

        # Log the DataFrame columns to ensure the correct column setup
        logger.info(f"Columns in data_for_training after renaming: {data_for_training.columns.tolist()}")

        # Train models
        try:
            models, accuracies, accuracy_percentages = train_models(data_for_training)
            if not models:
                logger.error("No models returned from training.")
                return Response({'error': 'Model training failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Exception during model training: {str(e)}")
            return Response({'error': 'Failed to train models'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Prepare latest data for predictions
        latest_entry = filtered_levels.latest('timestamp')
        prediction_data = {
            'timestamp': latest_entry.timestamp.toordinal(),
            'temperature': latest_entry.temperature,
            'humidity': latest_entry.humidity
        }

        predicted_levels = {}
        for model_name, model in models.items():
            predicted_levels[model_name] = []
            for rig in rigs:
                sensor_id = rig.sensor_id
                prediction_input = pd.DataFrame([prediction_data])

                try:
                    predicted_level = predict(model, prediction_data)
                    predicted_levels[model_name].append({
                        'name': sensor_id,
                        'y': predicted_level
                    })
                    
                    # Log predictions to PredictedWaterLevels
                    PredictedWaterLevels.objects.create(
                        rig=rig,
                        timestamp=latest_entry.timestamp,
                        predicted_level=predicted_level,
                        model_name=model_name,
                        accuracy=accuracies[model_name]
                    )
                except Exception as e:
                    logger.error(f"Exception during prediction for model {model_name} at rig {sensor_id}: {str(e)}")
                    return Response({'error': 'Failed to predict water levels'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Prepare and return response data
        response_data = {
            'predicted_data': predicted_levels,
            'model_details': {
                'models': list(models.keys()),
                'accuracies': accuracies,
                'accuracy_percentages': accuracy_percentages
            },
            'previous_predictions': list(PredictedWaterLevels.objects.filter(
                timestamp__gte=current_time - timedelta(minutes=5)
            ).values('timestamp', 'predicted_level'))
        }
        
        logger.info(f"Response data: {response_data}")
        return Response(response_data, status=status.HTTP_200_OK)

class ModelPerformanceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            # Get the user's profile and subscription plan
            user_profile = UserProfile.objects.get(user=request.user)
            current_time = now()

            # Determine time threshold based on the subscription plan
            time_threshold = self.get_time_threshold(user_profile, current_time)
            if time_threshold is None:
                return Response({'error': 'Invalid subscription plan'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Filter data based on the time threshold
            water_level_data = WaterLevelData.objects.filter(timestamp__gte=time_threshold)

            # Ensure there is data to process
            if not water_level_data.exists():
                return Response({'error': 'No data available within the specified time range'}, status=status.HTTP_404_NOT_FOUND)

            # Serialize data for response
            serializer = WaterLevelDataSerializer(water_level_data, many=True)
            structured_data = self.format_performance_data(serializer.data)

            response_data = {'current_performance_data': structured_data}

            # Add model prediction accuracy if government user
            if user_profile.subscription_plan.name == 'government':
                accuracy_data = self.calculate_model_performance(water_level_data)
                response_data.update(accuracy_data)

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in ModelPerformanceAPIView: {str(e)}")
            return Response({'error': 'An error occurred while processing the request'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def format_performance_data(self, data):
        """
        Formats performance data for visualization.
        """
        formatted_data = {}
        for item in data:
            sensor_id = item.get('rig')
            if sensor_id not in formatted_data:
                formatted_data[sensor_id] = {
                    'timestamps': [],
                    'levels': [],
                    'temperatures': [],
                    'humidities': []
                }
            formatted_data[sensor_id]['timestamps'].append(item['timestamp'])
            formatted_data[sensor_id]['levels'].append(item.get('waterLevel'))
            formatted_data[sensor_id]['temperatures'].append(item['temperature'])
            formatted_data[sensor_id]['humidities'].append(item['humidity'])

        return formatted_data

    def calculate_model_performance(self, water_level_data):
        """
        Calculates model performance metrics for government users.
        """
        data_for_training = list(water_level_data.values('timestamp', 'temperature', 'humidity', 'level'))
        models, accuracies, accuracy_percentages = train_models(data_for_training)

        return {
            'model_accuracies': accuracies,
            'accuracy_percentages': accuracy_percentages
        }

    def get_time_threshold(self, user_profile, current_time):
        """
        Determine the time threshold for data retrieval based on subscription plan.
        """
        subscription_plan = user_profile.subscription_plan

        if subscription_plan and subscription_plan.name == 'government' or user_profile.user.is_staff:
            logger.info("Setting time threshold to 1 day for government or staff user.")
            return current_time - timedelta(days=1)  # longest threshold, e.g., 1 day

        if subscription_plan and subscription_plan.name == 'corporate':
            logger.info("Setting time threshold to 2 hours for corporate user.")
            return current_time - timedelta(hours=2)
        elif subscription_plan and subscription_plan.name == 'free':
            logger.info("Setting time threshold to 30 minutes for free user.")
            return current_time - timedelta(minutes=30)

        logger.warning("Invalid subscription plan encountered.")
        return None


