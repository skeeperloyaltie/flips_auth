import requests
import json
import time
import random
from datetime import datetime
import pytz
import redis
import os

# Redis connection
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379"))

# The endpoint URLs
sensor_data_url = "https://api.flipsintel.org/monitor/sensor-data/"
rigs_url = "https://api.flipsintel.org/monitor/get-rigs/"

# The header, including an authorization token
headers = {
    "Content-Type": "application/json",
    "Authorization": "Token 951127f867969f82e3be8a69e2b20568ee495a06",
}

def fetch_rigs():
    """Fetches rig data from the server or Redis cache."""
    # Try to get rigs from Redis
    cached_rigs = redis_client.get("rigs")
    if cached_rigs:
        return json.loads(cached_rigs)

    # Fetch from API if not in cache
    while True:
        try:
            response = requests.get(rigs_url, headers=headers)
            if response.status_code == 200:
                rigs = response.json()
                # Cache for 5 minutes
                redis_client.setex("rigs", 300, json.dumps(rigs))
                return rigs
            else:
                print(f"Failed to fetch rigs: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching rigs: {e}")

        print("Retrying in 60 seconds...")
        time.sleep(60)

def generate_real_time_data(sensor_id, rig):
    """
    Generates real-time data using the current timestamp.
    """
    nairobi_tz = pytz.timezone('Africa/Nairobi')
    timestamp = datetime.now(nairobi_tz).isoformat()

    return {
        "sensorID": sensor_id,
        "waterLevel": round(random.uniform(5.0, 10.0), 2),
        "temperature": round(random.uniform(20.0, 30.0), 2),
        "humidity": round(random.uniform(50.0, 70.0), 2),
        "timestamp": timestamp,
        "latitude": rig["latitude"],
        "longitude": rig["longitude"]
    }

def send_data():
    """
    Continuously fetch rig data, generate real-time sensor data,
    and send it to the server.
    """
    while True:
        rigs = fetch_rigs()
        if not rigs:
            print("No rigs available to send data.")
            continue

        selected_rig = random.choice(rigs)
        sensor_id = selected_rig.get("sensor_id")

        if not sensor_id:
            print(f"Skipping rig with invalid or missing sensor_id: {selected_rig}")
            continue

        data = generate_real_time_data(sensor_id, selected_rig)

        try:
            response = requests.post(sensor_data_url, headers=headers, data=json.dumps(data))
            if response.status_code in (200, 201):
                print(
                    f"Data sent successfully for sensor {sensor_id} (rig {selected_rig.get('rig_id')})"
                )
                print(response.json())
            else:
                print(
                    f"Failed to send data for sensor {sensor_id} (rig {selected_rig.get('rig_id')}): {response.status_code}"
                )
                try:
                    print(response.json())
                except json.JSONDecodeError:
                    print(response.text)
        except requests.exceptions.RequestException as e:
            print(
                f"Error sending request for sensor {sensor_id} (rig {selected_rig.get('rig_id')}): {e}"
            )

        time.sleep(3)

if __name__ == "__main__":
    send_data()
