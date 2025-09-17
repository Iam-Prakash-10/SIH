import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from modules.database import DatabaseManager

class FaultDetectionSystem:
    def __init__(self):
        self.db = DatabaseManager()
        
    def check_solar_panel_faults(self, hours_back=1):
        """Check for solar panel faults based on sun intensity vs power output"""
        conn = self.db.get_connection()
        
        # Get recent solar data
        query = '''
            SELECT timestamp, sun_intensity, power_output, efficiency, panel_temperature
            FROM solar_data 
            WHERE timestamp >= datetime('now', '-{} hours')
            ORDER BY timestamp DESC
        '''.format(hours_back)
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return []
        
        faults_detected = []
        
        for _, row in df.iterrows():
            sun_intensity = row['sun_intensity']
            power_output = row['power_output']
            efficiency = row['efficiency']
            panel_temp = row['panel_temperature']
            timestamp = row['timestamp']
            
            # Fault detection logic
            if sun_intensity > 300:  # Good sun conditions
                # Expected power calculation (simplified)
                expected_power = (sun_intensity / 1000) * 5000 * 0.18  # 5kW panel at 18% efficiency
                power_ratio = power_output / expected_power if expected_power > 0 else 0
                
                # Check for significant power drop
                if power_ratio < 0.6:  # Less than 60% of expected power
                    fault = {
                        'timestamp': timestamp,
                        'type': 'low_power_output',
                        'severity': 'high',
                        'message': f'Solar panel low power output detected. Expected: {expected_power:.1f}W, Actual: {power_output:.1f}W',
                        'sun_intensity': sun_intensity,
                        'power_output': power_output,
                        'expected_power': expected_power,
                        'efficiency_ratio': power_ratio
                    }
                    faults_detected.append(fault)
                    
                    # Create alert in database
                    self.db.create_alert('solar_fault', 'high', fault['message'])
            
            # Check for efficiency drops
            if efficiency < 0.12:  # Less than 12% efficiency
                fault = {
                    'timestamp': timestamp,
                    'type': 'low_efficiency',
                    'severity': 'medium',
                    'message': f'Solar panel efficiency drop detected. Current efficiency: {efficiency*100:.1f}%',
                    'efficiency': efficiency
                }
                faults_detected.append(fault)
                self.db.create_alert('efficiency_drop', 'medium', fault['message'])
            
            # Check for overheating
            if panel_temp > 80:  # Panel temperature too high
                fault = {
                    'timestamp': timestamp,
                    'type': 'overheating',
                    'severity': 'high',
                    'message': f'Solar panel overheating detected. Temperature: {panel_temp:.1f}°C',
                    'temperature': panel_temp
                }
                faults_detected.append(fault)
                self.db.create_alert('overheating', 'high', fault['message'])
        
        return faults_detected
    
    def check_wind_turbine_faults(self, hours_back=1):
        """Check for wind turbine faults"""
        conn = self.db.get_connection()
        
        query = '''
            SELECT timestamp, wind_speed, power_output
            FROM wind_data 
            WHERE timestamp >= datetime('now', '-{} hours')
            ORDER BY timestamp DESC
        '''.format(hours_back)
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return []
        
        faults_detected = []
        
        for _, row in df.iterrows():
            wind_speed = row['wind_speed']
            power_output = row['power_output']
            timestamp = row['timestamp']
            
            # Check for abnormal power output given wind speed
            if wind_speed > 5:  # Good wind conditions
                # Expected power for small wind turbine (simplified curve)
                expected_power = min(3000 * (wind_speed / 12) ** 3, 3000) if wind_speed < 25 else 0
                power_ratio = power_output / expected_power if expected_power > 0 else 0
                
                if power_ratio < 0.5 and expected_power > 100:  # Significant underperformance
                    fault = {
                        'timestamp': timestamp,
                        'type': 'wind_underperformance',
                        'severity': 'medium',
                        'message': f'Wind turbine underperforming. Wind speed: {wind_speed:.1f}m/s, Expected: {expected_power:.1f}W, Actual: {power_output:.1f}W',
                        'wind_speed': wind_speed,
                        'power_output': power_output,
                        'expected_power': expected_power
                    }
                    faults_detected.append(fault)
                    self.db.create_alert('wind_fault', 'medium', fault['message'])
        
        return faults_detected
    
    def check_battery_health(self, hours_back=24):
        """Check battery health and charging patterns"""
        conn = self.db.get_connection()
        
        query = '''
            SELECT timestamp, battery_storage, solar_generation, wind_generation, total_consumption
            FROM energy_data 
            WHERE timestamp >= datetime('now', '-{} hours')
            ORDER BY timestamp
        '''.format(hours_back)
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty or len(df) < 10:
            return []
        
        faults_detected = []
        battery_capacity = 10000  # 10kWh
        
        # Check for battery issues
        df['battery_percentage'] = (df['battery_storage'] / battery_capacity) * 100
        df['net_generation'] = df['solar_generation'] + df['wind_generation'] - df['total_consumption']
        
        # Check for charging issues
        charging_periods = df[df['net_generation'] > 500]  # Periods with surplus generation
        if not charging_periods.empty:
            # Check if battery is actually charging during surplus
            for i in range(len(charging_periods) - 1):
                current_battery = charging_periods.iloc[i]['battery_percentage']
                next_battery = charging_periods.iloc[i + 1]['battery_percentage']
                
                if next_battery <= current_battery and current_battery < 95:  # Battery not charging when it should
                    fault = {
                        'timestamp': charging_periods.iloc[i]['timestamp'],
                        'type': 'battery_charging_fault',
                        'severity': 'high',
                        'message': f'Battery not charging despite surplus generation. Battery level: {current_battery:.1f}%',
                        'battery_percentage': current_battery
                    }
                    faults_detected.append(fault)
                    self.db.create_alert('battery_fault', 'high', fault['message'])
                    break  # Only report once per check
        
        # Check for rapid discharge
        discharge_rate = df['battery_percentage'].diff()
        rapid_discharge = discharge_rate < -5  # More than 5% drop in one reading
        
        if rapid_discharge.any():
            rapid_discharge_times = df[rapid_discharge]['timestamp'].tolist()
            for timestamp in rapid_discharge_times[:3]:  # Limit to 3 alerts
                fault = {
                    'timestamp': timestamp,
                    'type': 'rapid_battery_discharge',
                    'severity': 'medium',
                    'message': 'Rapid battery discharge detected. Check for power leaks.',
                }
                faults_detected.append(fault)
                self.db.create_alert('battery_discharge', 'medium', fault['message'])
        
        # Check for low battery
        latest_battery = df.iloc[-1]['battery_percentage']
        if latest_battery < 10:
            fault = {
                'timestamp': df.iloc[-1]['timestamp'],
                'type': 'low_battery',
                'severity': 'high',
                'message': f'Critical battery level: {latest_battery:.1f}%. Immediate action required.',
                'battery_percentage': latest_battery
            }
            faults_detected.append(fault)
            self.db.create_alert('low_battery', 'high', fault['message'])
        
        return faults_detected
    
    def check_system_connectivity(self):
        """Check if all systems are reporting data"""
        faults_detected = []
        current_time = datetime.now()
        
        # Check last data timestamps
        latest_energy = self.db.get_latest_energy_data(1)
        latest_solar = self.db.get_latest_solar_data(1)
        
        if not latest_energy:
            fault = {
                'timestamp': current_time.isoformat(),
                'type': 'no_energy_data',
                'severity': 'critical',
                'message': 'No energy data received. Check system connectivity.'
            }
            faults_detected.append(fault)
            self.db.create_alert('connectivity', 'critical', fault['message'])
        else:
            # Check if data is recent (within last 5 minutes)
            try:
                last_timestamp = datetime.fromisoformat(latest_energy[0][1].replace('Z', '+00:00')) if latest_energy[0][1].endswith('Z') else datetime.fromisoformat(latest_energy[0][1])
                time_diff = (current_time - last_timestamp).total_seconds() / 60  # minutes
                
                if time_diff > 5:  # More than 5 minutes old
                    fault = {
                        'timestamp': current_time.isoformat(),
                        'type': 'stale_data',
                        'severity': 'medium',
                        'message': f'Energy data is stale. Last update: {time_diff:.1f} minutes ago.'
                    }
                    faults_detected.append(fault)
                    self.db.create_alert('stale_data', 'medium', fault['message'])
            except:
                pass  # Skip timestamp parsing errors
        
        if not latest_solar:
            fault = {
                'timestamp': current_time.isoformat(),
                'type': 'no_solar_data',
                'severity': 'high',
                'message': 'No solar data received. Check solar monitoring system.'
            }
            faults_detected.append(fault)
            self.db.create_alert('solar_connectivity', 'high', fault['message'])
        
        return faults_detected
    
    def run_comprehensive_check(self):
        """Run all fault detection checks"""
        all_faults = []
        
        try:
            # Check solar panels
            solar_faults = self.check_solar_panel_faults(1)
            all_faults.extend(solar_faults)
            
            # Check wind turbine
            wind_faults = self.check_wind_turbine_faults(1)
            all_faults.extend(wind_faults)
            
            # Check battery health
            battery_faults = self.check_battery_health(24)
            all_faults.extend(battery_faults)
            
            # Check system connectivity
            connectivity_faults = self.check_system_connectivity()
            all_faults.extend(connectivity_faults)
            
        except Exception as e:
            error_fault = {
                'timestamp': datetime.now().isoformat(),
                'type': 'system_error',
                'severity': 'critical',
                'message': f'Fault detection system error: {str(e)}'
            }
            all_faults.append(error_fault)
            self.db.create_alert('system_error', 'critical', error_fault['message'])
        
        return all_faults
    
    def get_fault_summary(self, days=7):
        """Get a summary of faults over the specified period"""
        conn = self.db.get_connection()
        
        query = '''
            SELECT alert_type, severity, COUNT(*) as count
            FROM alerts 
            WHERE timestamp >= datetime('now', '-{} days')
            GROUP BY alert_type, severity
            ORDER BY count DESC
        '''.format(days)
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return {'total_faults': 0, 'by_type': {}, 'by_severity': {}}
        
        # Group by type and severity
        by_type = df.groupby('alert_type')['count'].sum().to_dict()
        by_severity = df.groupby('severity')['count'].sum().to_dict()
        
        return {
            'total_faults': df['count'].sum(),
            'by_type': by_type,
            'by_severity': by_severity
        }
