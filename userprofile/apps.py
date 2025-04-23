from django.apps import AppConfig


class UserprofileConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'userprofile'

    def ready(self):
        import userprofile.signals  # Import signals to ensure they get registered
        
        
from django.apps import AppConfig
from django.core.management import call_command

class UserProfileConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "userprofile"

    def ready(self):
        try:
            call_command("createprofile")
        except Exception as e:
            print(f"Superuser creation skipped: {e}")
