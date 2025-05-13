from django.urls import path
from .views import UserSubscriptionStatusView, PaymentMethodsView, PaymentPageView, VerificationPageView, \
    CheckUserSubscriptionView, VerifyPaymentAPIView, UserPaymentHistoryView

urlpatterns = [

    path('verify-subscription/', UserSubscriptionStatusView.as_view(), name='verify-subscription'),
    path('methods/', PaymentMethodsView.as_view(), name='payment-methods'),
    path('verification/', VerificationPageView.as_view(), name='verification-page'),
    path('check-subscription/', CheckUserSubscriptionView.as_view(), name='check-subscription'),
    path('verify-payment/', VerifyPaymentAPIView.as_view(), name='verify-payment'),
    path('initiate/', PaymentMethodsView.as_view(), name='initiate-payment'),
    path('verify-payment/', VerifyPaymentAPIView.as_view(), name='verify-payment'),
    path('history/', UserPaymentHistoryView.as_view(), name='payment-history'),
    path('payment-page/', PaymentPageView.as_view(), name='payment-page'),
]
