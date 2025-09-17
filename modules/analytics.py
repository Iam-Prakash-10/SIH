import torch
import torch.nn as nn
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from modules.database import DatabaseManager
import matplotlib.pyplot as plt
import io
import base64

class EnergyPredictor(nn.Module):
    """PyTorch neural network for energy prediction"""
    def __init__(self, input_size=4, hidden_size=64, output_size=3):
        super(EnergyPredictor, self).__init__()
        self.hidden1 = nn.Linear(input_size, hidden_size)
        self.hidden2 = nn.Linear(hidden_size, hidden_size)
        self.output = nn.Linear(hidden_size, output_size)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.2)
        
    def forward(self, x):
        x = self.relu(self.hidden1(x))
        x = self.dropout(x)
        x = self.relu(self.hidden2(x))
        x = self.dropout(x)
        x = self.output(x)
        return x

class EnergyAnalytics:
    def __init__(self):
        self.db = DatabaseManager()
        self.model = EnergyPredictor()
        self.is_trained = False
        
    def get_historical_data(self, days=30):
        """Fetch historical data from database"""
        conn = self.db.get_connection()
        
        # Get energy data
        energy_query = '''
            SELECT timestamp, solar_generation, wind_generation, total_consumption, battery_storage
            FROM energy_data 
            WHERE timestamp >= datetime('now', '-{} days')
            ORDER BY timestamp
        '''.format(days)
        
        energy_df = pd.read_sql_query(energy_query, conn)
        
        # Get solar data
        solar_query = '''
            SELECT timestamp, sun_intensity, panel_temperature, power_output, efficiency
            FROM solar_data 
            WHERE timestamp >= datetime('now', '-{} days')
            ORDER BY timestamp
        '''.format(days)
        
        solar_df = pd.read_sql_query(solar_query, conn)
        
        conn.close()
        return energy_df, solar_df
    
    def calculate_daily_statistics(self, days=7):
        """Calculate daily statistics for renewable energy generation"""
        energy_df, solar_df = self.get_historical_data(days)
        
        if energy_df.empty:
            return None
        
        # Convert timestamp to datetime
        energy_df['timestamp'] = pd.to_datetime(energy_df['timestamp'])
        energy_df['date'] = energy_df['timestamp'].dt.date
        
        # Calculate daily aggregates
        daily_stats = energy_df.groupby('date').agg({
            'solar_generation': ['sum', 'mean', 'max'],
            'wind_generation': ['sum', 'mean', 'max'],
            'total_consumption': ['sum', 'mean', 'max'],
            'battery_storage': ['min', 'max', 'mean']
        }).round(2)
        
        # Flatten column names
        daily_stats.columns = ['_'.join(col).strip() for col in daily_stats.columns]
        
        return daily_stats
    
    def calculate_averages(self, days=7):
        """Calculate average power generation, consumption, and storage"""
        energy_df, _ = self.get_historical_data(days)
        
        if energy_df.empty:
            return {
                'avg_solar_generation': 0,
                'avg_wind_generation': 0,
                'avg_consumption': 0,
                'avg_storage': 0
            }
        
        averages = {
            'avg_solar_generation': energy_df['solar_generation'].mean(),
            'avg_wind_generation': energy_df['wind_generation'].mean(),
            'avg_consumption': energy_df['total_consumption'].mean(),
            'avg_storage': energy_df['battery_storage'].mean()
        }
        
        return {k: round(v, 2) for k, v in averages.items()}
    
    def analyze_efficiency_trends(self):
        """Analyze solar panel efficiency trends"""
        _, solar_df = self.get_historical_data(30)
        
        if solar_df.empty:
            return None
        
        solar_df['timestamp'] = pd.to_datetime(solar_df['timestamp'])
        
        # Calculate efficiency trends
        efficiency_trend = solar_df.groupby(solar_df['timestamp'].dt.date)['efficiency'].mean()
        
        # Calculate correlation between sun intensity and power output
        correlation = solar_df['sun_intensity'].corr(solar_df['power_output'])
        
        # Identify potential issues
        low_efficiency_days = efficiency_trend[efficiency_trend < 0.15].index.tolist()
        
        return {
            'avg_efficiency': solar_df['efficiency'].mean(),
            'efficiency_trend': efficiency_trend.to_dict(),
            'sun_power_correlation': correlation,
            'low_efficiency_days': [str(day) for day in low_efficiency_days]
        }
    
    def prepare_training_data(self):
        """Prepare data for PyTorch model training"""
        energy_df, solar_df = self.get_historical_data(30)
        
        if energy_df.empty:
            return None, None
        
        # Merge datasets on timestamp
        energy_df['timestamp'] = pd.to_datetime(energy_df['timestamp'])
        solar_df['timestamp'] = pd.to_datetime(solar_df['timestamp'])
        
        merged_df = pd.merge(energy_df, solar_df, on='timestamp', how='inner')
        
        # Feature engineering
        merged_df['hour'] = merged_df['timestamp'].dt.hour
        merged_df['day_of_week'] = merged_df['timestamp'].dt.dayofweek
        merged_df['total_generation'] = merged_df['solar_generation'] + merged_df['wind_generation']
        
        # Select features for training
        feature_columns = ['hour', 'day_of_week', 'sun_intensity', 'panel_temperature']
        target_columns = ['solar_generation', 'wind_generation', 'total_consumption']
        
        # Create sequences for time series prediction
        features = merged_df[feature_columns].values
        targets = merged_df[target_columns].values
        
        # Normalize features
        features = (features - features.mean(axis=0)) / (features.std(axis=0) + 1e-8)
        targets = targets / 1000.0  # Scale down to kW
        
        return torch.FloatTensor(features), torch.FloatTensor(targets)
    
    def train_prediction_model(self, epochs=100):
        """Train PyTorch model for energy prediction"""
        X, y = self.prepare_training_data()
        
        if X is None or len(X) < 10:
            print("Insufficient data for training")
            return False
        
        # Split data
        split_idx = int(0.8 * len(X))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Training setup
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        
        # Training loop
        for epoch in range(epochs):
            self.model.train()
            optimizer.zero_grad()
            
            outputs = self.model(X_train)
            loss = criterion(outputs, y_train)
            
            loss.backward()
            optimizer.step()
            
            if (epoch + 1) % 20 == 0:
                print(f'Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}')
        
        # Evaluation
        self.model.eval()
        with torch.no_grad():
            test_outputs = self.model(X_test)
            test_loss = criterion(test_outputs, y_test)
            print(f'Test Loss: {test_loss.item():.4f}')
        
        self.is_trained = True
        return True
    
    def predict_next_hour(self):
        """Predict energy generation and consumption for the next hour"""
        if not self.is_trained:
            if not self.train_prediction_model():
                return None
        
        # Get current conditions
        now = datetime.now()
        hour = now.hour
        day_of_week = now.weekday()
        
        # Estimate current sun intensity and temperature
        if 6 <= hour <= 18:
            sun_intensity = 600 * np.sin(np.pi * (hour - 6) / 12)
        else:
            sun_intensity = 0
        
        panel_temp = 25 + (sun_intensity / 30)
        
        # Prepare input
        features = torch.FloatTensor([[hour, day_of_week, sun_intensity, panel_temp]])
        
        # Normalize (using simple normalization)
        features = features / torch.tensor([24.0, 7.0, 800.0, 60.0])
        
        # Predict
        self.model.eval()
        with torch.no_grad():
            prediction = self.model(features)
            prediction = prediction * 1000.0  # Scale back to watts
        
        return {
            'predicted_solar': float(prediction[0][0]),
            'predicted_wind': float(prediction[0][1]),
            'predicted_consumption': float(prediction[0][2])
        }
    
    def calculate_energy_balance(self, days=7):
        """Calculate energy balance for trading analysis"""
        energy_df, _ = self.get_historical_data(days)
        
        if energy_df.empty:
            return None
        
        # Calculate totals
        total_generation = energy_df['solar_generation'].sum() + energy_df['wind_generation'].sum()
        total_consumption = energy_df['total_consumption'].sum()
        net_balance = total_generation - total_consumption
        
        # Calculate daily patterns
        energy_df['timestamp'] = pd.to_datetime(energy_df['timestamp'])
        energy_df['hour'] = energy_df['timestamp'].dt.hour
        
        hourly_balance = energy_df.groupby('hour').agg({
            'solar_generation': 'sum',
            'wind_generation': 'sum',
            'total_consumption': 'sum'
        })
        
        hourly_balance['net_generation'] = (
            hourly_balance['solar_generation'] + 
            hourly_balance['wind_generation'] - 
            hourly_balance['total_consumption']
        )
        
        # Find best selling/buying hours
        surplus_hours = hourly_balance[hourly_balance['net_generation'] > 0].index.tolist()
        deficit_hours = hourly_balance[hourly_balance['net_generation'] < 0].index.tolist()
        
        return {
            'total_generation_kwh': round(total_generation / 1000, 2),
            'total_consumption_kwh': round(total_consumption / 1000, 2),
            'net_balance_kwh': round(net_balance / 1000, 2),
            'surplus_hours': surplus_hours,
            'deficit_hours': deficit_hours,
            'energy_self_sufficiency': round((total_generation / total_consumption * 100), 2) if total_consumption > 0 else 0
        }
    
    def generate_trading_recommendation(self):
        """Generate energy trading recommendations"""
        balance = self.calculate_energy_balance(7)
        prediction = self.predict_next_hour()
        
        if not balance or not prediction:
            return None
        
        # Current market prices (simulated)
        base_buy_price = 0.12  # $/kWh
        base_sell_price = 0.08  # $/kWh
        
        # Price varies by time of day (peak hours are more expensive)
        hour = datetime.now().hour
        if 17 <= hour <= 21:  # Peak hours
            buy_multiplier = 1.5
            sell_multiplier = 1.3
        elif 22 <= hour <= 6:  # Off-peak hours
            buy_multiplier = 0.8
            sell_multiplier = 0.7
        else:  # Standard hours
            buy_multiplier = 1.0
            sell_multiplier = 1.0
        
        current_buy_price = base_buy_price * buy_multiplier
        current_sell_price = base_sell_price * sell_multiplier
        
        # Calculate predicted surplus/deficit
        predicted_net = (prediction['predicted_solar'] + 
                        prediction['predicted_wind'] - 
                        prediction['predicted_consumption']) / 1000  # Convert to kWh
        
        recommendation = {
            'current_buy_price': round(current_buy_price, 3),
            'current_sell_price': round(current_sell_price, 3),
            'predicted_net_kwh': round(predicted_net, 2),
            'action': 'hold',
            'potential_earnings': 0,
            'potential_cost': 0
        }
        
        if predicted_net > 0.5:  # Surplus
            recommendation['action'] = 'sell'
            recommendation['potential_earnings'] = round(predicted_net * current_sell_price, 2)
        elif predicted_net < -0.5:  # Deficit
            recommendation['action'] = 'buy'
            recommendation['potential_cost'] = round(abs(predicted_net) * current_buy_price, 2)
        
        return recommendation
