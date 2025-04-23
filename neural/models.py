# monitor/model.py
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping

# Data Preprocessing
def preprocess_data(water_levels):
    df = pd.DataFrame(water_levels)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.sort_values('timestamp', inplace=True)
    X = df[['timestamp', 'temperature', 'humidity']]
    y = df['level']
    X['timestamp'] = X['timestamp'].apply(lambda x: x.toordinal())

    # Normalize the features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return X_scaled, y, scaler

# Define Neural Network Model
def create_model(input_dim):
    model = Sequential()
    model.add(Dense(64, input_dim=input_dim, activation='relu'))
    model.add(Dropout(0.2))
    model.add(Dense(32, activation='relu'))
    model.add(Dense(1))  # Output layer for regression
    model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
    return model

# Train Neural Network
def train_neural_network(X, y):
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    model = create_model(X_train.shape[1])
    early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
    history = model.fit(X_train, y_train,
                        validation_data=(X_val, y_val),
                        epochs=100,
                        batch_size=32,
                        callbacks=[early_stopping],
                        verbose=1)
    return model, history

# Evaluate Model
def evaluate_model(model, X, y):
    y_pred = model.predict(X)
    mse = mean_squared_error(y, y_pred)
    return mse, y_pred

# Predict Latest Data
def predict_latest(model, latest_data, scaler):
    latest_data_scaled = scaler.transform([[
        latest_data['timestamp'],
        latest_data['temperature'],
        latest_data['humidity']
    ]])
    prediction = model.predict(latest_data_scaled)[0][0]  # Take the prediction value directly from model output
    return prediction