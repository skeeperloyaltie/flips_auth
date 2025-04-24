"""auth URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include

# from .views import ExampleView
# Add this in your project's urls.py


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),  # new
    path("", include("userauth.urls")),
    # path('example/', ExampleView.as_view(), name='example'),
    path("api/", include("api.urls")),
    path(
        "subscription/", include("subscription.urls")
    ),  # Assuming 'subscription' is the name of your app
    path(
        "api_monitor/", include("api_monitor.urls")
    ),  # Include the api_monitor app URLs
    path("payments/", include("payments.urls")),
    path("sms/", include("sms.urls")),
    path("monitoring/", include("monitoring.urls")),
    path("prediction/", include("prediction.urls")),
    path("apistatus/", include("apistatus.urls")),  # Include the apistatus URLs here
    path("contact/", include("contact.urls")),  # Include the apistatus URLs here
    path("newsletter/", include("newsletter.urls")),
    path("monitor/", include("monitor.urls")),
    path("neural/", include("neural.urls")),
    path("userprofile/", include("userprofile.urls")),
    # path("support/", include("support.urls")),
    path('activity/', include('activity.urls')),  # Include the activity logger API
    path('rigsdata/', include('rigsdata.urls')),
    path('reports/', include('reports.urls')),
    path('settings/', include("settings.urls")),
    path('gis/', include("gis.urls")),
    path('modelbuilder/', include('modelbuilder.urls')),  # Include modelbuilder app URLs
    path('insurance/', include('insurance.urls')),

]
# pprint(get_resolver().reverse_dict)
