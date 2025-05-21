from django.urls import path
from .views import SubscribeView, PromotionalMessageView

urlpatterns = [
    path('subscribe/', SubscribeView.as_view(), name='subscribe'),
    path('promotions/', PromotionalMessageView.as_view(), name='promotions'),
]