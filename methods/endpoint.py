import requests
import subprocess
import os
import sys
import django

# Initialize Django so that it can find test modules
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth.settings')
django.setup()

API_ENDPOINTS = {
    "api": {
        "endpoints": [
            {"name": "User Info", "url": "/api/user-info/"},
        ],
        "test_module": "api.tests"
    },
    "monitoring": {
        "endpoints": [
            {"name": "Measurements", "url": "/monitoring/measurements/"},
            {"name": "Water Levels", "url": "/monitoring/water-levels/"},
            {"name": "Humidity", "url": "/monitoring/humidity/"},
            {"name": "Temperature", "url": "/monitoring/temperature/"},
            {"name": "Linear Regression", "url": "/monitoring/linear-regression/"},
            {"name": "Get Data", "url": "/monitoring/getdata/"},
            {"name": "List Files", "url": "/monitoring/list-files/"},
            {"name": "Flood Monitoring", "url": "/monitoring/flood-monitoring/"},
            {"name": "Map Visualization", "url": "/monitoring/map-visualization/"},
        ],
        "test_module": "monitoring.tests"
    },
    "payments": {
        "endpoints": [
            {"name": "Create Payment Intent", "url": "/payments/create-payment-intent/"},
            {"name": "Payment Webhook", "url": "/payments/webhook/"},
        ],
        "test_module": "payments.tests"
    },
    "prediction": {
        "endpoints": [
            {"name": "Create Time Slot", "url": "/prediction/create-time-slot/"},
            {"name": "Get Predictions", "url": "/prediction/get-predictions/"},
        ],
        "test_module": "prediction.tests"
    },
    "sms": {
        "endpoints": [
            {"name": "Send SMS", "url": "/sms/send-sms/"},
        ],
        "test_module": "sms.tests"
    },
    "subscription": {
        "endpoints": [
            {"name": "Subscription Plans", "url": "/subscription/plans/"},
            {"name": "Check Subscription Status", "url": "/subscription/status/"},
            {"name": "Subscribe", "url": "/subscription/subscribe/"},
            {"name": "Get Dashboard URL", "url": "/subscription/get-dashboard-url/"},
        ],
        "test_module": "subscription.tests"
    },
    "userauth": {
        "endpoints": [
            {"name": "Register", "url": "/register/"},
            {"name": "Login", "url": "/login/"},
            {"name": "User List", "url": "/users/"},
            {"name": "Logout", "url": "/logout/"},
        ],
        "test_module": "userauth.tests"
    }
}


# Base URL of your Django server
BASE_URL = "http://127.0.0.1:8000"

def check_endpoint(api_name, endpoint):
    """Check if an endpoint returns a 200 status code."""
    url = BASE_URL + endpoint["url"]
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print(f"[SUCCESS] {api_name} - {endpoint['name']} endpoint is working. Status code: {response.status_code}")
        else:
            print(f"[ERROR] {api_name} - {endpoint['name']} endpoint failed. Status code: {response.status_code}")
    except Exception as e:
        print(f"[EXCEPTION] {api_name} - {endpoint['name']} endpoint raised an exception: {e}")

def run_tests(api_name, test_module):
    """Run the tests for a specific API."""
    print(f"Running tests for {api_name}...")
    try:
        # Use Django's test runner to execute the tests for the given module
        command = f"python manage.py test {test_module}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"[SUCCESS] Tests for {api_name} passed.")
        else:
            print(f"[ERROR] Tests for {api_name} failed. Output:\n{result.stdout}\nErrors:\n{result.stderr}")
    except Exception as e:
        print(f"[EXCEPTION] Running tests for {api_name} raised an exception: {e}")

def main():
    # Iterate through each API and its endpoints
    for api_name, api_info in API_ENDPOINTS.items():
        print(f"Checking API: {api_name}")
        
        # Check each endpoint in the API
        for endpoint in api_info["endpoints"]:
            check_endpoint(api_name, endpoint)
        
        # Run the tests for the API
        run_tests(api_name, api_info["test_module"])

if __name__ == "__main__":
    main()
