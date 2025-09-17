import pandas as pd
from datetime import datetime, timedelta
from modules.database import DatabaseManager
from modules.analytics import EnergyAnalytics

class EnergyTradingSystem:
    def __init__(self):
        self.db = DatabaseManager()
        self.analytics = EnergyAnalytics()
        
        # Base energy prices ($/kWh)
        self.base_buy_price = 0.12
        self.base_sell_price = 0.08
        
        # Time-of-day pricing multipliers
        self.peak_hours = list(range(17, 22))  # 5 PM to 9 PM
        self.off_peak_hours = list(range(22, 24)) + list(range(0, 7))  # 10 PM to 6 AM
        
        self.peak_buy_multiplier = 1.8
        self.peak_sell_multiplier = 1.5
        self.off_peak_buy_multiplier = 0.7
        self.off_peak_sell_multiplier = 0.6
    
    def get_current_market_prices(self):
        """Get current energy market prices based on time of day"""
        current_hour = datetime.now().hour
        
        if current_hour in self.peak_hours:
            buy_price = self.base_buy_price * self.peak_buy_multiplier
            sell_price = self.base_sell_price * self.peak_sell_multiplier
            price_category = "Peak Hours"
        elif current_hour in self.off_peak_hours:
            buy_price = self.base_buy_price * self.off_peak_buy_multiplier
            sell_price = self.base_sell_price * self.off_peak_sell_multiplier
            price_category = "Off-Peak Hours"
        else:
            buy_price = self.base_buy_price
            sell_price = self.base_sell_price
            price_category = "Standard Hours"
        
        return {
            'buy_price': round(buy_price, 4),
            'sell_price': round(sell_price, 4),
            'category': price_category,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_hourly_price_forecast(self, hours=24):
        """Get price forecast for the next 24 hours"""
        forecast = []
        base_time = datetime.now()
        
        for i in range(hours):
            forecast_time = base_time + timedelta(hours=i)
            hour = forecast_time.hour
            
            if hour in self.peak_hours:
                buy_price = self.base_buy_price * self.peak_buy_multiplier
                sell_price = self.base_sell_price * self.peak_sell_multiplier
                category = "Peak"
            elif hour in self.off_peak_hours:
                buy_price = self.base_buy_price * self.off_peak_buy_multiplier
                sell_price = self.base_sell_price * self.off_peak_sell_multiplier
                category = "Off-Peak"
            else:
                buy_price = self.base_buy_price
                sell_price = self.base_sell_price
                category = "Standard"
            
            forecast.append({
                'hour': hour,
                'datetime': forecast_time.strftime('%Y-%m-%d %H:00'),
                'buy_price': round(buy_price, 4),
                'sell_price': round(sell_price, 4),
                'category': category
            })
        
        return forecast
    
    def calculate_energy_surplus_deficit(self, hours_back=1):
        """Calculate current energy surplus or deficit"""
        conn = self.db.get_connection()
        
        query = '''
            SELECT solar_generation, wind_generation, total_consumption, battery_storage
            FROM energy_data 
            ORDER BY timestamp DESC 
            LIMIT 1
        '''
        
        result = conn.execute(query).fetchone()
        conn.close()
        
        if not result:
            return {
                'status': 'no_data',
                'surplus_deficit': 0,
                'total_generation': 0,
                'consumption': 0,
                'battery_level': 0
            }
        
        solar_gen, wind_gen, consumption, battery = result
        total_generation = solar_gen + wind_gen
        net_balance = total_generation - consumption
        
        battery_capacity = 10000
        battery_percentage = (battery / battery_capacity) * 100
        
        # Determine trading recommendation
        if net_balance > 100 and battery_percentage > 80:
            status = 'surplus_sell_recommended'
        elif net_balance < -100 and battery_percentage < 30:
            status = 'deficit_buy_recommended'
        elif net_balance > 0:
            status = 'surplus_store'
        elif net_balance < 0:
            status = 'deficit_use_battery'
        else:
            status = 'balanced'
        
        return {
            'status': status,
            'surplus_deficit': round(net_balance, 2),
            'total_generation': round(total_generation, 2),
            'consumption': round(consumption, 2),
            'battery_level': round(battery, 2),
            'battery_percentage': round(battery_percentage, 1)
        }
    
    def generate_trading_recommendation(self):
        """Generate current trading recommendation"""
        current_prices = self.get_current_market_prices()
        energy_status = self.calculate_energy_surplus_deficit()
        
        recommendation = {
            'timestamp': datetime.now().isoformat(),
            'action': 'hold',
            'reason': 'Balanced energy consumption',
            'potential_amount_kwh': 0,
            'potential_value': 0,
            'current_buy_price': current_prices['buy_price'],
            'current_sell_price': current_prices['sell_price'],
            'price_category': current_prices['category'],
            'energy_status': energy_status
        }
        
        surplus_deficit = energy_status['surplus_deficit']
        battery_percentage = energy_status['battery_percentage']
        
        # Trading decision logic
        if energy_status['status'] == 'surplus_sell_recommended':
            # Surplus energy and battery is full - sell to grid
            sellable_amount = abs(surplus_deficit) / 1000  # Convert to kWh
            potential_earnings = sellable_amount * current_prices['sell_price']
            
            recommendation.update({
                'action': 'sell',
                'reason': f'High energy surplus ({surplus_deficit:.1f}W) and battery full ({battery_percentage:.1f}%)',
                'potential_amount_kwh': round(sellable_amount, 3),
                'potential_value': round(potential_earnings, 2)
            })
            
        elif energy_status['status'] == 'deficit_buy_recommended':
            # Energy deficit and battery low - buy from grid
            needed_amount = abs(surplus_deficit) / 1000  # Convert to kWh
            potential_cost = needed_amount * current_prices['buy_price']
            
            recommendation.update({
                'action': 'buy',
                'reason': f'Energy deficit ({surplus_deficit:.1f}W) and low battery ({battery_percentage:.1f}%)',
                'potential_amount_kwh': round(needed_amount, 3),
                'potential_value': round(potential_cost, 2)
            })
            
        elif current_prices['category'] == 'Off-Peak Hours' and battery_percentage < 50:
            # Off-peak hours with low battery - good time to buy
            recommendation.update({
                'action': 'buy_opportunistic',
                'reason': 'Off-peak pricing and low battery - good opportunity to buy cheap energy',
                'potential_amount_kwh': 2.0,  # Buy 2 kWh
                'potential_value': round(2.0 * current_prices['buy_price'], 2)
            })
            
        elif current_prices['category'] == 'Peak Hours' and battery_percentage > 70:
            # Peak hours with high battery - good time to sell
            recommendation.update({
                'action': 'sell_opportunistic',
                'reason': 'Peak pricing and high battery - good opportunity to sell at high prices',
                'potential_amount_kwh': 1.5,  # Sell 1.5 kWh
                'potential_value': round(1.5 * current_prices['sell_price'], 2)
            })
        
        return recommendation
    
    def execute_trade(self, trade_type, amount_kwh, price_per_kwh, user_id=1):
        """Execute a trade and record it in the database"""
        if trade_type not in ['buy', 'sell']:
            return {'success': False, 'message': 'Invalid trade type'}
        
        if amount_kwh <= 0:
            return {'success': False, 'message': 'Invalid amount'}
        
        total_amount = amount_kwh * price_per_kwh
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO energy_transactions 
                (transaction_type, energy_amount, price_per_kwh, total_amount, status)
                VALUES (?, ?, ?, ?, 'completed')
            ''', (trade_type, amount_kwh, price_per_kwh, total_amount))
            
            transaction_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'transaction_id': transaction_id,
                'message': f'Successfully {trade_type} {amount_kwh} kWh for ${total_amount:.2f}',
                'amount_kwh': amount_kwh,
                'total_cost': total_amount
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Trade execution failed: {str(e)}'}
    
    def get_trading_history(self, days=30):
        """Get trading history for the specified period"""
        conn = self.db.get_connection()
        
        query = '''
            SELECT timestamp, transaction_type, energy_amount, price_per_kwh, total_amount, status
            FROM energy_transactions 
            WHERE timestamp >= datetime('now', '-{} days')
            ORDER BY timestamp DESC
        '''.format(days)
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return {
                'transactions': [],
                'summary': {
                    'total_bought_kwh': 0,
                    'total_sold_kwh': 0,
                    'total_spent': 0,
                    'total_earned': 0,
                    'net_profit': 0
                }
            }
        
        # Calculate summary statistics
        buy_transactions = df[df['transaction_type'] == 'buy']
        sell_transactions = df[df['transaction_type'] == 'sell']
        
        total_bought = buy_transactions['energy_amount'].sum() if not buy_transactions.empty else 0
        total_sold = sell_transactions['energy_amount'].sum() if not sell_transactions.empty else 0
        total_spent = buy_transactions['total_amount'].sum() if not buy_transactions.empty else 0
        total_earned = sell_transactions['total_amount'].sum() if not sell_transactions.empty else 0
        net_profit = total_earned - total_spent
        
        summary = {
            'total_bought_kwh': round(total_bought, 2),
            'total_sold_kwh': round(total_sold, 2),
            'total_spent': round(total_spent, 2),
            'total_earned': round(total_earned, 2),
            'net_profit': round(net_profit, 2)
        }
        
        # Convert dataframe to list of dictionaries
        transactions = df.to_dict('records')
        
        return {
            'transactions': transactions,
            'summary': summary
        }
    
    def get_optimal_trading_schedule(self, hours=24):
        """Generate optimal trading schedule for the next 24 hours"""
        price_forecast = self.get_hourly_price_forecast(hours)
        
        # Get energy balance prediction (simplified)
        balance_data = self.analytics.calculate_energy_balance(1)
        if not balance_data:
            return []
        
        schedule = []
        current_battery = 50  # Assume 50% battery level as starting point
        battery_capacity = 10  # 10 kWh capacity
        
        for forecast in price_forecast:
            hour_recommendation = {
                'datetime': forecast['datetime'],
                'hour': forecast['hour'],
                'buy_price': forecast['buy_price'],
                'sell_price': forecast['sell_price'],
                'price_category': forecast['category'],
                'recommended_action': 'hold',
                'amount_kwh': 0,
                'estimated_value': 0,
                'battery_level_after': current_battery
            }
            
            # Simple trading logic based on price patterns
            if forecast['category'] == 'Off-Peak' and current_battery < 80:
                # Buy during off-peak if battery is not full
                buy_amount = min(2.0, (80 - current_battery) / 10 * battery_capacity)
                if buy_amount > 0.1:
                    hour_recommendation.update({
                        'recommended_action': 'buy',
                        'amount_kwh': round(buy_amount, 2),
                        'estimated_value': round(buy_amount * forecast['buy_price'], 2)
                    })
                    current_battery = min(100, current_battery + (buy_amount / battery_capacity) * 100)
            
            elif forecast['category'] == 'Peak' and current_battery > 30:
                # Sell during peak if battery has charge
                sell_amount = min(1.5, (current_battery - 30) / 100 * battery_capacity)
                if sell_amount > 0.1:
                    hour_recommendation.update({
                        'recommended_action': 'sell',
                        'amount_kwh': round(sell_amount, 2),
                        'estimated_value': round(sell_amount * forecast['sell_price'], 2)
                    })
                    current_battery = max(0, current_battery - (sell_amount / battery_capacity) * 100)
            
            hour_recommendation['battery_level_after'] = round(current_battery, 1)
            schedule.append(hour_recommendation)
        
        return schedule
    
    def get_market_analytics(self, days=7):
        """Get market analytics and insights"""
        history = self.get_trading_history(days)
        price_forecast = self.get_hourly_price_forecast(24)
        
        # Calculate average prices by time category
        peak_prices = [p for p in price_forecast if p['category'] == 'Peak']
        off_peak_prices = [p for p in price_forecast if p['category'] == 'Off-Peak']
        standard_prices = [p for p in price_forecast if p['category'] == 'Standard']
        
        avg_peak_buy = sum(p['buy_price'] for p in peak_prices) / len(peak_prices) if peak_prices else 0
        avg_peak_sell = sum(p['sell_price'] for p in peak_prices) / len(peak_prices) if peak_prices else 0
        avg_offpeak_buy = sum(p['buy_price'] for p in off_peak_prices) / len(off_peak_prices) if off_peak_prices else 0
        avg_offpeak_sell = sum(p['sell_price'] for p in off_peak_prices) / len(off_peak_prices) if off_peak_prices else 0
        
        # Calculate potential savings
        peak_offpeak_buy_diff = avg_peak_buy - avg_offpeak_buy if avg_offpeak_buy > 0 else 0
        peak_offpeak_sell_diff = avg_peak_sell - avg_offpeak_sell if avg_offpeak_sell > 0 else 0
        
        analytics = {
            'trading_summary': history['summary'],
            'price_analysis': {
                'avg_peak_buy_price': round(avg_peak_buy, 4),
                'avg_peak_sell_price': round(avg_peak_sell, 4),
                'avg_offpeak_buy_price': round(avg_offpeak_buy, 4),
                'avg_offpeak_sell_price': round(avg_offpeak_sell, 4),
                'peak_offpeak_buy_savings': round(peak_offpeak_buy_diff, 4),
                'peak_offpeak_sell_premium': round(peak_offpeak_sell_diff, 4)
            },
            'recommendations': [
                f"Buy during off-peak hours to save ${peak_offpeak_buy_diff:.3f}/kWh",
                f"Sell during peak hours to earn ${peak_offpeak_sell_diff:.3f}/kWh extra",
                "Maintain battery level between 30-80% for optimal trading flexibility"
            ]
        }
        
        return analytics