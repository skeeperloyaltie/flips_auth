# support/views.py

import json
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from .models import Ticket
from .serializers import TicketSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Intro message for the chatbot
intro_message = (
    "Hello, welcome to FLIPS! How can we assist you today?\n"
    "Here are a few things I can help you with:\n"
    "1. Register an account\n"
    "2. Login to your account\n"
    "3. Learn about flood prediction services\n"
    "Please click on one of the buttons below or type your query."
)

# Sample responses for the chatbot
response_options = {
    "register": "You can register by providing your email and password. Would you like me to take you to the registration page?",
    "login": "If you already have an account, please login to access more features. Shall I take you to the login page?",
    "flood prediction": "Our flood prediction services provide real-time monitoring and alerts. Would you like to learn more about how this works?",
    "agent": "I will create a support ticket for you. Please provide a brief description of your issue.",
}

# Function to serve as the chatbot response handler
@csrf_exempt
def chatbot_response(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            message = data.get("message", "").strip().lower()
            logger.info("Received message: %s", message)
        except json.JSONDecodeError:
            logger.error("Invalid JSON received.")
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

        if not message:
            logger.info("Empty message received, returning intro message.")
            return JsonResponse({"response": intro_message}, status=200)

        # Handle specific commands or intents
        if message in response_options:
            response = response_options[message]
            logger.info("Matched intent: %s, response: %s", message, response)
            return JsonResponse({"response": response}, status=200)
        elif "agent" in message:
            logger.info("User requested to speak with an agent.")
            return JsonResponse(
                {"response": "Your request to talk to an agent has been received. Redirecting..."},
                status=200,
            )
        else:
            logger.warning("No intent matched for message: %s", message)
            return JsonResponse({"response": "I'm sorry, I didn't understand that. Could you please provide more details or click one of the options?"}, status=200)

    logger.error("Invalid request method.")
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)

# Function to handle ticket creation
@csrf_exempt
def create_ticket(request):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"status": "error", "message": "User not logged in"}, status=403
        )

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            subject = data.get("subject")
            description = data.get("description")
            ticket = Ticket.objects.create(
                user=request.user, subject=subject, description=description
            )
            send_ticket_notification(ticket)
            return JsonResponse(
                {"status": "success", "message": "Ticket created successfully"},
                status=200,
            )
        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Invalid JSON"}, status=400
            )
    return JsonResponse(
        {"status": "error", "message": "Invalid request method"}, status=400
    )

# Function to notify agents when a ticket is created
def send_ticket_notification(ticket):
    subject = f"New Support Ticket: {ticket.subject}"
    message = f"User {ticket.user.username} has created a new support ticket.\n\nSubject: {ticket.subject}\nDescription: {ticket.description}\n\nPlease respond as soon as possible."
    send_mail(subject, message, "support@flips.com", ["agent@flips.com"])
    logger.info(f"Notification sent for ticket {ticket.id}")

# API View to list tickets
@api_view(["GET"])
@login_required
def list_tickets(request):
    tickets = Ticket.objects.filter(user=request.user)
    serializer = TicketSerializer(tickets, many=True)
    return Response(serializer.data)

# Registration view
@csrf_exempt
def register_user(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")
            password = data.get("password")
            user = User.objects.create_user(
                username=email, email=email, password=password
            )
            UserProfile.objects.create(user=user)
            user = authenticate(username=email, password=password)
            if user is not None:
                login(request, user)
                return JsonResponse(
                    {
                        "status": "success",
                        "message": "User registered and logged in successfully",
                    },
                    status=200,
                )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse(
        {"status": "error", "message": "Invalid request method"}, status=400
    )

# View to check if the user session is active
@login_required
def check_session(request):
    return JsonResponse({"isAuthenticated": True})

# Render the chatbot on the landing page
def landing_page(request):
    return render(request, 'landing_page.html', {'intro_message': intro_message})
