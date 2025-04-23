from rest_framework import serializers
from .models import CustomModel, ModelFeature, RigAssignment

class ModelFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelFeature
        fields = ['id', 'feature_name', 'is_active']


class CustomModelSerializer(serializers.ModelSerializer):
    features = ModelFeatureSerializer(many=True, required=False)
    rig_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomModel
        fields = ['id', 'name', 'description', 'features', 'ml_model', 'rig_name', 'created_at', 'updated_at']

    def get_rig_name(self, obj):
        """
        Fetch the rig name (sensor_id) associated with the custom model.
        """
        rig_assignment = obj.rig_assignments.first()  # Assuming one rig per model
        if rig_assignment:
            return rig_assignment.rig.sensor_id
        return None
