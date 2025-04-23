class Task:
    def __init__(self, name, assigned_to, due_date, sub_tasks=None):
        self.name = name
        self.assigned_to = assigned_to
        self.due_date = due_date
        self.sub_tasks = sub_tasks if sub_tasks else []

    def __str__(self):
        return f"{self.name} - Assigned to: {self.assigned_to} - Due: {self.due_date}"

class WorkPlan:
    def __init__(self):
        self.tasks = []

    def add_task(self, task):
        self.tasks.append(task)

    def display_plan(self):
        for task in self.tasks:
            print(f"Task: {task.name} - Assigned to: {task.assigned_to} - Due Date: {task.due_date}")
            if task.sub_tasks:
                print("Subtasks:")
                for sub_task in task.sub_tasks:
                    print(f"\t- {sub_task}")
            print("\n")

# Initialize work plan
work_plan = WorkPlan()

# James's tasks
payment_module_ui = Task(
    name="Payment Module UI Design",
    assigned_to="James",
    due_date="Week 1",
    sub_tasks=[
        "Design the payment page",
        "Integrate various payment options",
        "Ensure responsiveness across devices"
    ]
)

payment_api_integration = Task(
    name="Payment API Integration",
    assigned_to="James",
    due_date="Week 2",
    sub_tasks=[
        "Connect frontend payment form with backend API",
        "Handle token generation for secure payments"
    ]
)

auth_ui = Task(
    name="UI for User Authentication",
    assigned_to="James",
    due_date="Week 1",
    sub_tasks=[
        "Design login and registration forms",
        "Ensure token storage on frontend"
    ]
)

subscription_ui = Task(
    name="UI for Subscription Management",
    assigned_to="James",
    due_date="Week 2",
    sub_tasks=[
        "Build interface for plan selection",
        "Display subscription status"
    ]
)

dashboard_ui = Task(
    name="Real-time Data Dashboard (Frontend)",
    assigned_to="James",
    due_date="Week 2",
    sub_tasks=[
        "Integrate Chart.js for real-time data visualization",
        "Display water levels, humidity, and temperature"
    ]
)

map_visualization = Task(
    name="Map Visualization",
    assigned_to="James",
    due_date="Week 3",
    sub_tasks=[
        "Implement flood monitoring map using Leaflet.js",
        "Ensure smooth map interaction"
    ]
)

# Godfrey's tasks
user_auth_api = Task(
    name="User Authentication API",
    assigned_to="Godfrey",
    due_date="Week 1",
    sub_tasks=[
        "Design authentication API",
        "Integrate JWT for token-based authentication"
    ]
)

subscription_api = Task(
    name="Subscription API Design",
    assigned_to="Godfrey",
    due_date="Week 2",
    sub_tasks=[
        "Create subscription management API",
        "Handle subscription upgrades and downgrades"
    ]
)

data_apis = Task(
    name="Real-time Data APIs",
    assigned_to="Godfrey",
    due_date="Week 1",
    sub_tasks=[
        "API for water levels (/monitoring/water-levels/)",
        "API for humidity (/monitoring/humidity/)",
        "API for temperature (/monitoring/temperature/)"
    ]
)

prediction_models = Task(
    name="Prediction Models Implementation",
    assigned_to="Godfrey",
    due_date="Week 3",
    sub_tasks=[
        "Linear Regression for water levels prediction",
        "Polynomial Regression for complex data trends",
        "ARIMA/SARIMA for time-series forecasting"
    ]
)

flood_monitoring_backend = Task(
    name="Flood Monitoring Backend",
    assigned_to="Godfrey",
    due_date="Week 3",
    sub_tasks=[
        "Fetch GIS and Google Earth Engine (GEE) data",
        "Process and serve real-time flood data",
        "Use Kalman Filter and ARIMAX for real-time prediction"
    ]
)

sms_alert_integration = Task(
    name="SMS Alert System Integration",
    assigned_to="Godfrey",
    due_date="Week 4",
    sub_tasks=[
        "Integrate SMS alerts via AfricasTalking or AWS SNS",
        "Send notifications for critical flood levels"
    ]
)

testing_debugging = Task(
    name="Testing & Debugging",
    assigned_to="Both",
    due_date="Week 4",
    sub_tasks=[
        "Unit testing for APIs",
        "Frontend integration testing",
        "End-to-end testing"
    ]
)

# Add all tasks to the work plan
work_plan.add_task(payment_module_ui)
work_plan.add_task(payment_api_integration)
work_plan.add_task(auth_ui)
work_plan.add_task(subscription_ui)
work_plan.add_task(dashboard_ui)
work_plan.add_task(map_visualization)

work_plan.add_task(user_auth_api)
work_plan.add_task(subscription_api)
work_plan.add_task(data_apis)
work_plan.add_task(prediction_models)
work_plan.add_task(flood_monitoring_backend)
work_plan.add_task(sms_alert_integration)
work_plan.add_task(testing_debugging)

# Display the work plan
work_plan.display_plan()
