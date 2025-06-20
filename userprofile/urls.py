from django.urls import path
from .views import UserProfileView, UpdateUserView, UpdatePasswordView, DeleteAccountView, SendPasswordResetEmailView, PasswordResetConfirmView, VerifyResetTokenView, AcceptPrivacyPolicyView, HealthCheckView

urlpatterns = [
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profile/update/', UpdateUserView.as_view(), name='update-user'),
    path('profile/password/', UpdatePasswordView.as_view(), name='update-password'),
    path('profile/delete/', DeleteAccountView.as_view(), name='delete-account'),
    path('password-reset/', SendPasswordResetEmailView.as_view(), name='password-reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),\
    path('verify-reset-token/', VerifyResetTokenView.as_view(), name='verify-reset-token'),
    path('accept-privacy-policy/', AcceptPrivacyPolicyView.as_view(), name='accept-privacy-policy'),
    path('health/', HealthCheckView.as_view(), name='health_check'),


]


