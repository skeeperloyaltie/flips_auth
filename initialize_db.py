import os
import django
from django.contrib.auth import get_user_model
from django.core.management import call_command

# Initialize Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth.settings')  # Replace with your settings module
django.setup()

# Superuser details
User = get_user_model()
username = 'skeeper'
email = 'skeepertech7@gmail.com'
password = '13917295!Gg'

print("Starting initialization...")

try:
    # Ensure the superuser exists with correct flags
    user, created = User.objects.get_or_create(username=username, defaults={'email': email})
    if created:
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print(f"Superuser '{username}' created with the correct flags.")
    else:
        # Update password and ensure flags are correct
        if not user.is_staff or not user.is_superuser:
            user.is_staff = True
            user.is_superuser = True
            print(f"Superuser '{username}' flags updated.")
        user.set_password(password)
        user.save()
        print(f"Superuser '{username}' password updated.")
except Exception as e:
    print(f"Error initializing superuser: {e}")

# Run other setup commands
try:
    print("Running additional setup commands...")
    call_command('create_profiles')
    call_command('add_rigs')
    call_command('add_subscription_plans')
    print("Setup commands completed successfully.")
except Exception as e:
    print(f"Error running setup commands: {e}")
