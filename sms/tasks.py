# sms/tasks.py
from celery import shared_task

from auth.sms.models import WaterLevel

@shared_task
def check_and_send_alerts():
    latest_level = WaterLevel.objects.latest('timestamp')
    
    if latest_level.level > THRESHOLD:
        message = f"Alert! Water level is above the threshold. Current level: {latest_level.level}m"
        phone_numbers = ['+254712345678']  # Replace with the list of phone numbers you want to notify
        
        try:
            response = sms.send(message, phone_numbers)
            print(f"Alert sent successfully: {response}")
        except Exception as e:
            print(f"Failed to send alert: {e}")
