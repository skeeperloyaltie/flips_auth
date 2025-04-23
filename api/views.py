from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import logging
from rest_framework.exceptions import NotAuthenticated
from .utils import encode_to_base64, decode_from_base64

logger = logging.getLogger(__name__)
# In your Django view

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_info(request):
    logger.debug('Headers: %s', request.headers)
    logger.debug('User: %s', request.user)

    # Ensure user is authenticated and log error if not
    if request.user.is_authenticated:
        return Response({'email': request.user.email, 'username': request.user.username})
    else:
        raise NotAuthenticated('Authentication credentials were not provided or are invalid.')

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_encrypted_link(request):
    """Creates an encrypted link from a given path."""
    path = request.data.get('path')

    if not path:
        return Response({'error': 'Path is required'}, status=status.HTTP_400_BAD_REQUEST)

    encoded_path = encode_to_base64(path)
    return Response({'encoded_link': encoded_path}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def decode_and_fetch(request, encoded_path):
    """Decodes an encrypted link and fetches the info."""
    decoded_path = decode_from_base64(encoded_path)
    logger.debug(f'Decoded Path: {decoded_path}')

    # Add your logic to use the decoded path (e.g., check if it leads to a valid resource)

    return Response({'decoded_path': decoded_path}, status=status.HTTP_200_OK)


# views.py

from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import logging

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_mapbox_token(request):
    """Endpoint to provide the Mapbox access token to authenticated users."""
    mapbox_token = settings.MAPBOX_ACCESS_TOKEN
    return Response({'mapbox_access_token': mapbox_token})
