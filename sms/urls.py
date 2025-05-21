from django.urls import path
from .views import SMSConfigView, SMSLogView, LoginCodeView, VerifyLoginCodeView

urlpatterns = [
    path('sms/config/', SMSConfigView.as_view(), name='sms-config'),
    path('sms/logs/', SMSLogView.as_view(), name='sms-logs'),
    path('sms/login-code/', LoginCodeView.as_view(), name='login-code'),
    path('sms/verify-code/', VerifyLoginCodeView.as_view(), name='verify-code'),
]