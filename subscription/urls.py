# urls.py

from django.urls import path
from .views import SubscriptionPlanListCreateView, check_user_subscription, subscribe, get_dashboard_url, SubscriptionDetailsView, UpgradePromptView

urlpatterns = [
    path('plans/', SubscriptionPlanListCreateView.as_view(), name='subscription-plans'),
    path('plans/<int:id>/', SubscriptionPlanDetailView.as_view(), name='plan-detail'),

    path('status/', check_user_subscription, name='check-subscription-status'),
    path('subscribe/', subscribe, name='subscribe'),
    path('get-dashboard-url/', get_dashboard_url, name='get-dashboard-url'),
    path('details/', SubscriptionDetailsView.as_view(), name='subscription_details'),
    path('upgrade/', UpgradePromptView.as_view(), name='subscription-upgrade'),

]



