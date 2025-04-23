#
# from django.db import models
# from django.contrib.auth.models import User
# from payments.models import UserPayment  # Import UserPayment from payments
#
# class SubscriptionPlan(models.Model):
#     name = models.CharField(max_length=50)
#     access_duration = models.IntegerField(help_text="Time limit in minutes for free users")
#     description = models.TextField()
#
#     def __str__(self):
#         return self.name
#
# class UserSubscription(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
#     expiry_date = models.DateTimeField()
#     payment = models.OneToOneField(UserPayment, on_delete=models.CASCADE, null=True, blank=True)  # Link to UserPayment
#
#     def __str__(self):
#         return f"{self.user.username}'s subscription to {self.plan.name}"
