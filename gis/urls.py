from django.urls import path
from .views import analyze_roi

urlpatterns = [
    path("analyze-roi/", analyze_roi, name="analyze_roi"),  # API endpoint
]
