# payments/utils.py

from django.utils import timezone
from payments.models import UserPayment
from subscription.models import UserSubscription, SubscriptionPlan

def process_payment(user, payment_method, plan, unique_reference, amount):
    # Create a payment entry
    payment = UserPayment.objects.create(
        user=user,
        payment_method=payment_method,
        plan=plan,
        unique_reference=unique_reference,
        amount=amount,
        is_verified=True,  # Assuming payment is verified for this example
        verified_at=timezone.now()
    )

    # Create or update the user subscription
    subscription, created = UserSubscription.objects.update_or_create(
        user=user,
        plan=plan,
        defaults={
            'expiry_date': timezone.now() + timezone.timedelta(days=30),  # Set to 30 days from now, for example
            'payment': payment  # Link the payment to the subscription
        }
    )

    return subscription
