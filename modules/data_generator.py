import random
import math
import datetime
import threading
import time
from modules.database import DatabaseManager

class EnergyDataGenerator:
    def __init__(self):
        self.db = DatabaseManager()
        self.is_running = False
        self.thread = None
        
        # Base values for realistic data generation
        self.solar_base_capacity = 5000  # 5kW
        self.wind_base_capacity = 3000   # 3kW
        self.base_consumption = 2000     # 2kW average household consumption
        self.battery_capacity = 10000    # 10kWh battery
        self.current_battery_level = 5000  # Start at 50% capacity
        
    def get_time_factor(self):
        """Get time-based factors for solar and wind generation"""
        now = datetime.datetime.now()
        hour = now.hour
        
        # Solar generation based on sun position (0-1 factor)
        if 6 <= hour <= 18:
            # Peak solar at noon (12), declining towards morning and evening
            solar_factor = math.sin(math.pi * (hour - 6) / 12)
            solar_factor = max(0, solar_factor)
        else:
            solar_factor = 0
        
        # Wind factor - slightly higher at night and morning
        wind_factor = 0.3 + 0.4 * math.sin(2 * math.pi * hour / 24) + random.uniform(-0.2, 0.2)
        wind_factor = max(0.1, min(1.0, wind_factor))
        
        # Consumption pattern - higher during day and evening
        if 7 <= hour <= 22:
            consumption_factor = 0.8 + 0.4 * math.sin(math.pi * (hour - 7) / 15)
        else:
            consumption_factor = 0.4 + random.uniform(-0.1, 0.1)
        
        return solar_factor, wind_factor, consumption_factor
    
    def generate_solar_data(self):
        """Generate realistic solar panel data"""
        solar_factor, _, _ = self.get_time_factor()
        
        # Sun intensity (W/m²) - realistic values for solar irradiance
        if solar_factor > 0:
            base_intensity = 800 * solar_factor  # Peak of 800 W/m²
            sun_intensity = base_intensity + random.uniform(-100, 150)
            sun_intensity = max(0, sun_intensity)
        else:
            sun_intensity = 0
        
        # Panel temperature (°C) - affects efficiency
        ambient_temp = 25 + random.uniform(-5, 10)
        panel_temp = ambient_temp + (sun_intensity / 30)  # Panel heats up with sun
        
        # Solar panel efficiency (decreases with temperature)
        base_efficiency = 0.20  # 20% base efficiency
        temp_loss = max(0, (panel_temp - 25) * 0.004)  # 0.4% loss per degree above 25°C
        efficiency = base_efficiency - temp_loss + random.uniform(-0.01, 0.01)
        efficiency = max(0.1, min(0.25, efficiency))
        
        # Power output calculation
        if sun_intensity > 50:  # Minimum threshold for generation
            power_output = (sun_intensity / 1000) * self.solar_base_capacity * efficiency
            power_output = max(0, power_output + random.uniform(-100, 100))
        else:
            power_output = 0
        
        return sun_intensity, panel_temp, power_output, efficiency
    
    def generate_wind_data(self):
        """Generate realistic wind turbine data"""
        _, wind_factor, _ = self.get_time_factor()
        
        # Wind speed (m/s)
        base_wind_speed = 8 * wind_factor
        wind_speed = base_wind_speed + random.uniform(-2, 4)
        wind_speed = max(0, wind_speed)
        
        # Wind direction (degrees)
        wind_direction = random.uniform(0, 360)
        
        # Wind power generation (cubic relationship with wind speed)
        if wind_speed > 3:  # Cut-in speed
            if wind_speed > 25:  # Cut-out speed
                power_output = 0
            else:
                # Power curve approximation for small wind turbine
                normalized_speed = min(wind_speed / 12, 1)  # Rated speed at 12 m/s
                power_output = self.wind_base_capacity * (normalized_speed ** 3)
                power_output = max(0, power_output + random.uniform(-50, 50))
        else:
            power_output = 0
        
        return wind_speed, wind_direction, power_output
    
    def generate_consumption_data(self):
        """Generate realistic energy consumption data"""
        _, _, consumption_factor = self.get_time_factor()
        
        # Base consumption with random variations
        consumption = self.base_consumption * consumption_factor
        consumption = consumption + random.uniform(-200, 300)
        consumption = max(500, consumption)  # Minimum consumption
        
        return consumption
    
    def update_battery_storage(self, solar_power, wind_power, consumption):
        """Update battery storage based on generation and consumption"""
        total_generation = solar_power + wind_power
        net_power = total_generation - consumption
        
        # Update battery level
        self.current_battery_level += net_power * (1/60)  # Assuming 1-minute intervals
        
        # Battery constraints
        self.current_battery_level = max(0, min(self.battery_capacity, self.current_battery_level))
        
        # Grid import/export
        grid_import = 0
        grid_export = 0
        
        if net_power < 0 and self.current_battery_level <= 100:
            # Need to import from grid
            grid_import = abs(net_power)
        elif net_power > 0 and self.current_battery_level >= self.battery_capacity * 0.95:
            # Export to grid when battery is full
            grid_export = net_power
        
        return self.current_battery_level, grid_import, grid_export
    
    def check_solar_panel_fault(self, sun_intensity, power_output, efficiency):
        """Check for potential solar panel faults"""
        if sun_intensity > 400:  # Good sun conditions
            expected_power = (sun_intensity / 1000) * self.solar_base_capacity * 0.18  # Expected at 18% efficiency
            power_ratio = power_output / expected_power if expected_power > 0 else 0
            
            if power_ratio < 0.6:  # Less than 60% of expected power
                fault_message = f"Solar panel efficiency drop detected! Expected: {expected_power:.1f}W, Actual: {power_output:.1f}W"
                self.db.create_alert('solar_fault', 'high', fault_message)
                return True
        
        return False
    
    def generate_single_datapoint(self):
        """Generate a single complete data point"""
        # Generate individual component data
        sun_intensity, panel_temp, solar_power, efficiency = self.generate_solar_data()
        wind_speed, wind_direction, wind_power = self.generate_wind_data()
        consumption = self.generate_consumption_data()
        
        # Update battery and grid data
        battery_level, grid_import, grid_export = self.update_battery_storage(
            solar_power, wind_power, consumption
        )
        
        # Check for faults
        self.check_solar_panel_fault(sun_intensity, solar_power, efficiency)
        
        # Store data in database
        self.db.insert_energy_data(solar_power, wind_power, consumption, battery_level, grid_import, grid_export)
        self.db.insert_solar_data(sun_intensity, panel_temp, solar_power, efficiency)
        self.db.insert_wind_data(wind_speed, wind_direction, wind_power)
        
        return {
            'timestamp': datetime.datetime.now(),
            'solar_generation': solar_power,
            'wind_generation': wind_power,
            'total_consumption': consumption,
            'battery_storage': battery_level,
            'sun_intensity': sun_intensity,
            'panel_temperature': panel_temp,
            'wind_speed': wind_speed,
            'efficiency': efficiency
        }
    
    def start_continuous_generation(self, interval=30):
        """Start continuous data generation in background thread"""
        self.is_running = True
        
        def generate_loop():
            while self.is_running:
                try:
                    self.generate_single_datapoint()
                    time.sleep(interval)
                except Exception as e:
                    print(f"Error in data generation: {e}")
                    time.sleep(interval)
        
        self.thread = threading.Thread(target=generate_loop)
        self.thread.daemon = True
        self.thread.start()
    
    def stop_generation(self):
        """Stop continuous data generation"""
        self.is_running = False
        if self.thread:
            self.thread.join()
    
    def generate_historical_data(self, days=7):
        """Generate historical data for the past few days"""
        end_time = datetime.datetime.now()
        start_time = end_time - datetime.timedelta(days=days)
        
        current_time = start_time
        while current_time < end_time:
            # Temporarily set the time for realistic data
            original_time = datetime.datetime.now
            datetime.datetime.now = lambda: current_time
            
            try:
                self.generate_single_datapoint()
                current_time += datetime.timedelta(minutes=30)  # Data every 30 minutes
            except Exception as e:
                print(f"Error generating historical data: {e}")
                current_time += datetime.timedelta(minutes=30)
            finally:
                datetime.datetime.now = original_time