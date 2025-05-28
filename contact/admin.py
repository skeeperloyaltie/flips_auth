# contact/admin.py
from django.contrib import admin
from django.core.mail import send_mail
from .models import ContactSubmission

class ContactSubmissionAdmin(admin.ModelAdmin):
    # Fields to display in the list view
    list_display = ('name', 'email', 'subject', 'created_at', 'message_preview')
    
    # Fields that can be searched
    search_fields = ('name', 'email', 'subject', 'message')
    
    # Filters for the sidebar
    list_filter = ('created_at',)
    
    # Make some fields read-only in the form view
    readonly_fields = ('created_at',)
    
    # Fields to display in the form view (optional, for clarity)
    fields = ('name', 'email', 'subject', 'message', 'created_at')
    
    # Custom actions
    actions = ['send_feedback_email']
    
    # Custom column to show a preview of the message
    def message_preview(self, obj):
        return obj.message[:50] + ('...' if len(obj.message) > 50 else '')
    message_preview.short_description = 'Message Preview'
    
    # Custom action to send feedback emails
    def send_feedback_email(self, request, queryset):
        for submission in queryset:
            try:
                # Send feedback email to the user
                subject = f"Feedback on Your Inquiry: {submission.subject}"
                message = (
                    f"Dear {submission.name},\n\n"
                    "Thank you for reaching out to FLIPS with your inquiry.\n\n"
                    f"Subject: {submission.subject}\n"
                    f"Your Message: {submission.message}\n\n"
                    "We have received your message and our team is reviewing it. "
                    "We will get back to you shortly with more information or a resolution. "
                    "If you have any further questions, feel free to contact us at flipsintelligence@gmail.com.\n\n"
                    "Best regards,\n"
                    "The FLIPS Team"
                )
                send_mail(
                    subject=subject,
                    message=message,
                    from_email='flipsintelligence@gmail.com',
                    recipient_list=[submission.email],
                    fail_silently=False,
                )
                # Notify admin of success
                self.message_user(request, f"Feedback email sent to {submission.email} for inquiry: {submission.subject}")
            except Exception as e:
                # Notify admin of failure
                self.message_user(
                    request,
                    f"Failed to send feedback email to {submission.email}: {str(e)}",
                    level='error'
                )
    
    send_feedback_email.short_description = "Send feedback email to selected contacts"

admin.site.register(ContactSubmission, ContactSubmissionAdmin)