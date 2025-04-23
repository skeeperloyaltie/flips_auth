#
# import logging
# from rest_framework import permissions
# from .models import UserSubscription  # Ensure your UserSubscription model is imported
#
# # Initialize logging
# logger = logging.getLogger(__name__)
#
# class IsStaffOrGovtPlan(permissions.BasePermission):
#     """
#     Custom permission to only allow staff or users with a government plan to access the view.
#     """
#
#     def has_permission(self, request, view):
#         # Log the user's details for debugging
#         logger.debug(f"Checking permissions for user: {request.user.username}, Staff: {request.user.is_staff}")
#
#         # Check if the user is staff
#         if request.user.is_staff:
#             logger.debug("Access granted: User is staff.")
#             return True
#
#         # Check if the user has a subscription
#         try:
#             subscription = UserSubscription.objects.get(user=request.user)
#             # Allow access if user has a government plan
#             if subscription.plan.name == 'government':
#                 logger.debug("Access granted: User has government plan.")
#                 return True
#             else:
#                 logger.debug("Access denied: User does not have a government plan.")
#         except UserSubscription.DoesNotExist:
#             logger.debug("Access denied: User has no subscription.")
#
#         return False
