from django.db import models
from django.contrib.auth.models import User
from userprofile.models import UserProfile
from monitor.models import Rig


class CustomModel(models.Model):
    """
    Represents a user-defined water analysis model.
    """
    APPROVAL_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    ML_MODEL_CHOICES = [
        ('SVM', 'Support Vector Machine'),
        ('Random Forest', 'Random Forest'),
        ('Neural Network', 'Neural Network'),
        ('KNN', 'K-Nearest Neighbors'),
        ('Linear Regression', 'Linear Regression'),
        ('Decision Tree', 'Decision Tree'),
    ]

    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='custom_models')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    ml_model = models.CharField(max_length=50, choices=ML_MODEL_CHOICES, default='Random Forest')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approval_status = models.CharField(max_length=50, choices=APPROVAL_STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"{self.name} (User: {self.user_profile.user.username})"


class ModelFeature(models.Model):
    """
    Represents a feature (e.g., water level, temperature) in a CustomModel.
    """
    custom_model = models.ForeignKey(CustomModel, on_delete=models.CASCADE, related_name='features')
    feature_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.feature_name} (Model: {self.custom_model.name})"


class RigAssignment(models.Model):
    """
    Tracks which rig is used in a CustomModel.
    """
    custom_model = models.ForeignKey(CustomModel, on_delete=models.CASCADE, related_name='rig_assignments')
    rig = models.ForeignKey(Rig, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rig {self.rig.sensor_id} assigned to {self.custom_model.name}"
