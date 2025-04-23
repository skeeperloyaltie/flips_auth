from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription_status', 'subscription_level')
    search_fields = ('user__username', 'subscription_level')