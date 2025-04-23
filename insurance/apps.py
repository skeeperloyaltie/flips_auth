from django.apps import AppConfig


# insurance/apps.py
class InsuranceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'insurance'

    def ready(self):
        import insurance.signals

