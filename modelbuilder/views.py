from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import CustomModel, ModelFeature
from .serializers import CustomModelSerializer, ModelFeatureSerializer
from userprofile.models import UserProfile
from django.utils.timezone import now
from datetime import timedelta
from monitor.models import WaterLevelData


import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import CustomModel, ModelFeature
from .serializers import CustomModelSerializer
from userprofile.models import UserProfile

# Configure logging
logger = logging.getLogger(__name__)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import CustomModel, ModelFeature
from .serializers import CustomModelSerializer
from userprofile.models import UserProfile
from monitor.models import Rig
import logging

logger = logging.getLogger(__name__)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import CustomModel, ModelFeature
from monitor.models import Rig
from userprofile.models import UserProfile
import logging

logger = logging.getLogger(__name__)

class CreateCustomModelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        API for creating a custom model with rig (identified by sensor_id), attributes, and ML model selection.
        """
        try:
            user_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            logger.warning(f"UserProfile not found for user: {request.user.username}")
            return Response({'error': 'User profile not found.'}, status=404)

        # Log input data
        logger.info(f"Received data for model creation: {request.data}")

        # Validate input
        name = request.data.get('name')
        description = request.data.get('description', '')
        attributes = request.data.get('attributes', [])
        sensor_id = request.data.get('rig_id')  # Using sensor_id instead of numeric rig_id
        ml_model = request.data.get('ml_model')  # Selected machine learning model

        if not name:
            logger.error("Model name is missing from the request.")
            return Response({'error': 'Model name is required.'}, status=400)

        if not attributes:
            logger.error("No attributes provided for the model.")
            return Response({'error': 'At least one attribute is required.'}, status=400)

        if not sensor_id:
            logger.error("No rig (sensor_id) provided for the model.")
            return Response({'error': 'Rig (sensor_id) selection is required.'}, status=400)

        if not ml_model:
            logger.error("No machine learning model selected.")
            return Response({'error': 'Machine learning model is required.'}, status=400)

        try:
            rig = Rig.objects.get(sensor_id=sensor_id)
        except Rig.DoesNotExist:
            logger.error(f"Rig with sensor_id {sensor_id} not found.")
            return Response({'error': 'Selected rig not found.'}, status=404)

        # Check for duplicate model names
        if CustomModel.objects.filter(user_profile=user_profile, name=name).exists():
            logger.warning(f"Duplicate model name detected for user: {request.user.username}, model name: {name}")
            return Response({'error': 'Model with this name already exists.'}, status=400)

        # Log successful validation
        logger.info(f"Creating model for user: {request.user.username}, name: {name}, description: {description}, attributes: {attributes}, rig: {rig.sensor_id}, ML model: {ml_model}")

        # Create custom model
        custom_model = CustomModel.objects.create(
            user_profile=user_profile,
            name=name,
            description=description,
            ml_model=ml_model
        )

        # Add features selected by the user
        for feature_name in attributes:
            ModelFeature.objects.create(custom_model=custom_model, feature_name=feature_name)
            logger.info(f"Added feature '{feature_name}' to model '{name}'")

        return Response({'message': 'Model created successfully.'}, status=201)







class UserCustomModelsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        API to fetch all custom models for the logged-in user in descending order.
        """
        try:
            user_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User profile not found.'}, status=404)

        custom_models = CustomModel.objects.filter(user_profile=user_profile).order_by('-created_at')
        serializer = CustomModelSerializer(custom_models, many=True)
        return Response(serializer.data)


class GenerateHighchartsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        API to generate Highcharts data based on the selected features.
        """
        features = request.data.get('features', [])
        time_range = request.data.get('time_range', 6)  # Default: last 6 hours

        if not features:
            return Response({'error': 'No features selected.'}, status=400)

        # Filter water level data
        water_levels = WaterLevelData.objects.filter(
            timestamp__gte=now() - timedelta(hours=time_range)
        ).values('timestamp', 'level', 'temperature', 'humidity')

        # Prepare Highcharts data
        chart_data = {
            'categories': [entry['timestamp'] for entry in water_levels],
            'series': []
        }

        if 'Water Level' in features:
            chart_data['series'].append({
                'name': 'Water Level',
                'data': [entry['level'] for entry in water_levels]
            })

        if 'Temperature' in features:
            chart_data['series'].append({
                'name': 'Temperature',
                'data': [entry['temperature'] for entry in water_levels]
            })

        if 'Humidity' in features:
            chart_data['series'].append({
                'name': 'Humidity',
                'data': [entry['humidity'] for entry in water_levels]
            })

        return Response(chart_data)

class UpdateCustomModelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, model_id):
        """
        API to update a custom model (requires admin approval).
        """
        try:
            custom_model = CustomModel.objects.get(id=model_id, user_profile__user=request.user)
        except CustomModel.DoesNotExist:
            return Response({'error': 'Model not found or access denied.'}, status=404)

        # Validate inputs
        name = request.data.get('name', custom_model.name)
        description = request.data.get('description', custom_model.description)
        attributes = request.data.get('attributes', [])

        # Update model fields
        custom_model.name = name
        custom_model.description = description
        custom_model.save()

        # Update features
        if attributes:
            custom_model.features.all().delete()
            for feature_name in attributes:
                ModelFeature.objects.create(custom_model=custom_model, feature_name=feature_name)

        return Response({'message': 'Model updated successfully. Pending admin approval.'}, status=200)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.files.base import ContentFile
from django.http import FileResponse
from .models import CustomModel, ModelFeature
from monitor.models import Rig, WaterLevelData
from monitor.ml_utils import train_models
from django.utils.timezone import now
from datetime import timedelta
import matplotlib.pyplot as plt
from io import BytesIO
import logging
import pandas as pd
from fpdf import FPDF

logger = logging.getLogger(__name__)

from django.http import FileResponse
from fpdf import FPDF
import matplotlib.pyplot as plt
from io import BytesIO
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import CustomModel, ModelFeature
from monitor.models import WaterLevelData, Rig
from monitor.ml_utils import train_models
from datetime import timedelta
from django.utils.timezone import now
import pandas as pd
import logging

logger = logging.getLogger(__name__)

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Image
import os
import tempfile
from django.http import FileResponse
import matplotlib.pyplot as plt
from io import BytesIO
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import CustomModel, ModelFeature, RigAssignment
from monitor.models import WaterLevelData
from monitor.ml_utils import train_models
from datetime import timedelta
from django.utils.timezone import now
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class GenerateReportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, model_id):
        """
        API to generate a PDF report for a custom model with visualizations and insights.
        """
        try:
            # Fetch the custom model
            custom_model = CustomModel.objects.get(id=model_id, user_profile__user=request.user)
        except CustomModel.DoesNotExist:
            logger.error(f"CustomModel with id {model_id} not found for user {request.user.username}.")
            return Response({'error': 'Model not found or access denied.'}, status=404)

        try:
            # Validate rig assignment and approval status
            rig_assignment = RigAssignment.objects.filter(custom_model=custom_model).first()
            if not rig_assignment:
                logger.error(f"No rig assigned to model {custom_model.name}.")
                return Response({'error': 'No rig assigned to the model.'}, status=400)

            if custom_model.approval_status != 'Approved':
                logger.warning(f"Rig assigned to model {custom_model.name} is not approved.")
                return Response({'error': 'Associated rig is not approved for analysis.'}, status=400)

            rig = rig_assignment.rig
            logger.info(f"Generating report for approved rig: {rig.sensor_id} in model {custom_model.name}")

            # Fetch water level data for the rig
            attributes = custom_model.features.values_list('feature_name', flat=True)
            water_levels = WaterLevelData.objects.filter(
                rig=rig,
                timestamp__gte=now() - timedelta(hours=6)
            ).values('timestamp', 'temperature', 'humidity', 'level')

            if not water_levels.exists():
                logger.info(f"No data available for rig {rig.sensor_id} in the last 6 hours.")
                return Response({'error': 'No data available for the selected rig and time range.'}, status=404)

            # Convert data to a DataFrame
            data = pd.DataFrame(list(water_levels))
            logger.info(f"Data fetched for analysis: {data.head()}")

            # Perform analysis using ML models
            models, accuracies, accuracy_percentages = train_models(data)

            # Generate visualizations and save to a temporary file
            temp_image_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            try:
                fig, ax = plt.subplots()
                for attribute in attributes:
                    attribute_col = attribute.lower().replace(" ", "_")
                    if attribute_col in data.columns:
                        ax.plot(data['timestamp'], data[attribute_col], label=attribute)
                ax.legend()
                ax.set_title(f"Visualization for Rig: {rig.sensor_id}")
                ax.set_xlabel('Timestamp')
                ax.set_ylabel('Values')
                plt.savefig(temp_image_file.name)
                plt.close(fig)

                # Generate PDF using ReportLab
                pdf_buffer = BytesIO()
                c = canvas.Canvas(pdf_buffer, pagesize=letter)

                # Add report title and description
                c.setFont("Helvetica-Bold", 16)
                c.drawString(100, 750, f"Report for Model: {custom_model.name}")
                c.setFont("Helvetica", 12)
                c.drawString(100, 730, f"Description: {custom_model.description}")

                # Add model accuracy insights
                c.setFont("Helvetica-Bold", 14)
                c.drawString(100, 700, "Model Accuracy and Insights:")
                y = 680
                for model_name, accuracy in accuracy_percentages.items():
                    c.setFont("Helvetica", 12)
                    c.drawString(100, y, f"{model_name}: {accuracy:.2f}%")
                    y -= 20

                # Add visualization image
                if os.path.exists(temp_image_file.name):
                    c.drawImage(temp_image_file.name, 50, 400, width=500, height=300)

                # Finalize the PDF
                c.save()

                # Return the PDF as a response
                pdf_buffer.seek(0)
                logger.info(f"Report for model {custom_model.name} generated successfully.")
                return FileResponse(pdf_buffer, as_attachment=True, filename=f"{custom_model.name}_report.pdf")
            finally:
                # Cleanup temporary image file using os.unlink
                temp_image_file.close()
                os.unlink(temp_image_file.name)

        except Exception as e:
            logger.error(f"Error generating report for model {custom_model.name}: {str(e)}")
            return Response({'error': 'An error occurred while generating the report.'}, status=500)






class DeleteCustomModelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, model_id):
        """
        API to delete a custom model (requires admin approval).
        """
        try:
            custom_model = CustomModel.objects.get(id=model_id, user_profile__user=request.user)
        except CustomModel.DoesNotExist:
            return Response({'error': 'Model not found or access denied.'}, status=404)

        # Mark for deletion (admin approval required)
        custom_model.delete()
        return Response({'message': 'Model marked for deletion. Pending admin approval.'}, status=200)
