# datasync/sync.py
import os
import pymongo
import logging
import time
from django.utils.timezone import make_aware
from datetime import datetime
from .models import PredictedWaterLevels,  WaterLevels, SyncActivity
from monitor.models import Rigs, WaterLevelData

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection URL from environment variable
url = os.getenv('MONGODB_URL', 'mongodb+srv://flips:13917295%21GdaguGg@flips.pahe8.mongodb.net/?retryWrites=true&w=majority&appName=flips')

DATABASE_NAME = 'flipscollection'
COLLECTION_NAMES = ['predicted_water_levels', 'rigs', 'water_level_data', 'water_levels']

def check_connection(client):
    try:
        client.admin.command('ping')
        logger.info('MongoDB connection successful.')
        return True
    except pymongo.errors.PyMongoError as e:
        logger.error(f'MongoDB connection error: {e}')
    return False

def get_mongo_client(max_retries=5, initial_delay=1):
    if not url.startswith('mongodb+srv://'):
        raise ValueError("Invalid MongoDB connection string. It must start with 'mongodb+srv://'")

    client = None
    for retry in range(max_retries):
        try:
            logger.info(f"Attempting to connect to MongoDB (Attempt {retry + 1})")
            client = pymongo.MongoClient(url)
            if check_connection(client):
                return client
        except pymongo.errors.PyMongoError as e:
            logger.error(f'Attempt {retry + 1} failed: {e}')
        delay = initial_delay * (2 ** retry)
        logger.info(f"Retrying to connect in {delay} seconds...")
        time.sleep(delay)

    raise Exception("Unable to connect to the MongoDB server. Check your connection configuration.")

def fetch_and_update_data():
    client = get_mongo_client()
    db = client[DATABASE_NAME]

    for collection_name in COLLECTION_NAMES:
        collection = db[collection_name]

        if collection_name == 'predicted_water_levels':
            model = PredictedWaterLevels
            get_last_timestamp = lambda: model.objects.using('default').latest('timestamp').timestamp
        elif collection_name == 'rigs':
            model = Rigs
            get_last_timestamp = lambda: datetime.min
        elif collection_name == 'water_level_data':
            model = WaterLevelData
            get_last_timestamp = lambda: model.objects.using('default').latest('timestamp').timestamp
        elif collection_name == 'water_levels':
            model = WaterLevels
            get_last_timestamp = lambda: model.objects.using('default').latest('timestamp').timestamp

        try:
            last_timestamp = get_last_timestamp()
        except model.DoesNotExist:
            last_timestamp = make_aware(datetime.min)

        new_records = collection.find({"timestamp": {"$gt": last_timestamp}})
        logger.info(f"Fetching new records from MongoDB collection: {collection_name}")

        records_updated = 0
        for record in new_records:
            if collection_name == 'predicted_water_levels':
                fields = {
                    '_id': str(record.get('_id')),
                    'timestamp': record.get('timestamp'),
                    'predicted_level': record.get('predicted_level')
                }
            elif collection_name == 'rigs':
                fields = {
                    '_id': str(record.get('_id')),
                    'sensor_id': record.get('sensor_id'),
                    'location': record.get('location'),
                    'latitude': record.get('latitude'),
                    'longitude': record.get('longitude')
                }
            elif collection_name == 'water_level_data':
                fields = {
                    '_id': str(record.get('_id')),
                    'timestamp': record.get('timestamp'),
                    'rig': record.get('rig'),
                    'level': record.get('level'),
                    'temperature': record.get('temperature'),
                    'humidity': record.get('humidity')
                }
            elif collection_name == 'water_levels':
                fields = {
                    '_id': str(record.get('_id')),
                    'timestamp': record.get('timestamp'),
                    'rig': record.get('rig'),
                    'level': record.get('level'),
                    'temperature': record.get('temperature'),
                    'humidity': record.get('humidity')
                }

            model.objects.using('default').update_or_create(
                _id=fields['_id'], defaults=fields
            )
            records_updated += 1

        if records_updated > 0:
            logger.info(f"{records_updated} records updated in PostgreSQL table '{collection_name}'.")
        else:
            logger.info(f"No new records to update for PostgreSQL table '{collection_name}'.")

        SyncActivity.objects.create(table_name=collection_name, records_updated=records_updated)