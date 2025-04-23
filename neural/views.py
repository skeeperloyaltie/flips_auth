from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import datetime
from db import fetch_db_collection  # Updated import path
from .models import preprocess_data, train_neural_network, evaluate_model, predict_latest
from monitor.utils import serialize_mongo_objects  # Import the utility function

class NeuralNetworkAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            water_levels_collection = fetch_db_collection('water_levels')

            water_levels = list(water_levels_collection.find())
            water_levels = serialize_mongo_objects(water_levels)

            # Preprocess data
            X, y, scaler = preprocess_data(water_levels)

            # Train neural network and get training history
            model, history = train_neural_network(X, y)

            # Evaluate model using cross-validation
            mse, _ = evaluate_model(model, X, y)

            # Predict the future water level based on the latest data entry
            latest_entry = water_levels[-1]
            prediction_data = {
                'timestamp': datetime.datetime.utcnow().toordinal(),
                'temperature': latest_entry['temperature'],
                'humidity': latest_entry['humidity']
            }

            predicted_level = predict_latest(model, prediction_data, scaler)

            # Prepare response data
            response_data = {
                'model_mse': mse,  # Model Mean Squared Error
                'predicted_level': predicted_level,  # Predicted water level
                'training_history': history.history  # Training history for loss visualization
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)