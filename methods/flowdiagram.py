from graphviz import Digraph

def generate_flow_diagram():
    # Create a Digraph object
    dot = Digraph('Flow Diagram', comment='Flood Monitoring System')

    # Define styles for different types of nodes
    auth_node_attr = {'shape': 'rectangle', 'style': 'filled', 'fillcolor': '#FFC107'}  # Yellow for authentication
    api_node_attr = {'shape': 'rectangle', 'style': 'filled', 'fillcolor': '#87CEEB'}   # Light blue for API calls
    process_node_attr = {'shape': 'rectangle'}  # Default style for processes
    decision_node_attr = {'shape': 'diamond'}
    start_end_node_attr = {'shape': 'oval', 'style': 'filled', 'fillcolor': '#90EE90'}  # Light green for start/end
    model_node_attr = {'shape': 'rectangle', 'style': 'filled', 'fillcolor': '#FFD700'}  # Gold for models

    # Start and End shapes
    dot.node('Start', 'Start', **start_end_node_attr)
    dot.node('End', 'End', **start_end_node_attr)

    # User Authentication and Login Flow
    dot.node('Login', 'User Enters Credentials', **process_node_attr)
    dot.node('ValidateLogin', 'Validate Login/Register\n(API: /api/login/ or /api/register/)', **decision_node_attr)
    dot.node('Token', 'Generate Token and Store', **auth_node_attr)
    dot.node('LoginFail', 'Invalid Credentials', **process_node_attr)

    # Fetch User and Subscription Info
    dot.node('Dashboard', 'Access Dashboard', **process_node_attr)
    dot.node('FetchUser', 'Fetch User Info\n(API: /api/user-info/)\n[Requires Auth]', **api_node_attr)
    dot.node('FetchSub', 'Fetch Subscription Status\n(API: /subscription/status/)\n[Requires Auth]', **api_node_attr)
    dot.node('NoSubscription', 'Not Subscribed, Prompt User', **process_node_attr)

    # Real-time Data Monitoring
    dot.node('RealTimeData', 'Fetch Real-time Data', **process_node_attr)
    dot.node('WaterLevels', 'Fetch Water Levels\n(API: /monitoring/water-levels/)\n[Requires Auth]', **api_node_attr)
    dot.node('Humidity', 'Fetch Humidity\n(API: /monitoring/humidity/)\n[Requires Auth]', **api_node_attr)
    dot.node('Temperature', 'Fetch Temperature\n(API: /monitoring/temperature/)\n[Requires Auth]', **api_node_attr)
    dot.node('DisplayData', 'Display Real-time Data on Dashboard\n(Chart.js)', **process_node_attr)

    # Prediction Models
    dot.node('PredictForm', 'Submit Prediction Form\n(Start/End Time)', **process_node_attr)
    
    # Add modeling processes (models)
    dot.node('LinearReg', 'Run Linear Regression\n(API: /api/predict/)\n[Requires Auth]', **model_node_attr)
    dot.node('PolyReg', 'Run Polynomial Regression', **model_node_attr)
    dot.node('TimeSeries', 'Run Time Series (ARIMA/SARIMA)', **model_node_attr)
    dot.node('DecisionTree', 'Run Decision Trees', **model_node_attr)
    dot.node('RandomForest', 'Run Random Forest', **model_node_attr)
    dot.node('SVM', 'Run Support Vector Machines (SVM)', **model_node_attr)
    dot.node('KNN', 'Run K-Nearest Neighbors (KNN)', **model_node_attr)
    dot.node('NeuralNet', 'Run Neural Networks', **model_node_attr)
    dot.node('Geospatial', 'Run Geospatial Models\n(GIS + GEE)', **model_node_attr)
    dot.node('Kalman', 'Run Kalman Filter', **model_node_attr)
    dot.node('ARIMAX', 'Run ARIMAX', **model_node_attr)

    dot.node('NoData', 'No Data Available for Prediction', **process_node_attr)
    dot.node('DisplayPrediction', 'Display Predicted Results', **process_node_attr)

    # Flood Monitoring Map
    dot.node('FloodMap', 'Display Flood Monitoring Map\n(Leaflet.js)', **process_node_attr)
    dot.node('FetchFloodData', 'Fetch Flood Data\n(API: /api/flood-monitoring/)\n[Requires Auth]', **api_node_attr)

    # External API Integration
    dot.node('SMSAlert', 'Send SMS Alert\n(AfricasTalking/AWS SNS)', **process_node_attr)

    # Authentication Flow
    dot.edge('Start', 'Login')
    dot.edge('Login', 'ValidateLogin')
    dot.edge('ValidateLogin', 'Token', label='Valid')
    dot.edge('ValidateLogin', 'LoginFail', label='Invalid')
    dot.edge('Token', 'Dashboard')
    dot.edge('LoginFail', 'End')

    # Fetch User and Subscription Info
    dot.edge('Dashboard', 'FetchUser')
    dot.edge('FetchUser', 'FetchSub')
    dot.edge('FetchSub', 'NoSubscription', label='Not Subscribed')
    dot.edge('FetchSub', 'RealTimeData', label='Subscribed')

    # Real-time Data Monitoring Flow
    dot.edge('RealTimeData', 'WaterLevels')
    dot.edge('WaterLevels', 'Humidity')
    dot.edge('Humidity', 'Temperature')
    dot.edge('Temperature', 'DisplayData')

    # Prediction Flow with various models
    dot.edge('DisplayData', 'PredictForm')
    dot.edge('PredictForm', 'LinearReg', label='Basic Prediction (Linear)')
    dot.edge('PredictForm', 'PolyReg', label='Advanced Nonlinear Prediction')
    dot.edge('PredictForm', 'TimeSeries', label='Time Series Forecasting')
    dot.edge('PredictForm', 'DecisionTree', label='Decision Trees')
    dot.edge('PredictForm', 'RandomForest', label='Random Forest')
    dot.edge('PredictForm', 'SVM', label='SVM')
    dot.edge('PredictForm', 'KNN', label='K-Nearest Neighbors')
    dot.edge('PredictForm', 'NeuralNet', label='Neural Networks')
    dot.edge('PredictForm', 'Geospatial', label='Geospatial Modeling')
    dot.edge('PredictForm', 'Kalman', label='Kalman Filter')
    dot.edge('PredictForm', 'ARIMAX', label='ARIMAX')

    dot.edge('LinearReg', 'DisplayPrediction', label='Data Available')
    dot.edge('PolyReg', 'DisplayPrediction', label='Data Available')
    dot.edge('TimeSeries', 'DisplayPrediction', label='Data Available')
    dot.edge('DecisionTree', 'DisplayPrediction', label='Data Available')
    dot.edge('RandomForest', 'DisplayPrediction', label='Data Available')
    dot.edge('SVM', 'DisplayPrediction', label='Data Available')
    dot.edge('KNN', 'DisplayPrediction', label='Data Available')
    dot.edge('NeuralNet', 'DisplayPrediction', label='Data Available')
    dot.edge('Geospatial', 'DisplayPrediction', label='Data Available')
    dot.edge('Kalman', 'DisplayPrediction', label='Data Available')
    dot.edge('ARIMAX', 'DisplayPrediction', label='Data Available')

    dot.edge('LinearReg', 'NoData', label='No Data')
    dot.edge('DisplayPrediction', 'End')

    # Flood Monitoring Map
    dot.edge('DisplayData', 'FloodMap')
    dot.edge('FloodMap', 'FetchFloodData')
    dot.edge('FetchFloodData', 'End')

    # SMS Alert Flow
    dot.edge('LinearReg', 'SMSAlert', label='Critical Flood Level')
    dot.edge('SMSAlert', 'End')

    # Highlight authentication requirements
    dot.edge('FetchUser', 'FetchSub', color='red', penwidth='2', label='Auth Required')
    dot.edge('FetchSub', 'RealTimeData', color='red', penwidth='2', label='Auth Required')
    dot.edge('RealTimeData', 'WaterLevels', color='red', penwidth='2')
    dot.edge('WaterLevels', 'Humidity', color='red', penwidth='2')
    dot.edge('Humidity', 'Temperature', color='red', penwidth='2')
    dot.edge('Temperature', 'DisplayData', color='red', penwidth='2')
    dot.edge('PredictForm', 'LinearReg', color='red', penwidth='2')
    dot.edge('FloodMap', 'FetchFloodData', color='red', penwidth='2')

    # Save diagram to file
    dot.render('flood_monitoring_flow_diagram_with_models', format='png', view=False)

    return "flood_monitoring_flow_diagram_with_models.png"

# Generate the flow diagram
diagram_path = generate_flow_diagram()

print(f"Diagram saved to {diagram_path}")
