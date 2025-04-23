from rest_framework import generics, permissions
from rest_framework.response import Response
from django.utils.timezone import now
from django.utils.dateparse import parse_date
from datetime import timedelta
from monitor.models import WaterLevelData
from userprofile.models import UserProfile
import csv
import io
import matplotlib.pyplot as plt
from weasyprint import HTML
import tempfile
from django.http import HttpResponse
from django.http import HttpResponse, HttpResponseForbidden
from rest_framework import generics, permissions
from rest_framework.response import Response
from django.utils.timezone import now
from django.utils.dateparse import parse_date
from datetime import timedelta
from monitor.models import WaterLevelData
from userprofile.models import UserProfile
import csv
import io
import matplotlib.pyplot as plt
from weasyprint import HTML
import tempfile

class SubscriptionBasedReportView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        report_format = request.query_params.get('format', 'csv')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            return Response({"detail": "UserProfile not found."}, status=404)

        subscription_plan = profile.subscription_plan
        report_data = self.generate_report_data(subscription_plan, start_date, end_date)

        # Check if the user is allowed to download PDF (government or admin)
        if report_format == 'pdf':
            if subscription_plan == 'government' or user.is_staff:  # Add admin check
                return self.export_as_pdf(report_data, profile)
            else:
                return HttpResponseForbidden("PDF reports are only available to government users or admins.")
        else:
            return self.export_as_csv(report_data)

    def generate_report_data(self, subscription_plan, start_date, end_date):
        start_date = parse_date(start_date) if start_date else None
        end_date = parse_date(end_date) if end_date else None

        if subscription_plan == 'free':
            start_date = start_date or (now() - timedelta(hours=1))  # Free tier limited to last hour
            data = WaterLevelData.objects.filter(timestamp__gte=start_date).values('rig__sensor_id', 'level', 'timestamp')
        elif subscription_plan in ['corporate', 'government']:
            query = WaterLevelData.objects.all()
            if start_date:
                query = query.filter(timestamp__gte=start_date)
            if end_date:
                query = query.filter(timestamp__lte=end_date)
            data = query.values('rig__sensor_id', 'level', 'timestamp')
        else:
            data = []
        return data

    def export_as_csv(self, data):
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(['Rig Sensor ID', 'Water Level', 'Timestamp'])
        for row in data:
            writer.writerow([row['rig__sensor_id'], row['level'], row['timestamp']])
        
        response = HttpResponse(csv_buffer.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="report.csv"'
        return response

    def export_as_pdf(self, data, profile):
        with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as temp_pdf:
            fig, ax = plt.subplots()
            levels = [item['level'] for item in data]
            timestamps = [item['timestamp'] for item in data]
            ax.plot(timestamps, levels, label='Water Levels')

            ax.set(xlabel='Timestamp', ylabel='Water Level', title='Water Level Report')
            ax.grid()

            graph_img_path = tempfile.mktemp(suffix=".png")
            plt.savefig(graph_img_path)
            plt.close(fig)

            html_content = f"""
            <html>
            <head><title>Water Level Report</title></head>
            <body>
                <h1>Water Level Report</h1>
                <p>Generated for: {profile.user.username}</p>
                <p>Current Plan: {profile.subscription_plan}</p>
                <p>Generated on: {now().strftime('%Y-%m-%d %H:%M')}</p>
                <h2>Graph:</h2>
                <img src="file://{graph_img_path}" alt="Water Level Graph" />
                <h2>Data:</h2>
                <table border="1">
                    <tr><th>Rig Sensor ID</th><th>Water Level</th><th>Timestamp</th></tr>
                    {''.join([f"<tr><td>{row['rig__sensor_id']}</td><td>{row['level']}</td><td>{row['timestamp']}</td></tr>" for row in data])}
                </table>
            </body>
            </html>
            """

            HTML(string=html_content).write_pdf(temp_pdf.name)

            with open(temp_pdf.name, 'rb') as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="report.pdf"'
                return response



class CustomReportView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        model_type = request.query_params.get('model', 'WaterLevelData')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        report_format = request.query_params.get('format', 'csv')

        # Convert start and end date to date objects
        start_date = parse_date(start_date) if start_date else None
        end_date = parse_date(end_date) if end_date else None

        # Generate data based on model and date range
        data = self.generate_custom_report(model_type, start_date, end_date)

        if report_format == 'pdf':
            return self.export_as_pdf(data)
        else:
            return self.export_as_csv(data)

    def generate_custom_report(self, model_type, start_date, end_date):
        query = WaterLevelData.objects.all()
        if start_date:
            query = query.filter(timestamp__gte=start_date)
        if end_date:
            query = query.filter(timestamp__lte=end_date)
        data = query.values('rig__sensor_id', 'level', 'timestamp')
        return data

    def export_as_csv(self, data):
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(['Rig Sensor ID', 'Water Level', 'Timestamp'])
        for row in data:
            writer.writerow([row['rig__sensor_id'], row['level'], row['timestamp']])
        response = Response(csv_buffer.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="report.csv"'
        return response

    def export_as_pdf(self, data):
        with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as temp_pdf:
            fig, ax = plt.subplots()
            levels = [item['level'] for item in data]
            timestamps = [item['timestamp'] for item in data]
            ax.plot(timestamps, levels, label='Water Levels')

            ax.set(xlabel='Timestamp', ylabel='Water Level', title='Water Level Report')
            ax.grid()

            graph_img_path = tempfile.mktemp(suffix=".png")
            plt.savefig(graph_img_path)
            plt.close(fig)

            html_content = f"""
            <html>
            <head><title>Water Level Report</title></head>
            <body>
                <h1>Water Level Report</h1>
                <p>Generated on: {now().strftime('%Y-%m-%d %H:%M')}</p>
                <h2>Graph:</h2>
                <img src="file://{graph_img_path}" alt="Water Level Graph" />
                <h2>Data:</h2>
                <table border="1">
                    <tr><th>Rig Sensor ID</th><th>Water Level</th><th>Timestamp</th></tr>
                    {''.join([f"<tr><td>{row['rig__sensor_id']}</td><td>{row['level']}</td><td>{row['timestamp']}</td></tr>" for row in data])}
                </table>
            </body>
            </html>
            """

            HTML(string=html_content).write_pdf(temp_pdf.name)

            with open(temp_pdf.name, 'rb') as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="report.pdf"'
                return response
