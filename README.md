# Renewable Energy Monitoring System

A comprehensive IoT-based renewable energy monitoring and trading platform built with Flask, PyTorch, and modern web technologies.

## Features

### 🌞 **Real-time Monitoring**
- Live solar panel power generation tracking
- Wind turbine energy production monitoring
- Battery storage level visualization
- Energy consumption analysis
- Sun intensity vs power generation correlation

### 📊 **Advanced Analytics**
- PyTorch-powered AI predictions for energy generation
- Historical data analysis with pandas and NumPy
- Daily, weekly, and monthly energy statistics
- Efficiency trend analysis
- Energy balance calculations

### ⚠️ **Intelligent Fault Detection**
- Automatic solar panel fault detection
- Wind turbine performance monitoring
- Battery health analysis
- System connectivity checks
- Real-time alert notifications

### 💰 **Energy Trading System**
- Dynamic pricing based on peak/off-peak hours
- AI-powered trading recommendations
- Energy surplus/deficit calculations
- Transaction history tracking
- Market analytics and insights

### 🔐 **User Authentication**
- Secure user registration and login
- Session management
- Multi-user support

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Application
```bash
python app.py
```

### Step 3: Access the Application
Open your browser and navigate to: `http://localhost:5000`

**Default Login Credentials:**
- Username: `admin`
- Password: `admin123`

## Technology Stack

### Backend
- **Flask** - Web framework
- **PyTorch** - AI/ML predictions
- **pandas** - Data analysis
- **NumPy** - Numerical computing
- **SQLite** - Database
- **Plotly** - Interactive graphs

### Frontend
- **Bootstrap 5** - UI framework
- **JavaScript/jQuery** - Dynamic interactions
- **Font Awesome** - Icons
- **Plotly.js** - Real-time charts

## System Architecture

### Data Generation
The system includes a realistic data generator that simulates:
- Solar power generation based on time of day and sun intensity
- Wind power generation with realistic wind speed patterns
- Energy consumption with daily usage patterns
- Battery storage simulation with charging/discharging cycles

### Machine Learning
- PyTorch neural network for energy prediction
- Real-time analysis of energy patterns
- Anomaly detection for fault identification

### Real-time Updates
- Background threads for continuous data generation
- Automatic fault detection every 5 minutes
- Real-time graph updates every 30 seconds

## Key Features Explained

### 1. Dashboard
- **Real-time Statistics**: Current solar, wind, consumption, and battery levels
- **Power Generation Graph**: Live comparison of generation vs consumption
- **Sun Intensity Analysis**: Correlation between solar irradiance and power output
- **Battery Monitoring**: Storage level with charging/discharging trends
- **Daily Statistics**: Historical energy data for the past 7 days

### 2. Analytics
- **7-day Averages**: Statistical analysis of energy patterns
- **AI Predictions**: Next-hour energy generation and consumption forecasts
- **Efficiency Analysis**: Solar panel performance metrics
- **Energy Balance**: Self-sufficiency calculations and surplus/deficit analysis

### 3. Fault Detection
- **Solar Panel Monitoring**: Detects efficiency drops and overheating
- **Wind Turbine Analysis**: Performance monitoring and fault detection
- **Battery Health**: Charging issues and rapid discharge detection
- **System Connectivity**: Data freshness and communication checks

### 4. Energy Trading
- **Dynamic Pricing**: Peak, off-peak, and standard hour pricing
- **Trading Recommendations**: AI-powered buy/sell suggestions
- **Transaction Management**: Execute trades and track history
- **Market Analytics**: Price trends and optimization strategies

## Data Models

### Energy Data
- Solar generation (Watts)
- Wind generation (Watts)
- Total consumption (Watts)
- Battery storage (Wh)
- Grid import/export (Watts)

### Solar Data
- Sun intensity (W/m²)
- Panel temperature (°C)
- Power output (Watts)
- Efficiency (%)
- Panel status

### Wind Data
- Wind speed (m/s)
- Wind direction (degrees)
- Power output (Watts)
- Turbine status

### Alerts
- Alert type and severity
- Timestamp and message
- Resolution status

### Transactions
- Buy/sell transactions
- Energy amount (kWh)
- Price per kWh
- Total amount ($)

## Configuration

### Database
The system uses SQLite for data storage. The database is automatically initialized on first run.

### Data Generation
- Historical data: 2 days generated on startup
- Real-time data: Updates every 30 seconds
- Fault detection: Runs every 5 minutes

### Trading System
- Base buy price: $0.12/kWh
- Base sell price: $0.08/kWh
- Peak hours: 5 PM - 9 PM (1.8x multiplier)
- Off-peak hours: 10 PM - 6 AM (0.7x multiplier)

## API Endpoints

### Dashboard APIs
- `GET /api/dashboard/power_generation` - Power generation graph data
- `GET /api/dashboard/battery_storage` - Battery storage graph data
- `GET /api/dashboard/sun_intensity_power` - Sun intensity vs power graph
- `GET /api/dashboard/current_stats` - Real-time statistics

### Analytics APIs
- `GET /api/analytics/prediction` - AI energy predictions

### Trading APIs
- `GET /api/trading/recommendation` - Current trading recommendation
- `POST /api/trading/execute` - Execute a trade
- `GET /api/trading/schedule` - Optimal trading schedule

### Fault Detection APIs
- `GET /api/fault_check` - Run comprehensive fault check

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please create an issue in the repository or contact the development team.

---

**Built with ❤️ for sustainable energy monitoring and IoT applications**