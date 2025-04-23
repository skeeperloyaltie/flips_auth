import logging
from django.contrib import admin
from django.utils import timezone
from .models import PaymentMethod, UserPayment
from userprofile.models import UserProfile
from django.apps import apps

# Configure the logger for this module
logger = logging.getLogger(__name__)

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'account_number', 'paybill_number')
    search_fields = ('name', 'account_number', 'paybill_number')
    list_filter = ('name',)  # Filter by payment method name for large datasets

    def changelist_view(self, request, extra_context=None):
        """
        Log when the PaymentMethod list view is accessed.
        """
        logger.info(f"Admin accessed PaymentMethod list view (User: {request.user.username}).")
        return super().changelist_view(request, extra_context)


@admin.register(UserPayment)
class UserPaymentAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'payment_method', 'plan', 'unique_reference',
        'amount', 'status', 'is_verified', 'created_at', 'verified_at'
    )
    list_filter = ('status', 'is_verified', 'plan', 'payment_method', 'created_at')  # Enhanced filters
    search_fields = ('user__username', 'unique_reference', 'payment_method__name')  # Search options
    date_hierarchy = 'created_at'  # Allow filtering by date in a hierarchy
    actions = ['verify_payments', 'revoke_payments', 'mark_as_pending']

    def changelist_view(self, request, extra_context=None):
        """
        Log when the UserPayment list view is accessed.
        """
        logger.info(f"Admin accessed UserPayment list view (User: {request.user.username}).")
        return super().changelist_view(request, extra_context)

    def verify_payments(self, request, queryset):
        """
        Admin action to verify selected payments in bulk.
        """
        verified_count = 0

        for payment in queryset.filter(is_verified=False):
            payment.is_verified = True
            payment.status = "verified"
            payment.verified_at = timezone.now()
            payment.save()
            self.update_subscription_status(payment)
            verified_count += 1

            logger.info(f"Verified payment for user {payment.user.username} (Ref: {payment.unique_reference}).")

        self.message_user(request, f"{verified_count} payments verified successfully.")
        logger.info(f"Admin {request.user.username} verified {verified_count} payments.")

    verify_payments.short_description = "Verify selected payments"

    def revoke_payments(self, request, queryset):
        """
        Admin action to revoke selected payments in bulk.
        """
        revoked_count = 0

        for payment in queryset.filter(is_verified=True):
            payment.is_verified = False
            payment.status = "revoked"
            payment.verified_at = None
            payment.save()
            self.update_subscription_status(payment)
            revoked_count += 1

            logger.info(f"Revoked verification for payment (User: {payment.user.username}, Ref: {payment.unique_reference}).")

        self.message_user(request, f"{revoked_count} payments revoked successfully.")
        logger.info(f"Admin {request.user.username} revoked {revoked_count} payments.")

    revoke_payments.short_description = "Revoke selected payments"

    def mark_as_pending(self, request, queryset):
        """
        Admin action to mark selected payments as pending.
        """
        pending_count = 0

        for payment in queryset:
            if payment.status != "pending":
                payment.status = "pending"
                payment.is_verified = False
                payment.verified_at = None
                payment.save()
                self.update_subscription_status(payment)
                pending_count += 1

                logger.info(f"Marked payment as pending (User: {payment.user.username}, Ref: {payment.unique_reference}).")

        self.message_user(request, f"{pending_count} payments marked as pending.")
        logger.info(f"Admin {request.user.username} marked {pending_count} payments as pending.")

    mark_as_pending.short_description = "Mark selected payments as pending"

    def save_model(self, request, obj, form, change):
        """
        Save the payment model and log admin actions.
        """
        if change:
            logger.info(f"Admin {request.user.username} updated payment for {obj.user.username} (Ref: {obj.unique_reference}).")
        else:
            logger.info(f"Admin {request.user.username} created a new payment for {obj.user.username}.")

        super().save_model(request, obj, form, change)
        if obj.is_verified:
            self.update_subscription_status(obj)

    def update_subscription_status(self, payment):
        """
        Updates the subscription status and user profile for a payment.
        """
        try:
            logger.info(f"Updating subscription for user {payment.user.username} (Ref: {payment.unique_reference}).")

            # Retrieve SubscriptionPlan and UserSubscription models
            SubscriptionPlan = apps.get_model('subscription', 'SubscriptionPlan')
            UserSubscription = apps.get_model('subscription', 'UserSubscription')

            # Update or create the user's subscription
            user_subscription, created = UserSubscription.objects.get_or_create(
                user=payment.user,
                plan=payment.plan,
                defaults={
                    'start_date': timezone.now(),
                    'end_date': timezone.now() + timezone.timedelta(days=30),
                    'active': payment.is_verified
                }
            )

            if not created:
                user_subscription.active = payment.is_verified
                user_subscription.end_date = timezone.now() + timezone.timedelta(days=30)
                user_subscription.save()

            # Update the user's profile
            user_profile, created = UserProfile.objects.get_or_create(user=payment.user)
            user_profile.subscription_status = payment.is_verified
            user_profile.subscription_level = payment.plan.name
            user_profile.subscription_plan = payment.plan
            user_profile.expiry_date = timezone.now() + timezone.timedelta(days=30)
            user_profile.save()

            logger.info(f"Subscription and profile updated for user {payment.user.username}.")
        except Exception as e:
            logger.error(f"Failed to update subscription for user {payment.user.username}: {e}")
