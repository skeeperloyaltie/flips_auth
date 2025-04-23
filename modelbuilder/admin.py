from django.contrib import admin
from .models import CustomModel, ModelFeature, RigAssignment


class ModelFeatureInline(admin.TabularInline):
    """
    Inline admin for Model Features.
    Allows adding and editing features directly within the CustomModel admin view.
    """
    model = ModelFeature
    extra = 1


class RigAssignmentInline(admin.TabularInline):
    """
    Inline admin for Rig Assignments.
    Allows viewing and editing rig assignments directly within the CustomModel admin view.
    """
    model = RigAssignment
    extra = 1


@admin.register(CustomModel)
class CustomModelAdmin(admin.ModelAdmin):
    """
    Admin configuration for CustomModel.
    Includes inlines for associated features and rig assignments.
    """
    list_display = ('name', 'user_profile', 'ml_model', 'approval_status', 'created_at', 'updated_at')
    list_filter = ('approval_status', 'ml_model', 'created_at')
    search_fields = ('name', 'user_profile__user__username', 'ml_model')
    inlines = [ModelFeatureInline, RigAssignmentInline]

    def get_queryset(self, request):
        """
        Customize the queryset to ensure admins can see all models.
        """
        return super().get_queryset(request).select_related('user_profile')


@admin.register(ModelFeature)
class ModelFeatureAdmin(admin.ModelAdmin):
    """
    Admin configuration for ModelFeature.
    Allows managing features separately from CustomModel if needed.
    """
    list_display = ('feature_name', 'custom_model', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('feature_name', 'custom_model__name')


@admin.register(RigAssignment)
class RigAssignmentAdmin(admin.ModelAdmin):
    """
    Admin configuration for RigAssignment.
    Allows tracking and managing rigs assigned to models.
    """
    list_display = ('rig', 'custom_model', 'assigned_at')
    search_fields = ('rig__sensor_id', 'custom_model__name')
