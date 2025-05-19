from django.urls import path
from .views import UserSubscriptionStatusView, PaymentPageView, VerificationPageView, \
    CheckUserSubscriptionView, VerifyPaymentAPIView, UserPaymentHistoryView, InitiatePaymentAPIView, PaymentMethodListView, mpesa_stk_callback, mpesa_stk_timeout

urlpatterns = [
    path('verify-subscription/', UserSubscriptionStatusView.as_view(), name='verify-subscription'),
    path('methods/', InitiatePaymentAPIView.as_view(), name='payment-methods'),
    path('verification/', VerificationPageView.as_view(), name='verification-page'),
    path('check-subscription/', CheckUserSubscriptionView.as_view(), name='check-subscription'),
    path('verify-payment/', VerifyPaymentAPIView.as_view(), name='verify-payment'),
    path('initiate/', InitiatePaymentAPIView.as_view(), name='initiate-payment'),
    path('history/', UserPaymentHistoryView.as_view(), name='payment-history'),
    path('payment-page/', PaymentPageView.as_view(), name='payment-page'),
    path('payment-methods/', PaymentMethodListView.as_view(), name='payment-method-list'),
    path('callback/', mpesa_stk_callback, name='mpesa_stk_callback'),
    path('timeout/', views.mpesa_stk_timeout, name='mpesa_timeout'),

]
