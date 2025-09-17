from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
import threading
import time
import json

# Import our custom modules
from modules.database import DatabaseManager
from modules.auth import AuthManager, User
from modules.data_generator import EnergyDataGenerator
from modules.dashboard import DashboardManager
from modules.analytics import EnergyAnalytics
from modules.fault_detection import FaultDetectionSystem
from modules.energy_trading import EnergyTradingSystem

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'renewable_energy_secret_key_2024'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Initialize modules
db = DatabaseManager()
auth_manager = AuthManager()
data_generator = EnergyDataGenerator()
dashboard_manager = DashboardManager()
analytics = EnergyAnalytics()
fault_detection = FaultDetectionSystem()
trading_system = EnergyTradingSystem()

@login_manager.user_loader
def load_user(user_id):
    return auth_manager.get_user(user_id)

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = auth_manager.login_user_account(username, password)
        if user:
            flash('Successfully logged in!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if auth_manager.create_user(username, email, password):
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username or email already exists', 'error')
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    auth_manager.logout_user_account()
    flash('Successfully logged out!', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get current stats for dashboard cards
    stats = dashboard_manager.get_current_stats()
    return render_template('dashboard.html', stats=stats)

@app.route('/analytics')
@login_required
def analytics_page():
    # Calculate analytics data
    averages = analytics.calculate_averages(7)
    daily_stats = analytics.calculate_daily_statistics(7)
    efficiency_trends = analytics.analyze_efficiency_trends()
    energy_balance = analytics.calculate_energy_balance(7)
    
    return render_template('analytics.html', 
                         averages=averages,
                         daily_stats=daily_stats,
                         efficiency_trends=efficiency_trends,
                         energy_balance=energy_balance)

@app.route('/alerts')
@login_required
def alerts():
    # Get all unresolved alerts
    alerts_list = db.get_unresolved_alerts()
    fault_summary = fault_detection.get_fault_summary(7)
    
    return render_template('alerts.html', 
                         alerts=alerts_list,
                         fault_summary=fault_summary)

@app.route('/trading')
@login_required
def trading():
    # Get trading data
    current_prices = trading_system.get_current_market_prices()
    recommendation = trading_system.generate_trading_recommendation()
    trading_history = trading_system.get_trading_history(30)
    market_analytics = trading_system.get_market_analytics(7)
    
    return render_template('trading.html',
                         current_prices=current_prices,
                         recommendation=recommendation,
                         trading_history=trading_history,
                         market_analytics=market_analytics)

# API Routes for real-time data
@app.route('/api/dashboard/power_generation')
@login_required
def api_power_generation():
    graph_json = dashboard_manager.create_power_generation_graph()
    return jsonify({'graph': graph_json})

@app.route('/api/dashboard/battery_storage')
@login_required
def api_battery_storage():
    graph_json = dashboard_manager.create_battery_storage_graph()
    return jsonify({'graph': graph_json})

@app.route('/api/dashboard/sun_intensity_power')
@login_required
def api_sun_intensity_power():
    graph_json = dashboard_manager.create_sun_intensity_vs_power_graph()
    return jsonify({'graph': graph_json})

@app.route('/api/dashboard/daily_statistics')
@login_required
def api_daily_statistics():
    graph_json = dashboard_manager.create_daily_statistics_graph()
    return jsonify({'graph': graph_json})

@app.route('/api/dashboard/energy_balance')
@login_required
def api_energy_balance():
    graph_json = dashboard_manager.create_energy_balance_pie_chart()
    return jsonify({'graph': graph_json})

@app.route('/api/dashboard/solar_vs_wind')
@login_required
def api_solar_vs_wind():
    graph_json = dashboard_manager.create_solar_vs_wind_comparison_graph()
    return jsonify({'graph': graph_json})

@app.route('/api/dashboard/current_stats')
@login_required
def api_current_stats():
    stats = dashboard_manager.get_current_stats()
    return jsonify(stats)

@app.route('/api/fault_check')
@login_required
def api_fault_check():
    """Run fault detection and return results"""
    faults = fault_detection.run_comprehensive_check()
    return jsonify({'faults': faults})

@app.route('/api/trading/recommendation')
@login_required
def api_trading_recommendation():
    """Get current trading recommendation"""
    recommendation = trading_system.generate_trading_recommendation()
    return jsonify(recommendation)

@app.route('/api/trading/execute', methods=['POST'])
@login_required
def api_execute_trade():
    """Execute a trade"""
    data = request.get_json()
    
    trade_type = data.get('trade_type')
    amount_kwh = float(data.get('amount_kwh', 0))
    price_per_kwh = float(data.get('price_per_kwh', 0))
    
    result = trading_system.execute_trade(trade_type, amount_kwh, price_per_kwh)
    return jsonify(result)

@app.route('/api/trading/schedule')
@login_required
def api_trading_schedule():
    """Get optimal trading schedule for next 24 hours"""
    schedule = trading_system.get_optimal_trading_schedule(24)
    return jsonify(schedule)

@app.route('/api/analytics/prediction')
@login_required
def api_prediction():
    """Get energy predictions"""
    prediction = analytics.predict_next_hour()
    return jsonify(prediction if prediction else {'error': 'Insufficient data for prediction'})

# Background task to run fault detection periodically
def run_periodic_fault_detection():
    """Run fault detection every 5 minutes"""
    while True:
        try:
            fault_detection.run_comprehensive_check()
            time.sleep(300)  # 5 minutes
        except Exception as e:
            print(f"Error in periodic fault detection: {e}")
            time.sleep(300)

# Background task to generate data continuously
def run_data_generation():
    """Generate data every 30 seconds"""
    data_generator.start_continuous_generation(30)


# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', 
                         error_code=404,
                         error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html',
                         error_code=500,
                         error_message="Internal server error"), 500

# Initialize the application
def initialize_app():
    """Initialize the application with default data and background tasks"""
    # Create a test user if none exists
    try:
        if not auth_manager.db.verify_user('admin', 'admin123'):
            auth_manager.create_user('admin', 'admin@renewableenergy.com', 'admin123')
            print("Created default admin user: admin/admin123")
    except Exception as e:
        print(f"Error creating admin user: {e}")
    
    # Initialize the application by generating historical data and starting background tasks
    try:
        data_generator.generate_historical_data(2)  # Generate 2 days of historical data
        print("Generated initial historical data")
    except Exception as e:
        print(f"Error generating historical data: {e}")
    
    # Start background data generation
    data_thread = threading.Thread(target=run_data_generation)
    data_thread.daemon = True
    data_thread.start()
    print("Started continuous data generation")
    
    # Start periodic fault detection
    fault_thread = threading.Thread(target=run_periodic_fault_detection)
    fault_thread.daemon = True
    fault_thread.start()
    print("Started periodic fault detection")

# Initialize the application
initialize_app()

if __name__ == '__main__':
    print("Starting Renewable Energy Monitoring Application...")
    print("Default login: admin / admin123")
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    
    app.run(debug=debug, host='0.0.0.0', port=port, threaded=True)
