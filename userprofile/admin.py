from django.contrib import admin
from .models import UserProfile, PrivacyPolicyAcceptance

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription_status', 'get_subscription_plan')
    search_fields = ('user__username', 'subscription_plan__name')

    def get_subscription_plan(self, obj):
        return obj.subscription_plan.name if obj.subscription_plan else 'None'
    get_subscription_plan.short_description = 'Subscription Plan'

@admin.register(PrivacyPolicyAcceptance)
class PrivacyPolicyAcceptanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'accepted', 'accepted_date', 'policy_version')
    search_fields = ('user__username', 'email')