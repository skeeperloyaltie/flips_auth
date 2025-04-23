from django.contrib import admin
from .models import Subscriber, PromotionalMessage

class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at')

class PromotionalMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'created_at', 'sent_at')

admin.site.register(Subscriber, SubscriberAdmin)
admin.site.register(PromotionalMessage, PromotionalMessageAdmin)