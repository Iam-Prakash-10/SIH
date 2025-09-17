import sqlite3
from datetime import datetime
import hashlib
import os

class DatabaseManager:
    def __init__(self, db_name='renewable_energy.db'):
        self.db_path = db_name
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table for authentication
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Energy data table for real-time data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS energy_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                solar_generation REAL NOT NULL,
                wind_generation REAL NOT NULL,
                total_consumption REAL NOT NULL,
                battery_storage REAL NOT NULL,
                grid_import REAL DEFAULT 0,
                grid_export REAL DEFAULT 0
            )
        ''')
        
        # Solar specific data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS solar_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sun_intensity REAL NOT NULL,
                panel_temperature REAL NOT NULL,
                power_output REAL NOT NULL,
                efficiency REAL NOT NULL,
                panel_status TEXT DEFAULT 'OK'
            )
        ''')
        
        # Wind specific data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wind_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                wind_speed REAL NOT NULL,
                wind_direction REAL NOT NULL,
                power_output REAL NOT NULL,
                turbine_status TEXT DEFAULT 'OK'
            )
        ''')
        
        # Alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                resolved BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Energy transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS energy_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                transaction_type TEXT NOT NULL,
                energy_amount REAL NOT NULL,
                price_per_kwh REAL NOT NULL,
                total_amount REAL NOT NULL,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        # Daily statistics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE NOT NULL,
                total_solar_generation REAL NOT NULL,
                total_wind_generation REAL NOT NULL,
                total_consumption REAL NOT NULL,
                avg_solar_generation REAL NOT NULL,
                avg_wind_generation REAL NOT NULL,
                avg_consumption REAL NOT NULL,
                max_storage REAL NOT NULL,
                min_storage REAL NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_user(self, username, email, password):
        """Create a new user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Hash the password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
            ''', (username, email, password_hash))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def verify_user(self, username, password):
        """Verify user credentials"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute('''
            SELECT id, username FROM users
            WHERE username = ? AND password_hash = ?
        ''', (username, password_hash))
        
        user = cursor.fetchone()
        conn.close()
        return user
    
    def insert_energy_data(self, solar_gen, wind_gen, consumption, storage, grid_import=0, grid_export=0):
        """Insert real-time energy data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO energy_data 
            (solar_generation, wind_generation, total_consumption, battery_storage, grid_import, grid_export)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (solar_gen, wind_gen, consumption, storage, grid_import, grid_export))
        
        conn.commit()
        conn.close()
    
    def insert_solar_data(self, sun_intensity, panel_temp, power_output, efficiency, status='OK'):
        """Insert solar panel data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO solar_data 
            (sun_intensity, panel_temperature, power_output, efficiency, panel_status)
            VALUES (?, ?, ?, ?, ?)
        ''', (sun_intensity, panel_temp, power_output, efficiency, status))
        
        conn.commit()
        conn.close()
    
    def insert_wind_data(self, wind_speed, wind_direction, power_output, status='OK'):
        """Insert wind turbine data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO wind_data 
            (wind_speed, wind_direction, power_output, turbine_status)
            VALUES (?, ?, ?, ?)
        ''', (wind_speed, wind_direction, power_output, status))
        
        conn.commit()
        conn.close()
    
    def create_alert(self, alert_type, severity, message):
        """Create a new alert"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts (alert_type, severity, message)
            VALUES (?, ?, ?)
        ''', (alert_type, severity, message))
        
        conn.commit()
        conn.close()
    
    def get_latest_energy_data(self, limit=100):
        """Get latest energy data for graphs"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM energy_data 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        data = cursor.fetchall()
        conn.close()
        return data
    
    def get_latest_solar_data(self, limit=100):
        """Get latest solar data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM solar_data 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        data = cursor.fetchall()
        conn.close()
        return data
    
    def get_unresolved_alerts(self):
        """Get unresolved alerts"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM alerts 
            WHERE resolved = FALSE 
            ORDER BY timestamp DESC
        ''')
        
        alerts = cursor.fetchall()
        conn.close()
        return alerts