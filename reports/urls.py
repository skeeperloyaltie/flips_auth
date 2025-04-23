from django.urls import path
from .views import CustomReportView, SubscriptionBasedReportView

urlpatterns = [
    path('reports/', CustomReportView.as_view(), name='custom-report'),
    path('subscription-reports/', SubscriptionBasedReportView.as_view(), name='subscription-report'),
]
