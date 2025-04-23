# import datetime
# import os
# from urllib import request
# import pandas as pd
# import numpy as np
# import rasterio
# from rasterio.transform import from_origin
# from sqlalchemy import create_engine
# from django.utils import timezone
# from rest_framework import status, views
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# import logging
# from userprofile.models import UserProfile, SubscriptionPlan
#
# from auth import settings
#
# # Initialize logger
# logger = logging.getLogger(__name__)
#
# # Database connection
# engine = create_engine('mysql+pymysql://root:1391@localhost:3306/flips')
#
# def check_subscription(user, request):
#     try:
#         profile = request.user.profile
#         current_time = timezone.now()
#
#         if not profile.subscription_plan or profile.expiry_date < current_time:
#             logger.info("Subscription expired or inactive for user %s", user.username)
#             return None, "Inactive or expired subscription"
#
#         subscription_plan = profile.subscription_plan
#         time_threshold = get_time_threshold(subscription_plan, user.is_staff, current_time)
#         if time_threshold is None:
#             logger.warning("Invalid subscription plan for user %s", user.username)
#             return None, "Invalid subscription plan"
#
#         logger.info("Subscription active for user %s with plan %s", user.username, subscription_plan)
#         return subscription_plan, None
#     except UserProfile.DoesNotExist:
#         logger.error("UserProfile not found for user %s", user.username)
#         return None, "No subscription found"
#
# def get_time_threshold(subscription_plan, is_staff, current_time):
#     if subscription_plan.name == 'government' or is_staff:
#         return current_time - datetime.timedelta(days=1)
#     elif subscription_plan.name == 'corporate':
#         return current_time - datetime.timedelta(hours=2)
#     elif subscription_plan.name == 'free':
#         return current_time - datetime.timedelta(minutes=30)
#     return None
#
# class WaterFlowAnalysisAPI(views.APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, request):
#         plan, error = check_subscription(request.user, request)
#         if error:
#             logger.warning(f"Subscription error for user {request.user.username}: {error}")
#             return Response({"error": error}, status=status.HTTP_403_FORBIDDEN)
#
#         query = """
#         SELECT w.level, r.latitude, r.longitude
#         FROM waterleveldata w
#         JOIN rigs r ON w.rig_id = r.id;
#         """
#
#         data = pd.read_sql(query, engine)
#
#         if data.empty:
#             logger.warning(f"No data found in the database for user {request.user.username}.")
#             return Response({"error": "No data available for water flow analysis."}, status=status.HTTP_404_NOT_FOUND)
#             # Log the column names and their data types
#         logger.info(f"Columns in the fetched data: {data.columns.tolist()}")
#         logger.info(f"Data types: {data.dtypes.to_dict()}")
#         min_lat, max_lat = data['latitude'].min(), data['latitude'].max()
#         min_lon, max_lon = data['longitude'].min(), data['longitude'].max()
#         resolution = 0.01
#
#         nrows = int((max_lat - min_lat) / resolution) + 1
#         ncols = int((max_lon - min_lon) / resolution) + 1
#         raster_data = np.full((nrows, ncols), np.nan)
#
#         for _, row in data.iterrows():
#             row_idx = int((row['latitude'] - min_lat) / resolution)
#             col_idx = int((row['longitude'] - min_lon) / resolution)
#             if 0 <= row_idx < nrows and 0 <= col_idx < ncols:
#                 raster_data[row_idx, col_idx] = row['level']
#
#         transform = from_origin(min_lon, max_lat, resolution, resolution)
#         # Define the TIFF file path in the media directory
#         tif_path = os.path.join(settings.MEDIA_ROOT, 'water_flow_analysis.tif')
#
#         with rasterio.open(
#             tif_path,
#             'w',
#             driver='GTiff',
#             height=nrows,
#             width=ncols,
#             count=1,
#             dtype=raster_data.dtype,
#             crs='EPSG:4326',
#             transform=transform,
#         ) as dst:
#             dst.write(raster_data, 1)
#
#         logger.info(f"Generated GeoTIFF file at {tif_path} for user {request.user.username}")
#
#         # In the response data:
#         response_data = {
#             "status": "GeoTIFF generated successfully",
#             "tiff_url": request.build_absolute_uri(f'/media/water_flow_analysis.tif'),
#             "subscription_plan": plan.name,
#             "latitude_range": (min_lat, max_lat),
#             "longitude_range": (min_lon, max_lon),
#         }
#
#         return Response(response_data, status=status.HTTP_200_OK)
#
#
# from rest_framework import permissions, status, views
# from rest_framework.response import Response
# from sqlalchemy import create_engine
# import logging
# import numpy as np
# import rasterio
# from rasterio.transform import from_origin
# import os
# from django.utils import timezone
# from auth import settings
#
# # Initialize logger
# logger = logging.getLogger(__name__)
#
# # Database connection
# engine = create_engine('mysql+pymysql://root:1391@localhost:3306/flips')
#
#
# class ROIManagementAPI(views.APIView):
#     permission_classes = [IsAuthenticated]
#
#     def post(self, request):
#         plan, error = check_subscription(request.user, request)
#         if error:
#             logger.warning(f"Subscription error for user {request.user.username}: {error}")
#             return Response({"error": error}, status=status.HTTP_403_FORBIDDEN)
#
#         coordinates = request.data.get('coordinates', None)
#         if not coordinates:
#             return Response({"error": "No coordinates provided."}, status=status.HTTP_400_BAD_REQUEST)
#
#         logger.info(f"Received ROI coordinates from user {request.user.username}: {coordinates}")
#
#         # Validate coordinates
#         if not isinstance(coordinates, list) or len(coordinates) != 4:
#             return Response({"error": "Invalid coordinates format. Expecting a list of four values."},
#                             status=status.HTTP_400_BAD_REQUEST)
#
#         min_lon, min_lat, max_lon, max_lat = coordinates
#
#         # Fetch relevant water level data within the ROI
#         query = """
#                 SELECT w.level, r.latitude, r.longitude
#                 FROM waterleveldata w
#                 JOIN rigs r ON w.rig_id = r.id
#                 WHERE r.latitude BETWEEN %s AND %s AND r.longitude BETWEEN %s AND %s;
#             """
#
#         data = pd.read_sql(query, engine, params=(min_lat, max_lat, min_lon, max_lon))
#
#         if data.empty:
#             logger.warning(f"No data found in the database for ROI defined by user {request.user.username}.")
#             return Response({"error": "No data available for the specified ROI."}, status=status.HTTP_404_NOT_FOUND)
#
#         # Generate a raster for the filtered data
#         return self.generate_raster(data, min_lon, min_lat, max_lon, max_lat, request.user.username)
#
#     def generate_raster(self, data, min_lon, min_lat, max_lon, max_lat, username):
#         resolution = 0.01
#
#         nrows = int((max_lat - min_lat) / resolution) + 1
#         ncols = int((max_lon - min_lon) / resolution) + 1
#         raster_data = np.full((nrows, ncols), np.nan)
#
#         for _, row in data.iterrows():
#             row_idx = int((row['latitude'] - min_lat) / resolution)
#             col_idx = int((row['longitude'] - min_lon) / resolution)
#             if 0 <= row_idx < nrows and 0 <= col_idx < ncols:
#                 raster_data[row_idx, col_idx] = row['level']
#
#         transform = from_origin(min_lon, max_lat, resolution, resolution)
#
#         # Define the TIFF file path in the media directory
#         tif_path = os.path.join(settings.MEDIA_ROOT, f'water_flow_analysis_{username}.tif')
#
#         with rasterio.open(
#                 tif_path,
#                 'w',
#                 driver='GTiff',
#                 height=nrows,
#                 width=ncols,
#                 count=1,
#                 dtype=raster_data.dtype,
#                 crs='EPSG:4326',
#                 transform=transform,
#         ) as dst:
#             dst.write(raster_data, 1)
#
#         logger.info(f"Generated GeoTIFF file at {tif_path} for user {username}")
#
#         # Response data with the generated TIFF URL
#         response_data = {
#             "status": "GeoTIFF generated successfully",
#             "tiff_url": request.build_absolute_uri(f'/media/{os.path.basename(tif_path)}'),
#             "roi_coordinates": {
#                 "min_lon": min_lon,
#                 "min_lat": min_lat,
#                 "max_lon": max_lon,
#                 "max_lat": max_lat
#             }
#         }
#
#         return Response(response_data, status=status.HTTP_200_OK)





