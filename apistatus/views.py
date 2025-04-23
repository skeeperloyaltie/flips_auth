import subprocess
from django.http import HttpResponse
from django.apps import apps
from importlib import import_module
from django.urls import (
    get_resolver,
    URLPattern,
    URLResolver,
)  # Importing get_resolver and necessary URL utilities

# List of apps to check status
APPS_TO_CHECK = [
    "allauth",
    "monitoring",
    "payments",
    "apistatus",
    "api_monitor",
    "api",
    "prediction",
    "subscription",
    "payments",
]


# Function to dynamically fetch the sub-URLs for a specific app
def get_app_urls(app_name):
    """
    Get all URLs for a specific app using its URLConf.
    """
    try:
        app_urls_module = import_module(f"{app_name}.urls")
        resolver = get_resolver(app_urls_module.__name__)
        url_patterns = resolver.url_patterns

        # Extract the paths and names of the sub-URLs
        subcategories = []
        for pattern in url_patterns:
            if isinstance(pattern, URLPattern):
                # Handle regular URL patterns with name and path
                subcategories.append(
                    {
                        "url": pattern.pattern.describe(),
                        "name": pattern.name or "(Unnamed)",  # Handle unnamed patterns
                    }
                )
            elif isinstance(pattern, URLResolver):
                # Handle included URL resolvers (skip these for now)
                subcategories.append(
                    {"url": pattern.pattern.describe(), "name": "URLResolver"}
                )
        return subcategories
    except ImportError:
        print(f"No URLs found for {app_name}")
        return []


# Function to run the tests for a specific app
def run_tests_for_app(app_name):
    """
    Run `python manage.py test <app_name>` and return whether the test passed.
    """
    try:
        result = subprocess.run(
            ["python", "manage.py", "test", app_name], capture_output=True, text=True
        )
        return result.returncode == 0  # If returncode is 0, the tests passed
    except Exception as e:
        print(f"Error running tests for {app_name}: {e}")
        return False


# Function to generate the HTML status page with Bootstrap
def generate_api_status_html():
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <title>API Status</title>
        <style>
            .working { background-color: #32CD32; color: white; }
            .not-working { background-color: #FF6347; color: white; }
            .container { margin-top: 50px; }
            .sub-url { margin-left: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="text-center">API Status</h1>
            <div class="list-group">
    """

    # Iterate through each app in the filtered installed apps
    for app in apps.get_app_configs():
        app_name = app.label
        if app_name not in APPS_TO_CHECK:  # Skip apps not in the list
            continue

        # Run tests for the main app
        tests_passed = run_tests_for_app(app_name)

        # Determine CSS class based on the test result
        status_class = "working" if tests_passed else "not-working"

        # Add the app section to the HTML
        html += f"""
            <a href="#" class="list-group-item list-group-item-action {status_class}">
                {app_name} - {'Working' if tests_passed else 'Not Working'}
            </a>
        """

        # Fetch sub-URLs for the app (if applicable)
        subcategories = get_app_urls(app_name)
        for sub in subcategories:
            # Normally you wouldn't run tests for sub-URLs specifically, but for demonstration purposes,
            # we could repeat the main test here.
            sub_tests_passed = run_tests_for_app(app_name)
            sub_status_class = "working" if sub_tests_passed else "not-working"

            # Add the sub-URL section to the HTML
            html += f"""
                <a href="#" class="list-group-item list-group-item-action sub-url {sub_status_class}">
                    &nbsp;&nbsp;&nbsp;{sub['url']} - {'Working' if sub_tests_passed else 'Not Working'}
                </a>
            """

    # Close the HTML tags
    html += """
            </div>
        </div>
    </body>
    </html>
    """
    return html


# Django view to return the HTML page
def endpoint_status_view(request):
    # Generate the HTML for the API status page
    html_content = generate_api_status_html()
    return HttpResponse(html_content, content_type="text/html")
