from django.apps import AppConfig

class ConfigConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'config'  # Make sure this matches the folder name
