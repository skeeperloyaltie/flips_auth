import logging
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.mail import send_mail
from .models import ContactSubmission
from .serializers import ContactSubmissionSerializer

# Set up logging
logger = logging.getLogger(__name__)

class ContactSubmissionView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = ContactSubmissionSerializer(data=request.data)
        if serializer.is_valid():
            # Save the contact submission
            submission = serializer.save()

            # Send confirmation email to the user
            try:
                subject = "Thank You for Contacting FLIPS"
                message = (
                    f"Dear {submission.name},\n\n"
                    "Thank you for reaching out to us! We have received your message and will get back to you soon.\n\n"
                    f"Details of your submission:\n"
                    f"Subject: {submission.subject}\n"
                    f"Message: {submission.message}\n\n"
                    "If you have any urgent inquiries, feel free to reach us at +254 700 168 812 or reply to this email.\n\n"
                    "Best regards,\n"
                    "The FLIPS Team\n"
                    "flipsintelligence@gmail.com"
                )
                send_mail(
                    subject=subject,
                    message=message,
                    from_email='flipsintelligence@gmail.com',
                    recipient_list=[submission.email],
                    fail_silently=False,
                )
                logger.info(f"Confirmation email sent to {submission.email} for contact submission: {submission.subject}")
            except Exception as e:
                # Log the error but don't fail the request
                logger.error(f"Failed to send confirmation email to {submission.email}: {str(e)}")

            return Response({"message": "Your message has been sent. Thank you!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)