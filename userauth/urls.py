from django.urls import path
from .views import CreateUserView, LoginView, UserListView, logout, VerifyEmailView, GoogleLoginView

urlpatterns = [
    path('register/', CreateUserView.as_view(), name='register'),
    path('verify-email/<uuid:token>/', VerifyEmailView.as_view(), name='verify-email'),
    path('login/', LoginView.as_view(), name='login'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('logout/', logout, name='logout'),
    path('google-login/', GoogleLoginView.as_view(), name='google-login'),
]