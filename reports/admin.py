from django.contrib import admin
from userprofile.models import UserProfile
from .views import SubscriptionBasedReportView
import io
import tempfile

# Ensure UserProfile is already registered
if admin.site.is_registered(UserProfile):
    # Get the existing admin class for UserProfile
    existing_admin_class = admin.site._registry[UserProfile].__class__

    # Define a custom action (e.g., report generation) and add it to the existing admin
    class CustomUserProfileAdmin(existing_admin_class):
        actions = ['generate_user_report']

        def generate_user_report(self, request, queryset):
            report_view = SubscriptionBasedReportView.as_view()

            for user_profile in queryset:
                # Simulate a request to the report view for each selected user
                request_data = {
                    'user': user_profile.user,
                }

                # Example format: can switch between 'csv' or 'pdf'
                report_format = 'csv'
                request.query_params = {'format': report_format}

                # Get the response from the view
                response = report_view(request, **request_data)

                if response.status_code == 200:
                    # Handle CSV format
                    if report_format == 'csv':
                        report_content = response.content.decode('utf-8')
                        filename = f'report_{user_profile.user.username}.csv'
                        report_file = io.StringIO(report_content)
                        self.save_report_to_file(user_profile, report_file, filename)

                    # Handle PDF format (if needed)
                    elif report_format == 'pdf':
                        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                        temp_pdf.write(response.content)
                        temp_pdf.close()
                        filename = f'report_{user_profile.user.username}.pdf'
                        self.save_report_to_file(user_profile, temp_pdf.name, filename)
                    
                    self.message_user(request, f"Report generated for {user_profile.user.username}.")
                else:
                    self.message_user(request, f"Failed to generate report for {user_profile.user.username}.", level='error')

        def save_report_to_file(self, user_profile, report_file, filename):
            """
            Save the generated report to a specified location.
            """
            # Placeholder implementation for saving the report
            with open(f'/path/to/save/location/{filename}', 'wb') as f:
                f.write(report_file.read())

        generate_user_report.short_description = 'Generate report for selected users'

    # Reassign the admin class with the new action
    admin.site._registry[UserProfile].actions += (CustomUserProfileAdmin.generate_user_report,)
