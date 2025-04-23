# activity_logger/admin.py

from django.contrib import admin
from .models import UserActivity

class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'path', 'method', 'timestamp', 'ip_address', 'user_agent']
    list_filter = ['user_profile__user__username', 'method', 'timestamp']  # Allow filtering by users
    search_fields = ['user_profile__user__username', 'path']  # Allow search by username or path
    readonly_fields = ['user_profile', 'path', 'method', 'timestamp', 'ip_address', 'user_agent']  # Disable editing

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of logs by any user (including superusers)."""
        return False

# Register the model with the admin site
admin.site.register(UserActivity, UserActivityAdmin)
