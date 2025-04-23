from django.urls import path
from .views import SubscribeView, PromotionalMessageView

urlpatterns = [
    path('subscribe/', SubscribeView.as_view(), name='subscribe'),
    path('promote/', PromotionalMessageView.as_view(), name='promote'),
]