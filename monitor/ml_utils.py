import pandas as pd
from sklearn.neighbors import KNeighborsRegressor
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import cross_val_score
import logging

logger = logging.getLogger(__name__)

# Define a maximum possible MSE value for normalizing the accuracies
MAX_MSE_VALUE = 100  # Example normalization value for MSE

def train_models(water_levels):
    df = pd.DataFrame(water_levels)
    
    # Log columns for debugging
    logger.info(f"Columns in input data: {df.columns.tolist()}")
    
    # Standardize the water level column name to `level`
    if 'waterLevel' in df.columns:
        df.rename(columns={'waterLevel': 'level'}, inplace=True)
    elif 'level' not in df.columns:
        logger.error("Input data is missing both 'waterLevel' and 'level' columns.")
        return {}, {}, {}  # Return empty results if neither column exists
    
    # Check if 'timestamp' column exists
    if 'timestamp' not in df.columns:
        logger.error("Input data missing 'timestamp' column.")
        return {}, {}, {}  # Return empty results if timestamp is missing
    
    # Ensure timestamp is in ordinal form for the model
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.sort_values('timestamp', inplace=True)
    
    # Define features and target
    X = df[['timestamp', 'temperature', 'humidity']].copy()
    y = df['level']
    X['timestamp'] = X['timestamp'].apply(lambda x: x.toordinal())

    logger.info(f"Training data (features): {X.head()}")
    logger.info(f"Training data (target): {y.head()}")

    # Initialize models
    models = {
        'knn': KNeighborsRegressor(n_neighbors=3),
        'linear_regression': LinearRegression(),
        'decision_tree': DecisionTreeRegressor(),
        'random_forest': RandomForestRegressor(),
        'svr': SVR()
    }

    # Train and evaluate models
    accuracies = {}
    accuracy_percentages = {}
    for model_name, model in models.items():
        try:
            model.fit(X, y)
            # Cross-validation to evaluate model accuracy
            cv_scores = cross_val_score(model, X, y, cv=5, scoring='neg_mean_squared_error')
            mean_cv_score = -cv_scores.mean()  # Convert to positive MSE

            accuracies[model_name] = mean_cv_score
            accuracy_percentage = 100 - (mean_cv_score / MAX_MSE_VALUE * 100)
            accuracy_percentages[model_name] = accuracy_percentage

            logger.info(f"Model {model_name} trained with cross-validation MSE: {mean_cv_score}")
            logger.info(f"Model {model_name} accuracy percentage: {accuracy_percentage}")

        except Exception as e:
            logger.error(f"Exception during training model {model_name}: {str(e)}")

    return models, accuracies, accuracy_percentages


def predict(model, latest_data):
    try:
        latest_data_df = pd.DataFrame([latest_data])
        logger.info(f"Prediction input data: {latest_data_df}")
        prediction = model.predict(latest_data_df)[0]
        logger.info(f"Prediction result: {prediction}")
        return prediction
    except Exception as e:
        logger.error(f"Exception during prediction: {str(e)}")
        return None