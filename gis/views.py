from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import ee
import logging
import os
from monitor.models import Rig

# Initialize logger
logger = logging.getLogger(__name__)

# Path to the service account key file
SERVICE_ACCOUNT_KEY_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/app/key.json")

# Initialize Earth Engine
def initialize_earth_engine():
    try:
        if SERVICE_ACCOUNT_KEY_PATH and os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
            credentials = ee.ServiceAccountCredentials(None, SERVICE_ACCOUNT_KEY_PATH)
            ee.Initialize(credentials)
            logger.info("Earth Engine initialized successfully.")
        else:
            raise FileNotFoundError(f"Service account key file not found at {SERVICE_ACCOUNT_KEY_PATH}.")
    except Exception as e:
        logger.error(f"Error initializing Earth Engine: {e}")
        raise RuntimeError("Failed to initialize Earth Engine with service account credentials.") from e


@csrf_exempt
def analyze_roi(request):
    """
    API endpoint to analyze a Region of Interest (ROI).
    Expects GeoJSON data in the request body.
    """
    if request.method != "POST":
        logger.warning("Invalid request method for /analyze-roi/")
        return JsonResponse({"error": "Invalid request method."}, status=400)

    logger.info("Received a POST request to analyze ROI.")

    try:
        initialize_earth_engine()

        # Extract GeoJSON from the request
        body = json.loads(request.body)
        aoi_geojson = body.get("aoi")

        # if rig_id:
        #     # Fetch rig by ID
        #     rig = Rig.objects.filter(id=rig_id).first()
        #     if not rig:
        #         logger.error(f"Rig with ID {rig_id} not found.")
        #         return JsonResponse({"error": "Rig not found."}, status=404)
        #
        #     # Define AOI as a buffer around the rig's location (e.g., 1 km radius)
        #     aoi = ee.Geometry.Point([rig.longitude, rig.latitude]).buffer(1000)  # 1 km buffer
        #     logger.info(f"Using AOI for rig {rig.sensor_id}: {aoi.getInfo()}")

        if not aoi_geojson:
            logger.error("No AOI provided in the request.")
            return JsonResponse({"error": "AOI is required."}, status=400)

        try:
            # Since `aoi_geojson` is already a dictionary, no need to call json.loads again
            aoi = ee.Geometry(aoi_geojson)
            logger.info(f"AOI parsed successfully: {aoi_geojson}")
        except Exception as e:
            logger.error(f"Invalid GeoJSON format: {e}")
            return JsonResponse({"error": "Invalid GeoJSON format."}, status=400)

        # Load and process Sentinel-2 data
        s2 = ee.ImageCollection("COPERNICUS/S2_HARMONIZED") \
            .filterDate("2024-03-01", "2024-05-30") \
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 23)) \
            .filterBounds(aoi) \
            .map(lambda img: img.clip(aoi))

        rgb_vis = {
            "opacity": 1,
            "bands": ["B4", "B3", "B2"],
            "min": 392.63,
            "max": 1694.87,
            "gamma": 1,
        }
        # Apply NDWI calculation
        dataset = s2.median()
        ndwi = dataset.normalizedDifference(["B3", "B8"]).rename("NDWI")
        water_mask = ndwi.gt(0.3).selfMask()

        # Calculate flood extent
        flood_area = water_mask.multiply(ee.Image.pixelArea()).divide(1e6)
        flood_stats = flood_area.reduceRegion(
            reducer=ee.Reducer.sum(), geometry=aoi, scale=10, maxPixels=1e9
        ).getInfo()
        flood_area_sq_km = round(flood_stats.get("NDWI", 0), 2)

        logger.info(f"Flood area calculated: {flood_area_sq_km} sq km.")

        # Population exposure analysis
        population = ee.ImageCollection("WorldPop/GP/100m/pop") \
            .filterDate("2020-01-01", "2024-05-20") \
            .median() \
            .clip(aoi)
        exposed_population_stats = population.updateMask(water_mask).reduceRegion(
            reducer=ee.Reducer.sum(), geometry=aoi, scale=100, maxPixels=1e9
        ).getInfo()
        exposed_population = int(exposed_population_stats.get("population", 0))

        logger.info(f"Exposed population calculated: {exposed_population}.")

        # Load additional analysis layers
        water_occurrence = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("occurrence").clip(aoi)
        gsw = ee.Image("JRC/GSW1_4/GlobalSurfaceWater")
        waterOccurrence = gsw.select('occurrence').clip(aoi)
        permanent_water = waterOccurrence.gt(80).selfMask()
        distance = permanent_water.fastDistanceTransform().divide(30).clip(aoi).reproject('EPSG:4326', None, 30)
        srtm = ee.Image("USGS/SRTMGL1_003").clip(aoi).reproject('EPSG:4326', None, 30)
        slope = ee.Terrain.slope(srtm)
        velocity = slope.divide(10)
        flow_time = distance.divide(velocity).mask(velocity.gt(0)).rename('FlowTime')
        flow_time_minutes = flow_time.divide(60)
        # Compile analysis layers
        analysis_layers = {
            "aoi": aoi_geojson,
            "water_occurrence": waterOccurrence.getMapId({'min': 0, 'max': 100, 'palette': ['white', 'blue']})[
                'tile_fetcher'].url_format,
            "ndwi": ndwi.getMapId({'min': -1, 'max': 1, 'palette': ['00FFFF', '0000FF']})[
                'tile_fetcher'].url_format,
            "population": population.getMapId({'min': 0.0016165449051186442, 'max': 10.273528099060059,
                                               'palette': ['white', 'yellow', 'orange', 'red']})[
                'tile_fetcher'].url_format,
            "dataset_without_cloud": dataset.getMapId(rgb_vis)['tile_fetcher'].url_format,
            "permanent_water": permanent_water.getMapId({'palette': 'blue'})['tile_fetcher'].url_format,
            "distance":
                distance.getMapId({'max': 500, 'min': 0, 'palette': ['blue', 'cyan', 'green', 'yellow', 'red']})[
                    'tile_fetcher'].url_format,
            "elevation": srtm.getMapId({'min': 1000, 'max': 1500, 'palette': ['green', 'yellow', 'red']})[
                'tile_fetcher'].url_format,
            "slope": slope.getMapId({'min': 0, 'max': 22, 'palette': ['white', 'green', 'yellow', 'red']})[
                'tile_fetcher'].url_format,
            "flow_velocity": flow_time.getMapId({'min': 0, 'max': 6, 'palette': ['blue', 'cyan', 'yellow', 'red']})[
                'tile_fetcher'].url_format,
            "flow_time_minutes":
                flow_time_minutes.getMapId({'min': 0, 'max': 500, 'palette': ['blue', 'cyan', 'yellow', 'red']})[
                    'tile_fetcher'].url_format,
        }

        # Legend definitions
        legends = {
            "water_occurrence": {"description": "Water occurrence", "colors": ["white", "blue"]},
            "ndwi": {"description": "Normalized Difference Water Index", "colors": ["cyan", "blue"]},
            "population": {"description": "Population density", "colors": ["white", "yellow", "orange", "red"]},
            "permanent_water": {"description": "Permanent water bodies", "colors": ["blue"]},
            "distance": {"description": "Distance to permanent water", "colors": ["blue", "cyan", "yellow", "red"]},
            "elevation": {"description": "Elevation levels", "colors": ["green", "yellow", "red"]},
            "slope": {"description": "Slope levels", "colors": ["white", "green", "yellow", "red"]},
            "flow_velocity": {"description": "Flow velocity", "colors": ["blue", "cyan", "yellow", "red"]},
            "flow_time_minutes": {"description": "Flow time (minutes)", "colors": ["blue", "cyan", "yellow", "red"]},
        }

        # Return the analysis results and legends
        return JsonResponse(
            {
                "flood_area_sq_km": flood_area_sq_km,
                "exposed_population": exposed_population,
                "analysis_layers": analysis_layers,
                "legends": legends,
            },
            status=200,
        )
    except Exception as e:
        logger.error(f"Error analyzing ROI: {e}")
        return JsonResponse({"error": str(e)}, status=500)


