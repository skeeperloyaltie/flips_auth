from django.urls import path
from .views import get_user_info, create_encrypted_link, decode_and_fetch, get_mapbox_token

urlpatterns = [
    path('user-info/', get_user_info, name='user-info'),
    path('create-encrypted-link/', create_encrypted_link, name='create-encrypted-link'),
    path('fetch/<str:encoded_path>/', decode_and_fetch, name='decode-and-fetch'),
    path('get-mapbox-token/', get_mapbox_token, name='get-mapbox-token'),  # Corrected endpoint for Mapbox token
]
