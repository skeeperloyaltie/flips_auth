# monitor/management/commands/add_rigs.py

from django.core.management.base import BaseCommand
from monitor.models import Rig, RigArea
from shapely.geometry import Polygon
from django.contrib.gis.geos import GEOSGeometry

class Command(BaseCommand):
    help = 'Add or update rigs in the database based on sensor_id'

    def handle(self, *args, **kwargs):
        # Define the polygon coordinates for Tana Area (example coordinates)
        # Define the polygon coordinates for the entire country of Kenya
        kenya_area_coordinates = [
            (34.816, 5.000),  # NW point
            (41.000, 5.000),  # NE point
            (41.000, -4.000),  # SE point
            (34.816, -4.000),  # SW point
            (34.816, 5.000)  # Closing the polygon
        ]

        # Create the polygon for Kenya Area
        kenya_area_polygon = GEOSGeometry(
            f'POLYGON(({", ".join(f"{lon} {lat}" for lon, lat in kenya_area_coordinates)}))')

        # Get or create the RigArea object with the polygon
        area, _ = RigArea.objects.get_or_create(
            name="Kenya Area",
            defaults={
                'description': "Area covering the entire country of Kenya",
                'area_polygon': kenya_area_polygon,
            }
        )

        rigs_data = [
            {
                "sensor_id": "Tana Upper",
                "location": "Kone",
                "latitude": -0.07842642962340313,
                "longitude": 38.95772447774984,
                "area": area,  # Use the created area object
            },
            {
                "sensor_id": "Tana Center",
                "location": "Sankuri",
                "latitude": -0.2961679840764966,
                "longitude": 39.53842118297724,
                "area": area,
            },
            {
                "sensor_id": "Tana Lower",
                "location": "Sombo",
                "latitude": -0.5678196253853346,
                "longitude": 39.68674985306361,
                "area": area,
            },
        ]

        for rig_data in rigs_data:
            rig, created = Rig.objects.get_or_create(
                sensor_id=rig_data['sensor_id'],
                defaults={
                    'location': rig_data['location'],
                    'latitude': rig_data['latitude'],
                    'longitude': rig_data['longitude'],
                    'area': rig_data['area'],  # Set the area when creating the rig
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'Created rig: {rig.sensor_id} with area: {area.name}'))
            else:
                # Update the existing rig's details, but not the area
                updated_fields = []

                if rig.latitude != rig_data['latitude']:
                    rig.latitude = rig_data['latitude']
                    updated_fields.append('latitude')
                if rig.longitude != rig_data['longitude']:
                    rig.longitude = rig_data['longitude']
                    updated_fields.append('longitude')
                if rig.location != rig_data['location']:
                    rig.location = rig_data['location']
                    updated_fields.append('location')

                if updated_fields:
                    rig.save()  # Save only if there are fields to update
                    self.stdout.write(self.style.SUCCESS(f'Updated rig: {rig.sensor_id}, changed fields: {", ".join(updated_fields)}'))
                else:
                    self.stdout.write(self.style.WARNING(f'Rig already exists and is up-to-date: {rig.sensor_id}'))
