from django.contrib import admin
from django.contrib import messages
from django.db import connection
from .models import UserProfile, PrivacyPolicyAcceptance
import logging

logger = logging.getLogger(__name__)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription_status', 'get_subscription_plan')
    search_fields = ('user__username', 'subscription_plan__name')
    actions = ['check_health']

    def get_subscription_plan(self, obj):
        return obj.subscription_plan.name if obj.subscription_plan else 'None'
    get_subscription_plan.short_description = 'Subscription Plan'

    def check_health(self, request, queryset):
        try:
            # Check database connectivity
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result[0] != 1:
                    logger.error("Admin health check failed: Invalid query result")
                    self.message_user(
                        request,
                        "Health check failed: Database returned invalid result",
                        level=messages.ERROR
                    )
                    return

            logger.info("Admin health check successful: Server and database are operational")
            self.message_user(
                request,
                "Health check successful: Server and database are operational",
                level=messages.SUCCESS
            )

        except Exception as e:
            logger.error(f"Admin health check failed: {str(e)}")
            self.message_user(
                request,
                f"Health check failed: {str(e)}",
                level=messages.ERROR
            )
    check_health.short_description = "Check server and database health"

@admin.register(PrivacyPolicyAcceptance)
class PrivacyPolicyAcceptanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'accepted', 'accepted_date', 'policy_version')
    search_fields = ('user__username', 'email')
    actions = ['check_health']

    def check_health(self, request, queryset):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result[0] != 1:
                    logger.error("Admin health check failed: Invalid query result")
                    self.message_user(
                        request,
                        "Health check failed: Database returned invalid result",
                        level=messages.ERROR
                    )
                    return

            logger.info("Admin health check successful: Server and database are operational")
            self.message_user(
                request,
                "Health check successful: Server and database are operational",
                level=messages.SUCCESS
            )

        except Exception as e:
            logger.error(f"Admin health check failed: {str(e)}")
            self.message_user(
                request,
                f"Health check failed: {str(e)}",
                level=messages.ERROR
            )
    check_health.short_description = "Check server and database health"