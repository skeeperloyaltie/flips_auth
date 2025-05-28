from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.core.mail import send_mail
from django.utils import timezone
from .models import Subscriber, PromotionalMessage
from .serializers import SubscriberSerializer, PromotionalMessageSerializer
from sms.utils import send_promotional_sms  # Import SMS utility

class SubscribeView(generics.CreateAPIView):
    queryset = Subscriber.objects.all()
    serializer_class = SubscriberSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            subscriber = Subscriber.objects.get(email=request.data['email'])
            try:
                send_mail(
                    subject="Welcome to FLIPS Newsletter!",
                    message="Thank you for subscribing to FLIPS. Stay tuned for updates on flood prediction and more!",
                    from_email='your_email@example.com',
                    recipient_list=[subscriber.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Failed to send welcome email to {subscriber.email}: {str(e)}")

            if subscriber.phone_number:
                try:
                    send_promotional_sms(
                        phone_number=subscriber.phone_number,
                        message="Welcome to FLIPS! Stay tuned for updates.",
                        promotional_message=None,
                        subscriber=subscriber
                    )
                except Exception as e:
                    print(f"Failed to send welcome SMS to {subscriber.phone_number}: {str(e)}")
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
        email_success = True
        sms_success = True

        # Send email to subscribers
        for subscriber in subscribers:
            try:
                send_mail(
                    subject=promo_message.subject,
                    message=promo_message.message,
                    from_email='your_email@example.com',
                    recipient_list=[subscriber.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Failed to send email to {subscriber.email}: {str(e)}")
                email_success = False

        # Send SMS to subscribers with phone numbers
        for subscriber in subscribers:
            if subscriber.phone_number:
                try:
                    sms_sent = send_promotional_sms(
                        phone_number=subscriber.phone_number,
                        message=promo_message.message[:160],  # SMS character limit
                        promotional_message=promo_message,
                        subscriber=subscriber
                    )
                    if not sms_sent:
                        # Fallback to email if SMS fails
                        try:
                            send_mail(
                                subject=promo_message.subject,
                                message=f"SMS failed. Here's your message: {promo_message.message}",
                                from_email='your_email@example.com',
                                recipient_list=[subscriber.email],
                                fail_silently=False,
                            )
                        except Exception as e:
                            print(f"Fallback email failed for {subscriber.email}: {str(e)}")
                            email_success = False
                        sms_success = False
                except Exception as e:
                    print(f"Failed to send SMS to {subscriber.phone_number}: {str(e)}")
                    sms_success = False

        # Update promotional message status
        promo_message.sent_at = timezone.now()
        promo_message.email_sent = email_success
        promo_message.sms_sent = sms_success
        promo_message.save()