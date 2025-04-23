from graphviz import Digraph

def generate_work_plan_flowchart():
    # Create a Digraph object
    dot = Digraph('Work Plan', comment='James and Godfrey Work Plan')

    # Define styles for different types of nodes
    james_node_attr = {'shape': 'rectangle', 'style': 'filled', 'fillcolor': '#87CEEB'}  # Light blue for James
    godfrey_node_attr = {'shape': 'rectangle', 'style': 'filled', 'fillcolor': '#FFA500'}  # Orange for Godfrey
    both_node_attr = {'shape': 'rectangle', 'style': 'filled', 'fillcolor': '#90EE90'}  # Light green for tasks involving both

    # Start and End shapes
    dot.node('Start', 'Start', shape='oval', style='filled', fillcolor='#90EE90')
    dot.node('End', 'End', shape='oval', style='filled', fillcolor='#90EE90')

    ### JAMES'S TASKS ###
    # Payment Module UI Design and Payment API Integration
    dot.node('PaymentModuleUI', 'Payment Module UI Design\n(James, Week 1)', **james_node_attr)
    dot.node('PaymentAPI', 'Payment API Integration\n(James, Week 2)', **james_node_attr)
    dot.node('PaymentAPI_UseCase', 'Connect UI to API, Token Management\n(Secure Payment)', **james_node_attr)

    # User Authentication UI Design
    dot.node('AuthUI', 'User Authentication UI Design\n(James, Week 1)', **james_node_attr)
    dot.node('AuthUI_UseCase', 'Design Login/Registration Form\n(Token Storage)', **james_node_attr)

    # Subscription Management UI Design
    dot.node('SubscriptionUI', 'Subscription Management UI\n(James, Week 2)', **james_node_attr)
    dot.node('SubscriptionUI_UseCase', 'Plan Selection, Subscription Status', **james_node_attr)

    # Real-time Data Dashboard (Frontend)
    dot.node('DashboardUI', 'Real-time Data Dashboard UI\n(James, Week 2)', **james_node_attr)
    dot.node('DashboardUI_UseCase', 'Integrate APIs, Display Data\n(Chart.js)', **james_node_attr)

    # Map Visualization (Frontend)
    dot.node('MapVisualization', 'Map Visualization (Leaflet.js)\n(James, Week 3)', **james_node_attr)
    dot.node('MapVisualization_UseCase', 'Integrate GIS Data, Display\nFlood Zones', **james_node_attr)

    ### GODFREY'S TASKS ###
    # User Authentication API
    dot.node('AuthAPI', 'User Authentication API\n(Godfrey, Week 1)', **godfrey_node_attr)
    dot.node('AuthAPI_UseCase', 'JWT Token Management, Validate User\n(API: /api/auth)', **godfrey_node_attr)

    # Subscription API
    dot.node('SubscriptionAPI', 'Subscription API Design\n(Godfrey, Week 2)', **godfrey_node_attr)
    dot.node('SubscriptionAPI_UseCase', 'Manage Plans, Handle\nUpgrades/Downgrades\n(API: /api/subscription)', **godfrey_node_attr)

    # Real-time Data APIs
    dot.node('DataAPIs', 'Real-time Data APIs\n(Godfrey, Week 1)', **godfrey_node_attr)
    dot.node('DataAPIs_UseCase', 'Water Levels, Humidity, Temperature\n(API: /monitoring/water-levels)', **godfrey_node_attr)

    # Prediction Models Implementation
    dot.node('PredictionModels', 'Prediction Models Implementation\n(Godfrey, Week 3)', **godfrey_node_attr)
    dot.node('PredictionModels_UseCase', 'Linear Regression, ARIMA/SARIMA\n(API: /api/predict)', **godfrey_node_attr)

    # Flood Monitoring Backend
    dot.node('FloodMonitoring', 'Flood Monitoring Backend\n(Godfrey, Week 3)', **godfrey_node_attr)
    dot.node('FloodMonitoring_UseCase', 'Fetch GIS Data, Kalman Filter\n(API: /api/flood-monitoring)', **godfrey_node_attr)

    # SMS Alert System Integration
    dot.node('SMSAlerts', 'SMS Alert System Integration\n(Godfrey, Week 4)', **godfrey_node_attr)
    dot.node('SMSAlerts_UseCase', 'AWS SNS, AfricasTalking Integration\nNotify Critical Flood Levels', **godfrey_node_attr)

    ### SHARED TASKS ###
    # Testing & Debugging
    dot.node('TestingDebugging', 'Testing & Debugging\n(James & Godfrey, Week 4)', **both_node_attr)
    dot.node('TestingDebugging_UseCase', 'Unit Testing (APIs), Integration Testing\n(Frontend/Backend)', **both_node_attr)

    ### Define the task flow and relationships ###
    # James's tasks and their subcategories
    dot.edge('Start', 'PaymentModuleUI')
    dot.edge('PaymentModuleUI', 'PaymentAPI')
    dot.edge('PaymentAPI', 'PaymentAPI_UseCase')

    dot.edge('Start', 'AuthUI')
    dot.edge('AuthUI', 'AuthUI_UseCase')
    dot.edge('AuthUI', 'PaymentAPI')

    dot.edge('Start', 'SubscriptionUI')
    dot.edge('SubscriptionUI', 'SubscriptionUI_UseCase')
    dot.edge('SubscriptionUI', 'DashboardUI')
    dot.edge('DashboardUI', 'DashboardUI_UseCase')

    dot.edge('DashboardUI', 'MapVisualization')
    dot.edge('MapVisualization', 'MapVisualization_UseCase')

    # Godfrey's tasks and their subcategories
    dot.edge('Start', 'AuthAPI')
    dot.edge('AuthAPI', 'AuthAPI_UseCase')

    dot.edge('Start', 'SubscriptionAPI')
    dot.edge('SubscriptionAPI', 'SubscriptionAPI_UseCase')

    dot.edge('Start', 'DataAPIs')
    dot.edge('DataAPIs', 'DataAPIs_UseCase')
    dot.edge('DataAPIs', 'DashboardUI')

    dot.edge('PredictionModels', 'PredictionModels_UseCase')
    dot.edge('FloodMonitoring', 'FloodMonitoring_UseCase')
    dot.edge('SMSAlerts', 'SMSAlerts_UseCase')

    # Linking James's UI tasks to Godfrey's backend tasks (dependencies)
    dot.edge('AuthAPI', 'AuthUI')  # Auth UI connects to Auth API
    dot.edge('SubscriptionAPI', 'SubscriptionUI')  # Subscription UI connects to API
    dot.edge('DataAPIs', 'DashboardUI')  # Dashboard UI fetches real-time data via APIs
    dot.edge('FloodMonitoring', 'MapVisualization')  # Flood data connects to map visualization

    # Shared tasks - testing and debugging
    dot.edge('PaymentAPI_UseCase', 'TestingDebugging')
    dot.edge('MapVisualization_UseCase', 'TestingDebugging')
    dot.edge('SMSAlerts_UseCase', 'TestingDebugging')
    dot.edge('TestingDebugging', 'End')

    # Save diagram to file
    dot.render('work_plan_flowchart', format='png', view=False)

    return "work_plan_flowchart.png"

# Generate the flowchart
diagram_path = generate_work_plan_flowchart()

print(f"Flowchart saved to {diagram_path}")
