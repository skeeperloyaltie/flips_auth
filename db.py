# auth/db.py
import os
import pymongo
import logging
import time
from pymongo import MongoClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection URL from environment variable
url = os.getenv('MONGODB_URL', 'mongodb+srv://flips:13917295%21GdaguGg@flips.pahe8.mongodb.net/?retryWrites=true&w=majority&appName=flips')

# Introduce constant for the database name
DATABASE_NAME = 'flipscollection'

# Function to check MongoDB connection
def check_connection(client):
    try:
        # The ping command is cheap and does not require auth.
        client.admin.command('ping')
        logger.info('MongoDB connection successful.')
        return True
    except pymongo.errors.ConnectionError as ce:
        logger.error(f'MongoDB connection error: {ce}')
    except pymongo.errors.ConfigurationError as cfe:
        logger.error(f'MongoDB configuration error: {cfe}')
    except pymongo.errors.OperationFailure as ofe:
        logger.error(f'Authentication failure: {ofe}')
    except Exception as e:
        logger.error(f'An error occurred: {e}')
    return False

def get_mongo_client(max_retries=5, initial_delay=1):
    if not url.startswith('mongodb+srv://'):
        raise ValueError("Invalid MongoDB connection string. It must start with 'mongodb+srv://'")

    client = None

    for retry in range(max_retries):
        try:
            logger.info(f"Attempting to connect to MongoDB (Attempt {retry + 1})")
            # Initialize the client
            client = MongoClient(url)
            if check_connection(client):
                return client
        except pymongo.errors.ConfigurationError as e:
            logger.error(f'Configuration error: {e}')
            break
        except Exception as e:
            logger.error(f'Attempt {retry + 1} failed: {e}')

        delay = initial_delay * (2 ** retry)  # Exponential backoff
        logger.info(f"Retrying to connect in {delay} seconds...")
        time.sleep(delay)

    # Handle connection failure (e.g., retry, raise an error, etc.)
    raise Exception("Unable to connect to the MongoDB server. Check your connection configuration.")

# Function to fetch the database collection, creating a fresh client if necessary
def fetch_db_collection(collection_name):
    client = get_mongo_client()
    db = client[DATABASE_NAME]
    return db[collection_name]