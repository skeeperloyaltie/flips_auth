# monitor/management/commands/update_rig_area.py

from django.core.management.base import BaseCommand
from monitor.models import Rig, RigArea

class Command(BaseCommand):
    help = 'Update the area of a specific rig'

    def add_arguments(self, parser):
        parser.add_argument('sensor_id', type=str, help='The sensor ID of the rig')
        parser.add_argument('new_area_name', type=str, help='The new area name to assign to the rig')

    def handle(self, *args, **kwargs):
        sensor_id = kwargs['sensor_id']
        new_area_name = kwargs['new_area_name']

        try:
            rig = Rig.objects.get(sensor_id=sensor_id)
            new_area, created = RigArea.objects.get_or_create(name=new_area_name)
            rig.area = new_area
            rig.save()
            self.stdout.write(self.style.SUCCESS(f'Updated area for rig {sensor_id} to {new_area_name}'))
        except Rig.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Rig with sensor_id {sensor_id} does not exist'))
