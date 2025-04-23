# insurance/admin.py
from django.contrib import admin
from .models import InsurancePlan, InsuranceProfile, InsuranceClaim, InsurancePayment

@admin.register(InsurancePlan)
class InsurancePlanAdmin(admin.ModelAdmin):
    """
    Admin interface for managing insurance plans.
    """
    list_display = ('name', 'premium', 'coverage_limit', 'duration_months', 'description_preview')
    search_fields = ('name', 'description')
    list_filter = ('duration_months',)

    def description_preview(self, obj):
        """
        Shorten the description for display in the admin interface.
        """
        return (obj.description[:50] + '...') if len(obj.description) > 50 else obj.description

    description_preview.short_description = 'Description Preview'


@admin.register(InsuranceProfile)
class InsuranceProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for managing user insurance profiles.
    """
    list_display = (
        'user_profile',
        'insured',
        'active_plan',
        'active_policies',
        'last_claim_date',
        'total_claimed'
    )
    search_fields = ('user_profile__user__username', 'active_plan__name')
    list_filter = ('insured', 'active_plan')

    def get_user_email(self, obj):
        """
        Display the associated user's email address.
        """
        return obj.user_profile.user.email

    get_user_email.short_description = 'User Email'


@admin.register(InsuranceClaim)
class InsuranceClaimAdmin(admin.ModelAdmin):
    """
    Admin interface for managing insurance claims.
    """
    list_display = (
        'id',
        'insurance_profile',
        'claim_amount',
        'claim_date',
        'status',
        'description_preview'
    )
    search_fields = (
        'insurance_profile__user_profile__user__username',
        'status'
    )
    list_filter = ('status', 'claim_date')
    ordering = ('-claim_date',)

    def description_preview(self, obj):
        """
        Shorten the description for display in the admin interface.
        """
        return (obj.description[:50] + '...') if obj.description else 'N/A'

    description_preview.short_description = 'Claim Description'


@admin.register(InsurancePayment)
class InsurancePaymentAdmin(admin.ModelAdmin):
    """
    Admin interface for managing insurance payments.
    """
    list_display = (
        'insurance_profile',
        'amount',
        'payment_date',
        'reference_number'
    )
    search_fields = (
        'insurance_profile__user_profile__user__username',
        'reference_number'
    )
    list_filter = ('payment_date',)
    ordering = ('-payment_date',)
