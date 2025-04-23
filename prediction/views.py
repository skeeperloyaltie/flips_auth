from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import TimeSlot, PredictionResult
from .serializers import TimeSlotSerializer, PredictionResultSerializer
from django.contrib.auth.models import User
from django.utils import timezone
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from monitoring.models import Measurement  # Import Measurement model

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_time_slot(request):
    serializer = TimeSlotSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_predictions(request):
    try:
        user = request.user
        time_slots = TimeSlot.objects.filter(user=user)
        predictions = []

        for time_slot in time_slots:
            # Fetch data from the Measurement model
            measurements = Measurement.objects.filter(timestamp__range=[time_slot.start_time, time_slot.end_time])
            df = pd.DataFrame(list(measurements.values('timestamp', 'water_level', 'humidity', 'temperature')))
            df['timestamp'] = pd.to_datetime(df['timestamp']).map(pd.Timestamp.timestamp)

            # Define features and target
            features = df[['timestamp', 'humidity', 'temperature']].values
            target = df['water_level'].values

            # Fit the model
            model = LinearRegression()
            model.fit(features, target)

            # Generate predictions
            timestamps = pd.date_range(time_slot.start_time, time_slot.end_time, freq='H')
            feature_data = np.array([[pd.Timestamp.timestamp(ts), np.mean(df['humidity']), np.mean(df['temperature'])] for ts in timestamps])
            predicted_values = model.predict(feature_data)

            data = {
                'timestamps': timestamps.tolist(),
                'predicted_values': predicted_values.tolist()
            }

            prediction_result, created = PredictionResult.objects.get_or_create(time_slot=time_slot, defaults={'result_data': data})
            if not created:
                prediction_result.result_data = data
                prediction_result.save()
                
            predictions.append(PredictionResultSerializer(prediction_result).data)

        return Response(predictions)

    except Exception as e:
        return Response({"error": str(e)}, status=500)
