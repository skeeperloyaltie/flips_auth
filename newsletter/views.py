from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.core.mail import send_mail
from django.utils import timezone
from .models import Subscriber, PromotionalMessage
from .serializers import SubscriberSerializer, PromotionalMessageSerializer

class SubscribeView(generics.CreateAPIView):
    queryset = Subscriber.objects.all()
    serializer_class = SubscriberSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            # Additional actions if needed
            pass
        return response

class PromotionalMessageView(generics.ListCreateAPIView):
    queryset = PromotionalMessage.objects.all()
    serializer_class = PromotionalMessageSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        promo_message = serializer.save()
        self.send_promotion(promo_message)

    def send_promotion(self, promo_message):
        subscribers = Subscriber.objects.all()
        for subscriber in subscribers:
            send_mail(
                promo_message.subject,
                promo_message.message,
                'your_email@example.com',  # from email
                [subscriber.email],
                fail_silently=False,
            )
        promo_message.sent_at = timezone.now()
        promo_message.save()