# from django.urls import path
# from .views import WaterFlowAnalysisAPI, ROIManagementAPI
#
# urlpatterns = [
#     path('gismapping/', WaterFlowAnalysisAPI.as_view(), name='water_flow_analysis'),
#     path('roi/', ROIManagementAPI.as_view(), name='roi_management')
# ]



# import logging
# from rest_framework import permissions
# from .models import UserSubscription  # Ensure your UserSubscription model is imported
#
# # Initialize logging
# logger = logging.getLogger(__name__)
#
# class IsStaffOrGovtPlan(permissions.BasePermission):
#     """
#     Custom permission to only allow staff or users with a government plan to access the view.
#     """
#
#     def has_permission(self, request, view):
#         # Log the user's details for debugging
#         logger.debug(f"Checking permissions for user: {request.user.username}, Staff: {request.user.is_staff}")
#
#         # Check if the user is staff
#         if request.user.is_staff:
#             logger.debug("Access granted: User is staff.")
#             return True
#
#         # Check if the user has a subscription
#         try:
#             subscription = UserSubscription.objects.get(user=request.user)
#             # Allow access if user has a government plan
#             if subscription.plan.name == 'government':
#                 logger.debug("Access granted: User has government plan.")
#                 return True
#             else:
#                 logger.debug("Access denied: User does not have a government plan.")
#         except UserSubscription.DoesNotExist:
#             logger.debug("Access denied: User has no subscription.")
#
#         return False





# from django.db import models
# from django.contrib.auth.models import User
# from payments.models import UserPayment  # Import UserPayment from payments
#
# class SubscriptionPlan(models.Model):
#     name = models.CharField(max_length=50)
#     access_duration = models.IntegerField(help_text="Time limit in minutes for free users")
#     description = models.TextField()
#
#     def __str__(self):
#         return self.name
#
# class UserSubscription(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
#     expiry_date = models.DateTimeField()
#     payment = models.OneToOneField(UserPayment, on_delete=models.CASCADE, null=True, blank=True)  # Link to UserPayment
#
#     def __str__(self):
#         return f"{self.user.username}'s subscription to {self.plan.name}"
