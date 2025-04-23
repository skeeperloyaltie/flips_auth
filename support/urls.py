# support/urls.py
from django.urls import path
from .views import (
    chatbot_response,
    create_ticket,
    list_tickets,
    register_user,
    check_session,
)

urlpatterns = [
    path("chatbot/", chatbot_response, name="chatbot-response"),
    path("create-ticket/", create_ticket, name="create-ticket"),
    path("tickets/", list_tickets, name="list-tickets"),
    path("register/", register_user, name="register-user"),
    path("check-session/", check_session, name="check-session"),
]
