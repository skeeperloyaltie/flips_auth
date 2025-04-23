from graphviz import Digraph

def generate_dashboard_flow_diagram():
    # Create a Digraph object
    dot = Digraph('Dashboard Flow Diagram', comment='Subscription-based Dashboard Access')

    # Define styles for different types of nodes
    free_tier_node_attr = {'shape': 'rectangle', 'style': 'filled', 'fillcolor': '#87CEEB'}  # Light blue for Free tier
    corporate_tier_node_attr = {'shape': 'rectangle', 'style': 'filled', 'fillcolor': '#FFA500'}  # Orange for Corporate tier
    premium_tier_node_attr = {'shape': 'rectangle', 'style': 'filled', 'fillcolor': '#FFD700'}  # Gold for Premium tier
    process_node_attr = {'shape': 'rectangle'}  # Default style for processes
    decision_node_attr = {'shape': 'diamond'}
    start_end_node_attr = {'shape': 'oval', 'style': 'filled', 'fillcolor': '#90EE90'}  # Light green for start/end

    # Start and End shapes
    dot.node('Start', 'Start', **start_end_node_attr)
    dot.node('End', 'End', **start_end_node_attr)

    # Subscription-based Dashboard Access
    dot.node('Login', 'User Logs In', **process_node_attr)
    dot.node('CheckSub', 'Check Subscription Tier', **decision_node_attr)

    # Free Tier Dashboard
    dot.node('FreeDashboard', 'Free Tier Dashboard\nBasic Data Access', **free_tier_node_attr)
    dot.node('FreeWaterLevels', 'Water Levels\n(/monitoring/water-levels/)', **free_tier_node_attr)
    dot.node('FreeHumidity', 'Humidity\n(/monitoring/humidity/)', **free_tier_node_attr)
    dot.node('FreeTemperature', 'Temperature\n(/monitoring/temperature/)', **free_tier_node_attr)
    dot.node('FreeLinearReg', 'Run Linear Regression\nLimited Access', **free_tier_node_attr)
    dot.node('FreeRestricted', 'Restricted Access\n(No GIS or Advanced Models)', **process_node_attr)

    # Corporate Tier Dashboard
    dot.node('CorporateDashboard', 'Corporate Tier Dashboard\nAdvanced Data Access', **corporate_tier_node_attr)
    dot.node('CorporateWaterLevels', 'Water Levels\n(/monitoring/water-levels/)', **corporate_tier_node_attr)
    dot.node('CorporateHumidity', 'Humidity\n(/monitoring/humidity/)', **corporate_tier_node_attr)
    dot.node('CorporateTemperature', 'Temperature\n(/monitoring/temperature/)', **corporate_tier_node_attr)
    dot.node('CorpPrediction', 'Run Predictions\n(Linear, Polynomial, Time-Series)', **corporate_tier_node_attr)
    dot.node('CorpDecisionTree', 'Use Decision Trees\nFor Classification', **corporate_tier_node_attr)
    dot.node('CorpRestricted', 'Restricted Access\n(No Neural Networks or Geospatial)', **process_node_attr)

    # Premium Tier Dashboard
    dot.node('PremiumDashboard', 'Premium Tier Dashboard\nFull Data Access', **premium_tier_node_attr)
    dot.node('PremiumWaterLevels', 'Water Levels\n(/monitoring/water-levels/)', **premium_tier_node_attr)
    dot.node('PremiumHumidity', 'Humidity\n(/monitoring/humidity/)', **premium_tier_node_attr)
    dot.node('PremiumTemperature', 'Temperature\n(/monitoring/temperature/)', **premium_tier_node_attr)
    dot.node('PremiumPrediction', 'Run Predictions\n(ARIMA, Gradient Boosting)', **premium_tier_node_attr)
    dot.node('PremiumNeuralNetwork', 'Use Neural Networks\nComplex Data Predictions', **premium_tier_node_attr)
    dot.node('FloodMap', 'Flood Monitoring Map\n(/api/flood-monitoring/)', **premium_tier_node_attr)
    dot.node('GeospatialModel', 'Geospatial Models (GIS + GEE)', **premium_tier_node_attr)
    dot.node('SMSAlert', 'Send SMS Alert\n(AfricasTalking/AWS SNS)', **premium_tier_node_attr)

    # Authentication and Subscription Flow
    dot.edge('Start', 'Login')
    dot.edge('Login', 'CheckSub')

    # Free Tier Flow
    dot.edge('CheckSub', 'FreeDashboard', label='Free Tier')
    dot.edge('FreeDashboard', 'FreeWaterLevels')
    dot.edge('FreeWaterLevels', 'FreeHumidity')
    dot.edge('FreeHumidity', 'FreeTemperature')
    dot.edge('FreeTemperature', 'FreeLinearReg')
    dot.edge('FreeLinearReg', 'FreeRestricted')
    dot.edge('FreeRestricted', 'End')

    # Corporate Tier Flow
    dot.edge('CheckSub', 'CorporateDashboard', label='Corporate Tier')
    dot.edge('CorporateDashboard', 'CorporateWaterLevels')
    dot.edge('CorporateWaterLevels', 'CorporateHumidity')
    dot.edge('CorporateHumidity', 'CorporateTemperature')
    dot.edge('CorporateTemperature', 'CorpPrediction')
    dot.edge('CorpPrediction', 'CorpDecisionTree')
    dot.edge('CorpDecisionTree', 'CorpRestricted')
    dot.edge('CorpRestricted', 'End')

    # Premium Tier Flow
    dot.edge('CheckSub', 'PremiumDashboard', label='Premium Tier')
    dot.edge('PremiumDashboard', 'PremiumWaterLevels')
    dot.edge('PremiumWaterLevels', 'PremiumHumidity')
    dot.edge('PremiumHumidity', 'PremiumTemperature')
    dot.edge('PremiumTemperature', 'PremiumPrediction')
    dot.edge('PremiumPrediction', 'PremiumNeuralNetwork')
    dot.edge('PremiumNeuralNetwork', 'FloodMap')
    dot.edge('FloodMap', 'GeospatialModel')
    dot.edge('GeospatialModel', 'SMSAlert')
    dot.edge('SMSAlert', 'End')

    # Save diagram to file
    dot.render('dashboard_access_flow_diagram', format='png', view=False)

    return "dashboard_access_flow_diagram.png"

# Generate the flow diagram
diagram_path = generate_dashboard_flow_diagram()

print(f"Diagram saved to {diagram_path}")
