# datasync/apps.py
from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.dispatch import receiver

class DatasyncConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'datasync'

    def ready(self):
        import datasync.signals  # Ensure signals are registered