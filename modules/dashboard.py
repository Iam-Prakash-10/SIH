import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import json
from datetime import datetime, timedelta
from modules.database import DatabaseManager
from modules.analytics import EnergyAnalytics

class DashboardManager:
    def __init__(self):
        self.db = DatabaseManager()
        self.analytics = EnergyAnalytics()
    
    def get_real_time_data(self, hours=24):
        """Get real-time energy data for the specified number of hours"""
        conn = self.db.get_connection()
        
        query = '''
            SELECT timestamp, solar_generation, wind_generation, total_consumption, battery_storage
            FROM energy_data 
            WHERE timestamp >= datetime('now', '-{} hours')
            ORDER BY timestamp DESC
            LIMIT 100
        '''.format(hours)
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            # Return empty structure if no data
            return pd.DataFrame(columns=['timestamp', 'solar_generation', 'wind_generation', 'total_consumption', 'battery_storage'])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df.sort_values('timestamp')
    
    def get_solar_intensity_data(self, hours=24):
        """Get solar intensity and power generation data"""
        conn = self.db.get_connection()
        
        query = '''
            SELECT timestamp, sun_intensity, power_output, efficiency, panel_temperature
            FROM solar_data 
            WHERE timestamp >= datetime('now', '-{} hours')
            ORDER BY timestamp DESC
            LIMIT 100
        '''.format(hours)
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return pd.DataFrame(columns=['timestamp', 'sun_intensity', 'power_output', 'efficiency', 'panel_temperature'])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df.sort_values('timestamp')
    
    def create_power_generation_graph(self):
        """Create real-time power generation graph"""
        df = self.get_real_time_data(24)
        
        if df.empty:
            # Create empty graph if no data
            fig = go.Figure()
            fig.add_annotation(
                text="No data available yet. Please wait for data generation to start.",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=16
            )
            fig.update_layout(
                title="Real-time Power Generation",
                xaxis_title="Time",
                yaxis_title="Power (Watts)",
                height=400
            )
            return fig.to_json()
        
        fig = go.Figure()
        
        # Solar generation
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['solar_generation'],
            mode='lines',
            name='Solar Generation',
            line=dict(color='orange', width=2),
            fill='tonexty' if len(fig.data) > 0 else 'tozeroy'
        ))
        
        # Wind generation
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['wind_generation'],
            mode='lines',
            name='Wind Generation',
            line=dict(color='blue', width=2),
            fill='tonexty'
        ))
        
        # Total consumption
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['total_consumption'],
            mode='lines',
            name='Total Consumption',
            line=dict(color='red', width=2, dash='dash')
        ))
        
        fig.update_layout(
            title="Real-time Power Generation vs Consumption",
            xaxis_title="Time",
            yaxis_title="Power (Watts)",
            hovermode='x unified',
            height=400,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        return fig.to_json()
    
    def create_battery_storage_graph(self):
        """Create battery storage level graph"""
        df = self.get_real_time_data(24)
        
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available yet.",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=16
            )
            fig.update_layout(
                title="Battery Storage Level",
                xaxis_title="Time",
                yaxis_title="Storage (Wh)",
                height=300
            )
            return fig.to_json()
        
        # Calculate battery percentage
        battery_capacity = 10000  # 10kWh capacity
        df['battery_percentage'] = (df['battery_storage'] / battery_capacity) * 100
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['battery_percentage'],
            mode='lines',
            name='Battery Level',
            line=dict(color='green', width=3),
            fill='tozeroy'
        ))
        
        # Add warning lines
        fig.add_hline(y=20, line_dash="dash", line_color="red", annotation_text="Low Battery (20%)")
        fig.add_hline(y=80, line_dash="dash", line_color="orange", annotation_text="High Battery (80%)")
        
        fig.update_layout(
            title="Battery Storage Level",
            xaxis_title="Time",
            yaxis_title="Battery Level (%)",
            yaxis=dict(range=[0, 100]),
            height=300,
            showlegend=False
        )
        
        return fig.to_json()
    
    def create_sun_intensity_vs_power_graph(self):
        """Create enhanced sun intensity vs power generation graph with correlation analysis"""
        df = self.get_solar_intensity_data(24)
        
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No solar data available yet.",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=16
            )
            fig.update_layout(
                title="Sun Intensity vs Solar Power Generation",
                xaxis_title="Time",
                yaxis_title="Intensity (W/m²) / Power (W)",
                height=450
            )
            return fig.to_json()
        
        # Calculate correlation coefficient
        correlation = df['sun_intensity'].corr(df['power_output']) if len(df) > 1 else 0
        
        # Calculate efficiency metrics
        df['theoretical_max'] = df['sun_intensity'] * 0.2  # Assuming 20% max efficiency
        df['efficiency_percentage'] = (df['power_output'] / df['theoretical_max'] * 100).clip(0, 100)
        
        # Create subplot with secondary y-axis
        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.7, 0.3],
            specs=[[{"secondary_y": True}], [{"secondary_y": False}]],
            subplot_titles=(
                f"Sun Intensity vs Solar Power (Correlation: {correlation:.3f})",
                "Real-time Solar Panel Efficiency"
            ),
            vertical_spacing=0.12
        )
        
        # Sun intensity area chart
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['sun_intensity'],
                mode='lines',
                name='Sun Intensity',
                line=dict(color='#FFD700', width=2),
                fill='tozeroy',
                fillcolor='rgba(255, 215, 0, 0.2)',
                hovertemplate='<b>Sun Intensity</b><br>%{y:.1f} W/m²<br>%{x}<extra></extra>'
            ),
            secondary_y=False, row=1, col=1
        )
        
        # Power output line with markers
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['power_output'],
                mode='lines+markers',
                name='Solar Power Output',
                line=dict(color='#FF8C00', width=3),
                marker=dict(size=4, color='#FF8C00'),
                hovertemplate='<b>Power Output</b><br>%{y:.1f} W<br>%{x}<extra></extra>'
            ),
            secondary_y=True, row=1, col=1
        )
        
        # Theoretical maximum power (reference line)
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['theoretical_max'],
                mode='lines',
                name='Theoretical Max (20% eff.)',
                line=dict(color='red', width=1, dash='dash'),
                opacity=0.6,
                hovertemplate='<b>Theoretical Max</b><br>%{y:.1f} W<br>%{x}<extra></extra>'
            ),
            secondary_y=True, row=1, col=1
        )
        
        # Efficiency percentage chart
        efficiency_colors = ['#FF4444' if eff < 10 else '#FFB347' if eff < 15 else '#90EE90' for eff in df['efficiency_percentage']]
        fig.add_trace(
            go.Bar(
                x=df['timestamp'],
                y=df['efficiency_percentage'],
                name='Panel Efficiency',
                marker=dict(color=efficiency_colors, opacity=0.8),
                hovertemplate='<b>Efficiency</b><br>%{y:.1f}%<br>%{x}<extra></extra>'
            ),
            row=2, col=1
        )
        
        # Update axis labels and styling
        fig.update_xaxes(title_text="Time", row=1, col=1)
        fig.update_xaxes(title_text="Time", row=2, col=1)
        fig.update_yaxes(title_text="Sun Intensity (W/m²)", secondary_y=False, row=1, col=1)
        fig.update_yaxes(title_text="Power Output (W)", secondary_y=True, row=1, col=1)
        fig.update_yaxes(title_text="Efficiency (%)", row=2, col=1, range=[0, 25])
        
        # Add efficiency threshold lines
        fig.add_hline(y=15, line_dash="dash", line_color="green", 
                     annotation_text="Good Efficiency (15%)", row=2, col=1)
        fig.add_hline(y=10, line_dash="dash", line_color="orange", 
                     annotation_text="Fair Efficiency (10%)", row=2, col=1)
        
        # Calculate and add performance metrics
        avg_efficiency = df['efficiency_percentage'].mean()
        max_power = df['power_output'].max()
        peak_intensity = df['sun_intensity'].max()
        
        # Add performance annotation
        performance_text = f"📊 Performance Metrics:<br>" \
                          f"Average Efficiency: {avg_efficiency:.1f}%<br>" \
                          f"Peak Power: {max_power:.1f}W<br>" \
                          f"Peak Intensity: {peak_intensity:.1f}W/m²"
        
        fig.add_annotation(
            text=performance_text,
            xref="paper", yref="paper",
            x=0.02, y=0.98,
            xanchor='left', yanchor='top',
            showarrow=False,
            font=dict(size=10, color="white"),
            bgcolor="rgba(0,0,0,0.7)",
            bordercolor="white",
            borderwidth=1,
            row=1, col=1
        )
        
        fig.update_layout(
            title=dict(
                text="<b>Sun Intensity vs Solar Power Generation - Real-time Analysis</b>",
                x=0.5,
                font=dict(size=16)
            ),
            hovermode='x unified',
            height=450,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5
            ),
            plot_bgcolor='rgba(248,249,250,0.8)',
            paper_bgcolor='white'
        )
        
        return fig.to_json()
    
    def create_daily_statistics_graph(self):
        """Create perfectly spaced and styled daily statistics comparison graph"""
        daily_stats = self.analytics.calculate_daily_statistics(7)
        
        if daily_stats is None or daily_stats.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="Insufficient data for daily statistics. Please wait for more data.",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=16
            )
            fig.update_layout(
                title="Daily Energy Statistics (Last 7 Days)",
                height=500
            )
            return fig.to_json()
        
        # Format dates for better display
        dates = [str(date)[-5:] for date in daily_stats.index]  # Show only MM-DD
        full_dates = [str(date) for date in daily_stats.index]  # Keep full dates for hover
        
        # Convert to kWh with better precision
        solar_kwh = daily_stats['solar_generation_sum'] / 1000
        wind_kwh = daily_stats['wind_generation_sum'] / 1000
        consumption_kwh = daily_stats['total_consumption_sum'] / 1000
        total_generation = solar_kwh + wind_kwh
        
        # Calculate daily energy balance
        energy_balance = total_generation - consumption_kwh
        
        # Calculate efficiency and trends
        solar_trend = solar_kwh.pct_change().mean() * 100 if len(solar_kwh) > 1 else 0
        wind_trend = wind_kwh.pct_change().mean() * 100 if len(wind_kwh) > 1 else 0
        consumption_trend = consumption_kwh.pct_change().mean() * 100 if len(consumption_kwh) > 1 else 0
        
        # Create perfectly spaced subplots
        fig = make_subplots(
            rows=3, cols=3,
            row_heights=[0.5, 0.25, 0.25],
            column_widths=[0.6, 0.2, 0.2],
            specs=[
                [{"colspan": 3, "type": "scatter"}, None, None],
                [{"type": "bar"}, {"type": "indicator"}, {"type": "indicator"}],
                [{"type": "bar"}, {"type": "bar"}, {"type": "bar"}]
            ],
            subplot_titles=(
                "Daily Energy Production vs Consumption - Last 7 Days",
                "", "",
                "Energy Balance",
                "Weekly Balance",
                "Generation Ratio",
                "Solar Trend",
                "Wind Trend", 
                "Consumption Trend"
            ),
            vertical_spacing=0.08,
            horizontal_spacing=0.05
        )
        
        # Main chart - Daily generation and consumption (Row 1)
        fig.add_trace(
            go.Bar(
                x=dates,
                y=solar_kwh,
                name='Solar Generation',
                marker=dict(
                    color='#FFA500',
                    opacity=0.8,
                    line=dict(color='#FF8C00', width=1.5),
                    pattern=dict(shape="", solidity=0.8)
                ),
                text=[f'{val:.1f}' for val in solar_kwh],
                textposition='inside',
                textfont=dict(color='white', size=10, family='Arial Black'),
                hovertemplate='<b>Solar Generation</b><br>%{y:.2f} kWh<br>Date: %{customdata}<extra></extra>',
                customdata=full_dates,
                width=0.25
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=dates,
                y=wind_kwh,
                name='Wind Generation',
                marker=dict(
                    color='#4169E1',
                    opacity=0.8,
                    line=dict(color='#0000CD', width=1.5),
                    pattern=dict(shape="", solidity=0.8)
                ),
                text=[f'{val:.1f}' for val in wind_kwh],
                textposition='inside',
                textfont=dict(color='white', size=10, family='Arial Black'),
                hovertemplate='<b>Wind Generation</b><br>%{y:.2f} kWh<br>Date: %{customdata}<extra></extra>',
                customdata=full_dates,
                width=0.25
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=consumption_kwh,
                mode='lines+markers',
                name='Total Consumption',
                line=dict(color='#DC143C', width=4, dash='solid'),
                marker=dict(
                    size=12,
                    color='#FFFFFF',
                    symbol='diamond',
                    line=dict(color='#DC143C', width=3)
                ),
                hovertemplate='<b>Total Consumption</b><br>%{y:.2f} kWh<br>Date: %{customdata}<extra></extra>',
                customdata=full_dates
            ),
            row=1, col=1
        )
        
        # Energy balance bars (Row 2, Col 1)
        balance_colors = ['#32CD32' if bal > 0 else '#FF6347' for bal in energy_balance]
        fig.add_trace(
            go.Bar(
                x=dates,
                y=energy_balance,
                name='Energy Balance',
                marker=dict(
                    color=balance_colors,
                    opacity=0.9,
                    line=dict(color='black', width=1.5)
                ),
                text=[f'{val:+.1f}' for val in energy_balance],
                textposition='outside',
                textfont=dict(color='black', size=9, family='Arial'),
                hovertemplate='<b>Energy Balance</b><br>%{y:.2f} kWh<br>Date: %{customdata}<extra></extra>',
                customdata=full_dates,
                showlegend=False,
                width=0.6
            ),
            row=2, col=1
        )
        
        # Weekly Balance Indicator (Row 2, Col 2)
        total_gen = total_generation.sum()
        total_cons = consumption_kwh.sum()
        week_balance = total_gen - total_cons
        
        fig.add_trace(
            go.Indicator(
                mode="number+delta",
                value=week_balance,
                delta={
                    "reference": 0,
                    "relative": False,
                    "valueformat": ".2f",
                    "increasing": {"color": "#32CD32"},
                    "decreasing": {"color": "#FF6347"}
                },
                title={
                    "text": "<b>Weekly Balance</b><br><span style='font-size:12px;color:gray'>Total kWh</span>",
                    "font": {"size": 14}
                },
                number={
                    'suffix': " kWh",
                    'font': {'size': 28, 'family': 'Arial Black'},
                    'valueformat': '.2f'
                },
                domain={'x': [0, 1], 'y': [0, 1]}
            ),
            row=2, col=2
        )
        
        # Generation Ratio Gauge (Row 2, Col 3)
        efficiency_ratio = (total_gen / total_cons * 100) if total_cons > 0 else 0
        
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=efficiency_ratio,
                title={
                    "text": "<b>Generation<br>Efficiency</b>",
                    "font": {"size": 14}
                },
                gauge={
                    'axis': {'range': [0, 150], 'tickwidth': 2},
                    'bar': {'color': "#1f77b4", 'thickness': 0.8},
                    'steps': [
                        {'range': [0, 70], 'color': "#ffcccc"},
                        {'range': [70, 90], 'color': "#fff2cc"},
                        {'range': [90, 110], 'color': "#d4edda"},
                        {'range': [110, 150], 'color': "#cce5ff"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 100
                    }
                },
                domain={'x': [0, 1], 'y': [0, 1]},
                number={'suffix': "%", 'font': {'size': 20}}
            ),
            row=2, col=3
        )
        
        # Trend bars (Row 3)
        trend_values = [solar_trend, wind_trend, consumption_trend]
        trend_names = ['Solar', 'Wind', 'Consumption']
        trend_colors = ['#FFA500', '#4169E1', '#DC143C']
        
        for i, (trend_val, trend_name, trend_color) in enumerate(zip(trend_values, trend_names, trend_colors)):
            fig.add_trace(
                go.Bar(
                    x=[trend_name],
                    y=[abs(trend_val)],
                    name=f'{trend_name} Trend',
                    marker=dict(
                        color=trend_color if trend_val >= 0 else '#FF6347',
                        opacity=0.8,
                        line=dict(color='black', width=1)
                    ),
                    text=[f'{trend_val:+.1f}%'],
                    textposition='auto',
                    textfont=dict(color='white', size=12, family='Arial Black'),
                    hovertemplate=f'<b>{trend_name} Trend</b><br>{trend_val:+.1f}% daily<extra></extra>',
                    showlegend=False,
                    width=0.8
                ),
                row=3, col=i+1
            )
        
        # Add performance summary annotation
        best_day = dates[total_generation.index.get_loc(total_generation.idxmax())] if not total_generation.empty else 'N/A'
        worst_day = dates[total_generation.index.get_loc(total_generation.idxmin())] if not total_generation.empty else 'N/A'
        avg_daily_gen = total_generation.mean()
        
        summary_text = f"📈 <b>Weekly Performance Summary</b><br>" \
                      f"Best Day: {best_day} ({total_generation.max():.1f} kWh)<br>" \
                      f"Worst Day: {worst_day} ({total_generation.min():.1f} kWh)<br>" \
                      f"Daily Average: {avg_daily_gen:.1f} kWh<br>" \
                      f"Weekly Balance: {week_balance:+.1f} kWh<br>" \
                      f"Overall Efficiency: {efficiency_ratio:.1f}%"
        
        fig.add_annotation(
            text=summary_text,
            xref="paper", yref="paper",
            x=0.02, y=0.98,
            xanchor='left', yanchor='top',
            showarrow=False,
            font=dict(size=11, color="white", family="Arial"),
            bgcolor="rgba(0,0,0,0.85)",
            bordercolor="#4169E1",
            borderwidth=2,
            borderpad=8
        )
        
        # Add reference lines
        fig.add_shape(
            type="line",
            x0=0, x1=1, xref="x domain",
            y0=0, y1=0, yref="y2",
            line=dict(dash="dash", color="gray", width=2),
            row=2, col=1
        )
        
        # Update axes with better styling
        fig.update_xaxes(
            title_text="<b>Date (MM-DD)</b>",
            title_font=dict(size=12, family='Arial'),
            tickfont=dict(size=10, family='Arial'),
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.2)',
            row=1, col=1
        )
        
        fig.update_xaxes(
            title_text="<b>Date</b>",
            title_font=dict(size=10),
            tickfont=dict(size=8),
            row=2, col=1
        )
        
        for i in range(1, 4):
            fig.update_xaxes(
                title_font=dict(size=9),
                tickfont=dict(size=8),
                row=3, col=i
            )
        
        fig.update_yaxes(
            title_text="<b>Energy (kWh)</b>",
            title_font=dict(size=12, family='Arial'),
            tickfont=dict(size=10, family='Arial'),
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.2)',
            row=1, col=1
        )
        
        fig.update_yaxes(
            title_text="<b>Balance (kWh)</b>",
            title_font=dict(size=10),
            tickfont=dict(size=8),
            row=2, col=1
        )
        
        for i in range(1, 4):
            fig.update_yaxes(
                title_text="<b>%/day</b>",
                title_font=dict(size=9),
                tickfont=dict(size=8),
                row=3, col=i
            )
        
        # Update layout with perfect spacing
        fig.update_layout(
            title=dict(
                text="<b>📈 Daily Energy Statistics & Performance Analysis - Last 7 Days</b>",
                x=0.5,
                y=0.97,
                font=dict(size=18, family='Arial Black', color='#2c3e50')
            ),
            barmode='group',
            height=500,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.08,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="black",
                borderwidth=1,
                font=dict(size=11, family='Arial')
            ),
            plot_bgcolor='rgba(248,249,250,0.4)',
            paper_bgcolor='white',
            margin=dict(l=50, r=50, t=80, b=80),
            font=dict(family='Arial')
        )
        
        return fig.to_json()
    
    def create_energy_balance_pie_chart(self):
        """Create energy balance pie chart"""
        averages = self.analytics.calculate_averages(7)
        
        total_generation = averages['avg_solar_generation'] + averages['avg_wind_generation']
        consumption = averages['avg_consumption']
        
        if total_generation == 0:
            fig = go.Figure()
            fig.add_annotation(
                text="No generation data available yet.",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=16
            )
            fig.update_layout(title="Energy Balance", height=300)
            return fig.to_json()
        
        # Calculate energy balance
        net_balance = total_generation - consumption
        
        if net_balance > 0:
            labels = ['Solar Generation', 'Wind Generation', 'Consumption', 'Surplus']
            values = [
                averages['avg_solar_generation'],
                averages['avg_wind_generation'],
                consumption,
                net_balance
            ]
            colors = ['orange', 'blue', 'red', 'green']
        else:
            labels = ['Solar Generation', 'Wind Generation', 'Consumption']
            values = [
                averages['avg_solar_generation'],
                averages['avg_wind_generation'],
                consumption
            ]
            colors = ['orange', 'blue', 'red']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.3,
            marker_colors=colors
        )])
        
        fig.update_layout(
            title="Average Energy Balance (7 Days)",
            height=300,
            showlegend=True
        )
        
        return fig.to_json()
    
    def create_solar_vs_wind_comparison_graph(self):
        """Create comprehensive solar vs wind energy comparison graph"""
        # Get data for both energy sources
        energy_df = self.get_real_time_data(24)
        
        if energy_df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No comparison data available yet.",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font_size=16
            )
            fig.update_layout(
                title="Solar vs Wind Energy Comparison",
                height=500
            )
            return fig.to_json()
        
        # Calculate performance metrics
        solar_total = energy_df['solar_generation'].sum() / 1000  # kWh
        wind_total = energy_df['wind_generation'].sum() / 1000   # kWh
        solar_avg = energy_df['solar_generation'].mean()
        wind_avg = energy_df['wind_generation'].mean()
        solar_peak = energy_df['solar_generation'].max()
        wind_peak = energy_df['wind_generation'].max()
        
        # Calculate reliability (coefficient of variation - lower is more reliable)
        solar_reliability = (energy_df['solar_generation'].std() / solar_avg) * 100 if solar_avg > 0 else 0
        wind_reliability = (energy_df['wind_generation'].std() / wind_avg) * 100 if wind_avg > 0 else 0
        
        # Create simpler subplot layout
        fig = make_subplots(
            rows=2, cols=2,
            row_heights=[0.6, 0.4],
            column_widths=[0.6, 0.4],
            specs=[
                [{"colspan": 2}, None],
                [{"type": "bar"}, {"type": "bar"}]
            ],
            subplot_titles=(
                "Real-time Generation Comparison (24 Hours)",
                "",
                "Total Energy Production (24h)",
                "Peak Performance Comparison"
            ),
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )
        
        # Main comparison chart (Row 1)
        fig.add_trace(
            go.Scatter(
                x=energy_df['timestamp'],
                y=energy_df['solar_generation'],
                mode='lines',
                name='Solar Generation',
                line=dict(color='#FFA500', width=3),
                fill='tonexty',
                fillcolor='rgba(255, 165, 0, 0.3)',
                hovertemplate='<b>Solar</b><br>%{y:.1f} W<br>%{x}<extra></extra>'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=energy_df['timestamp'],
                y=energy_df['wind_generation'],
                mode='lines',
                name='Wind Generation',
                line=dict(color='#4169E1', width=3),
                fill='tozeroy',
                fillcolor='rgba(65, 105, 225, 0.3)',
                hovertemplate='<b>Wind</b><br>%{y:.1f} W<br>%{x}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Total energy production (Row 2, Col 1)
        fig.add_trace(
            go.Bar(
                x=['Solar', 'Wind'],
                y=[solar_total, wind_total],
                name='Total Generation',
                marker=dict(
                    color=['#FFA500', '#4169E1'],
                    opacity=0.8,
                    line=dict(color='black', width=1)
                ),
                text=[f'{solar_total:.2f} kWh', f'{wind_total:.2f} kWh'],
                textposition='auto',
                showlegend=False,
                hovertemplate='<b>%{x}</b><br>%{y:.2f} kWh<extra></extra>'
            ),
            row=2, col=1
        )
        
        # Peak performance comparison (Row 2, Col 2)
        fig.add_trace(
            go.Bar(
                x=['Solar Peak', 'Wind Peak'],
                y=[solar_peak, wind_peak],
                name='Peak Performance',
                marker=dict(
                    color=['#FF8C00', '#0000CD'],
                    opacity=0.9,
                    line=dict(color='white', width=1)
                ),
                text=[f'{solar_peak:.0f}W', f'{wind_peak:.0f}W'],
                textposition='auto',
                showlegend=False,
                hovertemplate='<b>%{x}</b><br>%{y:.0f} W<extra></extra>'
            ),
            row=2, col=2
        )
        
        # Performance summary annotation
        winner = "Solar" if solar_total > wind_total else "Wind"
        advantage = abs(solar_total - wind_total)
        advantage_pct = (advantage / max(solar_total, wind_total) * 100) if max(solar_total, wind_total) > 0 else 0
        
        # Calculate additional metrics
        solar_efficiency = (solar_avg / 1000) * 100 if solar_avg > 0 else 0
        wind_efficiency = (wind_avg / 1000) * 100 if wind_avg > 0 else 0
        
        summary_text = f"🏆 24h Performance Summary:<br>" \
                      f"Leading Source: <b>{winner}</b><br>" \
                      f"Advantage: {advantage:.2f} kWh ({advantage_pct:.1f}%)<br>" \
                      f"Combined Output: {(solar_total + wind_total):.2f} kWh<br><br>" \
                      f"📊 Key Metrics:<br>" \
                      f"Solar Avg: {solar_avg:.1f}W (Reliability: {100-solar_reliability:.1f}%)<br>" \
                      f"Wind Avg: {wind_avg:.1f}W (Reliability: {100-wind_reliability:.1f}%)<br>" \
                      f"Best Peak: {'Solar' if solar_peak > wind_peak else 'Wind'} ({max(solar_peak, wind_peak):.0f}W)"
        
        fig.add_annotation(
            text=summary_text,
            xref="paper", yref="paper",
            x=0.02, y=0.98,
            xanchor='left', yanchor='top',
            showarrow=False,
            font=dict(size=10, color="white"),
            bgcolor="rgba(0,0,0,0.8)",
            bordercolor="gold",
            borderwidth=2
        )
        
        # Update layout
        fig.update_xaxes(title_text="Time", row=1, col=1)
        fig.update_yaxes(title_text="Power (W)", row=1, col=1)
        fig.update_yaxes(title_text="Energy (kWh)", row=2, col=1)
        fig.update_yaxes(title_text="Peak (W)", row=2, col=2)
        
        fig.update_layout(
            title=dict(
                text="<b>🌞 Solar vs 🌬️ Wind Energy - Performance Analysis & Comparison</b>",
                x=0.5,
                font=dict(size=16)
            ),
            height=500,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5
            ),
            plot_bgcolor='rgba(248,249,250,0.8)',
            paper_bgcolor='white'
        )
        
        return fig.to_json()
    
    def get_current_stats(self):
        """Get current statistics for dashboard cards"""
        # Get latest data point
        latest_data = self.db.get_latest_energy_data(1)
        latest_solar = self.db.get_latest_solar_data(1)
        
        if not latest_data:
            return {
                'current_solar': 0,
                'current_wind': 0,
                'current_consumption': 0,
                'battery_level': 0,
                'battery_percentage': 0,
                'sun_intensity': 0,
                'efficiency': 0,
                'alerts_count': 0
            }
        
        latest = latest_data[0]
        solar_data = latest_solar[0] if latest_solar else None
        
        # Get unresolved alerts count
        alerts = self.db.get_unresolved_alerts()
        
        battery_capacity = 10000  # 10kWh
        battery_percentage = (latest[5] / battery_capacity) * 100  # battery_storage is at index 5
        
        return {
            'current_solar': round(latest[2], 1),  # solar_generation
            'current_wind': round(latest[3], 1),   # wind_generation
            'current_consumption': round(latest[4], 1),  # total_consumption
            'battery_level': round(latest[5], 1),  # battery_storage
            'battery_percentage': round(battery_percentage, 1),
            'sun_intensity': round(solar_data[2], 1) if solar_data else 0,  # sun_intensity
            'efficiency': round(solar_data[4] * 100, 1) if solar_data else 0,  # efficiency as percentage
            'alerts_count': len(alerts)
        }
