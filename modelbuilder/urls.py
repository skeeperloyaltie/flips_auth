from django.urls import path
from .views import (
    CreateCustomModelAPIView,
    UserCustomModelsAPIView,
    GenerateHighchartsAPIView,
    GenerateReportAPIView,
)

urlpatterns = [
    path('create/', CreateCustomModelAPIView.as_view(), name='create_model'),
    path('user-models/', UserCustomModelsAPIView.as_view(), name='user_models'),
    path('generate-charts/', GenerateHighchartsAPIView.as_view(), name='generate_charts'),
    path('report/<int:model_id>/', GenerateReportAPIView.as_view(), name='generate_report'),
]
