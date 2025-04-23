from django.urls import path
from .views import ContactSubmissionView

urlpatterns = [
    path('submit/', ContactSubmissionView.as_view(), name='contact-submit'),
]