# sms/management/commands/check_water_levels.py
from django.core.management.base import BaseCommand
from sms.tasks import check_and_send_alerts

class Command(BaseCommand):
    help = 'Check water levels and send SMS alerts if necessary'

    def handle(self, *args, **kwargs):
        check_and_send_alerts()
