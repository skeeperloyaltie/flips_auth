# sms/views.py
from django.http import JsonResponse
# from africastalking_config import sms


import africastalking

# Set your app credentials
username = "flipsadmin"    # Your Africa's Talking username
api_key = "831746d735117ec7a84b3fc64e6c47e39c7e417ffddd2c20f439ca77c93a4a20"      # Your Africa's Talking API key

# Initialize the SDK
africastalking.initialize(username, api_key)

# Get the SMS service
sms = africastalking.SMS

def send_sms(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        message = request.POST.get('message')

        if not phone_number or not message:
            return JsonResponse({'error': 'Phone number and message are required'}, status=400)

        try:
            # Use the SMS service to send the message
            response = sms.send(message, [phone_number])
            return JsonResponse({'success': response}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)
