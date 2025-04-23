# insurance/urls.py

from django.urls import path
from .views import InsurancePlanListView, InsuranceProfileView, InsuranceClaimView

urlpatterns = [
    path('plans/', InsurancePlanListView.as_view(), name='insurance-plans'),
    path('profile/', InsuranceProfileView.as_view(), name='insurance-profile'),
    path('claims/', InsuranceClaimView.as_view(), name='insurance-claims'),
]
