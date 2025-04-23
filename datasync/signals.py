# datasync/signals.py
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .tasks import start_background_task

@receiver(post_migrate)
def start_sync_task(sender, **kwargs):
    start_background_task()