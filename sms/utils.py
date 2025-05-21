import requests
from django.conf import settings
from .models import SMSConfig, SMSLog

def send_sms(phone_number, message, message_type, subscriber=None, promotional_message=None):
    try:
        # Get SMS configuration
        sms_config = SMSConfig.objects.first()
        if not sms_config:
            raise Exception("SMS configuration not set")

        url = "https://api.textsms.co.ke/api/services/sendsms/"
        payload = {
            "apikey": sms_config.api_key,
            "partnerID": "your_partner_id",  # Replace with your TextSMS partner ID
            "message": message,
            "shortcode": sms_config.sender_id,
            "mobile": phone_number
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()

        # Log the SMS attempt
        SMSLog.objects.create(
            subscriber=subscriber,
            promotional_message=promotional_message,
            message_type=message_type,
            phone_number=phone_number,
            status='sent' if response.status_code == 200 else 'failed',
            response=str(response_data)
        )

        return response.status_code == 200

    except Exception as e:
        # Log the error
        SMSLog.objects.create(
            subscriber=subscriber,
            promotional_message=promotional_message,
            message_type=message_type,
            phone_number=phone_number,
            status='failed',
            response=str(e)
        )
        return False

def send_promotional_sms(phone_number, message, promotional_message, subscriber):
    return send_sms(
        phone_number=phone_number,
        message=message,
        message_type='promotional',
        subscriber=subscriber,
        promotional_message=promotional_message
    )

def send_login_code(phone_number, code):
    message = f"Your login code is: {code}. It expires in 10 minutes."
    return send_sms(
        phone_number=phone_number,
        message=message,
        message_type='login_code'
    )