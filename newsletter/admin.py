from django.contrib import admin
from django.utils import timezone
from django.core.mail import send_mail
from .models import Subscriber, PromotionalMessage
from sms.utils import send_promotional_sms  # Assuming this exists as per your views.py

class SubscriberAdmin(admin.ModelAdmin):
    # Fields to display in the list view
    list_display = ('email', 'phone_number', 'has_phone_number', 'subscribed_at')
    
    # Fields that can be searched
    search_fields = ('email', 'phone_number')
    
    # Filters for the sidebar
    list_filter = ('subscribed_at',)
    
    # Make some fields read-only in the form view
    readonly_fields = ('subscribed_at',)
    
    # Fields to display in the form view (optional, for clarity)
    fields = ('email', 'phone_number', 'subscribed_at')
    
    # Custom column to indicate if the subscriber has a phone number
    def has_phone_number(self, obj):
        return bool(obj.phone_number)
    has_phone_number.boolean = True  # Displays as a green checkmark or red cross
    has_phone_number.short_description = 'Has Phone Number'

class PromotionalMessageAdmin(admin.ModelAdmin):
    # Fields to display in the list view
    list_display = ('subject', 'created_at', 'sent_at', 'email_sent', 'sms_sent', 'sent_status')
    
    # Fields that can be searched
    search_fields = ('subject', 'message')
    
    # Filters for the sidebar
    list_filter = ('created_at', 'sent_at', 'email_sent', 'sms_sent')
    
    # Make some fields read-only in the form view
    readonly_fields = ('created_at', 'sent_at', 'email_sent', 'sms_sent')
    
    # Fields to display in the form view
    fields = ('subject', 'message', 'created_at', 'sent_at', 'email_sent', 'sms_sent')
    
    # Custom actions
    actions = ['resend_promotional_message']
    
    # Custom column to show sent status
    def sent_status(self, obj):
        if obj.sent_at:
            return "Sent" if (obj.email_sent or obj.sms_sent) else "Failed"
        return "Not Sent"
    sent_status.short_description = 'Status'
    
    # Custom action to resend promotional messages
    def resend_promotional_message(self, request, queryset):
        for promo_message in queryset:
            # Reset the sent status
            promo_message.sent_at = None
            promo_message.email_sent = False
            promo_message.sms_sent = False
            promo_message.save()
            
            # Resend to all subscribers
            subscribers = Subscriber.objects.all()
            email_success = True
            sms_success = True
            
            # Send email to subscribers
            for subscriber in subscribers:
                try:
                    send_mail(
                        subject=promo_message.subject,
                        message=promo_message.message,
                        from_email='info.flipsinteligence@gmail.com',
                        recipient_list=[subscriber.email],
                        fail_silently=False,
                    )
                except Exception as e:
                    self.message_user(request, f"Failed to send email to {subscriber.email}: {str(e)}", level='error')
                    email_success = False
            
            # Send SMS to subscribers with phone numbers
            for subscriber in subscribers:
                if subscriber.phone_number:
                    try:
                        sms_sent = send_promotional_sms(
                            phone_number=subscriber.phone_number,
                            message=promo_message.message[:160],
                            promotional_message=promo_message,
                            subscriber=subscriber
                        )
                        if not sms_sent:
                            try:
                                send_mail(
                                    subject=promo_message.subject,
                                    message=f"SMS failed. Here's your message: {promo_message.message}",
                                    from_email='info.flipsinteligence@gmail.com',
                                    recipient_list=[subscriber.email],
                                    fail_silently=False,
                                )
                            except Exception as e:
                                self.message_user(request, f"Fallback email failed for {subscriber.email}: {str(e)}", level='error')
                                email_success = False
                            sms_success = False
                    except Exception as e:
                        self.message_user(request, f"Failed to send SMS to {subscriber.phone_number}: {str(e)}", level='error')
                        sms_success = False
            
            # Update promotional message status
            promo_message.sent_at = timezone.now()
            promo_message.email_sent = email_success
            promo_message.sms_sent = sms_success
            promo_message.save()
            
            # Notify admin of success
            self.message_user(request, f"Promotional message '{promo_message.subject}' resent to {subscribers.count()} subscribers.")
    
    resend_promotional_message.short_description = "Resend selected promotional messages to all subscribers"

admin.site.register(Subscriber, SubscriberAdmin)
admin.site.register(PromotionalMessage, PromotionalMessageAdmin)