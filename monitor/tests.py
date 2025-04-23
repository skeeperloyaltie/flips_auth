# monitor/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
import json

class MonitorAPITests(TestCase):

    def setUp(self):
        self.client = Client()

        self.rig_data = {
            'sensorID': 'sensor_123',
            'location': 'River Test',
            'latitude': 12.34,
            'longitude': 56.78,
        }

        self.water_level_data = {
            'sensorID': 'sensor_123',
            'location': 'River Test',
            'latitude': 12.34,
            'longitude': 56.78,
            'waterLevel': 9.87,
            'temperature': 25.0,
            'humidity': 60.0,
        }

    def test_sensor_data_receiving(self):
        response = self.client.post(
            reverse('sensor_data'),
            data=json.dumps(self.rig_data),
            content_type='application/json',
            HTTP_AUTHORIZATION='Token your_token_here'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_water_level_data_receiving(self):
        # First create the rig
        self.client.post(
            reverse('sensor_data'),
            data=json.dumps(self.rig_data),
            content_type='application/json',
            HTTP_AUTHORIZATION='Token your_token_here'
        )

        # Now create water level data
        response = self.client.post(
            reverse('sensor_data'),
            data=json.dumps(self.water_level_data),
            content_type='application/json',
            HTTP_AUTHORIZATION='Token your_token_here'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_water_levels(self):
        # First create data
        self.test_water_level_data_receiving()
        # Test GET request
        response = self.client.get(reverse('water_level_list'), HTTP_AUTHORIZATION='Token your_token_here')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_rigs(self):
        # First create data
        self.test_sensor_data_receiving()
        # Test GET request
        response = self.client.get(reverse('rig_list'), HTTP_AUTHORIZATION='Token your_token_here')
        self.assertEqual(response.status_code, status.HTTP_200_OK)