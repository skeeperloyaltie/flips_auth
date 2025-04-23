# import logging
# import ee
# import os
#
# # Initialize logger
# logger = logging.getLogger(__name__)
#
# # Path to service account key file
# service_account_key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/app/key.json")
#
# # Initialize Earth Engine using the service account credentials
# try:
#     if service_account_key_path and os.path.exists(service_account_key_path):
#         credentials = ee.ServiceAccountCredentials(None, service_account_key_path)
#         ee.Initialize(credentials)
#         logger.info("Earth Engine initialized using service account credentials.")
#     else:
#        raise FileNotFoundError("Service account key file not found at the specified path.")
# except Exception as e:
#     logger.error(f"Error initializing Earth Engine: {e}")
#     raise RuntimeError("Failed to initialize Earth Engine with service account credentials") from e
#
# def fetch_dem_data(min_lon, min_lat, max_lon, max_lat):
#     """
#     Fetches DEM data strictly for the user-selected AOI coordinates.
#     This should ensure alignment between the coordinates and the fetched DEM.
#
#     Parameters:
#         min_lon (float): Minimum longitude of the bounding box.
#         min_lat (float): Minimum latitude of the bounding box.
#         max_lon (float): Maximum latitude of the bounding box.
#         max_lat (float): Maximum longitude of the bounding box.
#
#     Returns:
#         dict: Contains a URL to download the DEM image as a GeoTIFF and metadata if successful.
#     """
#     try:
#         # Debug logging of input coordinates to verify correctness
#         logger.debug(f"AOI coordinates received for DEM fetch: min_lon={min_lon}, min_lat={min_lat}, "
#                      f"max_lon={max_lon}, max_lat={max_lat}")
#
#         # Define AOI as a bounding box using user-provided coordinates
#         region = ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])
#
#         # Calculate scale dynamically based on the AOI size
#         width_km = abs(max_lon - min_lon) * 111  # Rough conversion to km at equator
#         scale = 30 if width_km < 30 else 90 if width_km < 100 else 300
#
#         # Load a DEM dataset from GEE (using SRTM as an example)
#         dem_image = ee.Image("USGS/SRTMGL1_003").reproject(crs="EPSG:4326", scale=scale)
#
#         # Clip the DEM image to the exact user-defined AOI
#         dem_clipped = dem_image.clip(region)
#
#         # Log the selected scale and region for clarity
#         logger.info(f"Fetching DEM with scale {scale}m for region bounds "
#                     f"({min_lat}, {min_lon}), ({max_lat}, {max_lon})")
#
#         # Request a download URL for the DEM image as a GeoTIFF
#         url = dem_clipped.getDownloadURL({
#             'scale': scale,
#             'region': region.toGeoJSONString(),
#             'format': 'GEO_TIFF',
#             'crs': "EPSG:4326"
#         })
#
#         return {
#             "url": url,
#             "metadata": {
#                 "source": "GEE USGS/SRTMGL1_003",
#                 "resolution": f"{scale}m",
#                 "bounds": {
#                     "min_lat": min_lat,
#                     "min_lon": min_lon,
#                     "max_lat": max_lat,
#                     "max_lon": max_lon
#                 }
#             }
#         }
#
#     except Exception as e:
#         logger.error(f"Failed to fetch DEM data from GEE: {e}")
#         return {
#             "error": "Could not retrieve DEM data",
#             "details": str(e)
#         }
