"""
Visualization Module for HK Rainfall Data
This module creates dynamic charts and maps for Hong Kong rainfall visualization.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import folium
from folium import plugins
import json
import logging
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

class RainfallVisualizer:
    """Class for creating dynamic visualizations of Hong Kong rainfall data."""
    
    def __init__(self):
        self.color_scale = [
            [0.0, '#ffffff'],    # White - No rain
            [0.1, '#e6f3ff'],    # Very light blue - Trace
            [0.2, '#cce7ff'],    # Light blue - Light rain
            [0.4, '#80d4ff'],    # Blue - Moderate rain
            [0.6, '#3399ff'],    # Medium blue - Heavy rain
            [0.8, '#0066cc'],    # Dark blue - Very heavy rain
            [1.0, '#003d7a']     # Very dark blue - Extreme rain
        ]
        
        # Hong Kong bounds for mapping
        self.hk_bounds = {
            'lat_min': 22.15, 'lat_max': 22.57,
            'lon_min': 113.83, 'lon_max': 114.41
        }
        
        # Set matplotlib style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def create_rainfall_bar_chart(self, rainfall_data: Dict) -> go.Figure:
        """Create an interactive bar chart of rainfall by region."""
        try:
            if 'regions' not in rainfall_data or not rainfall_data['regions']:
                # Create empty chart with message
                fig = go.Figure()
                fig.add_annotation(
                    text="No rainfall data available",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=16)
                )
                fig.update_layout(title="Hong Kong Rainfall by Region")
                return fig
            
            regions = list(rainfall_data['regions'].keys())
            rainfall_amounts = [rainfall_data['regions'][region]['average_rainfall'] 
                              for region in regions]
            
            # Create color scale based on rainfall intensity
            max_rainfall = max(rainfall_amounts) if rainfall_amounts else 1
            colors = ['rgb({},{},{})'.format(
                max(0, 255 - int(amount/max_rainfall * 200)),
                max(0, 255 - int(amount/max_rainfall * 150)),
                255
            ) for amount in rainfall_amounts]
            
            fig = go.Figure(data=[
                go.Bar(
                    x=regions,
                    y=rainfall_amounts,
                    marker_color=colors,
                    text=[f'{amount:.1f}mm' for amount in rainfall_amounts],
                    textposition='auto',
                    hovertemplate='<b>%{x}</b><br>Rainfall: %{y:.1f}mm<extra></extra>'
                )
            ])
            
            fig.update_layout(
                title={
                    'text': f'Hong Kong Rainfall by Region<br><sub>Last updated: {rainfall_data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")}</sub>',
                    'x': 0.5,
                    'xanchor': 'center'
                },
                xaxis_title="Region",
                yaxis_title="Rainfall (mm)",
                xaxis_tickangle=-45,
                height=500,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating rainfall bar chart: {str(e)}")
            return go.Figure()
    
    def create_rainfall_map(self, rainfall_data: Dict, district_coords: Dict) -> folium.Map:
        """Create an interactive map showing rainfall distribution."""
        try:
            # Create base map centered on Hong Kong
            hk_map = folium.Map(
                location=[22.3193, 114.1694],  # Hong Kong center
                zoom_start=11,
                tiles='OpenStreetMap'
            )
            
            if 'regions' not in rainfall_data or not rainfall_data['regions']:
                folium.Marker(
                    location=[22.3193, 114.1694],
                    popup="No rainfall data available",
                    icon=folium.Icon(color='gray', icon='info-sign')
                ).add_to(hk_map)
                return hk_map
            
            # Calculate max rainfall for color scaling
            max_rainfall = max([region['average_rainfall'] 
                              for region in rainfall_data['regions'].values()])
            
            # Add markers for each region with rainfall data
            for region_name, region_data in rainfall_data['regions'].items():
                # Try to find coordinates for this region
                coords = None
                for district, coord in district_coords.items():
                    if any(keyword in region_name for keyword in district.split()):
                        coords = [coord['lat'], coord['lon']]
                        break
                
                # Use approximate coordinates if exact match not found
                if coords is None:
                    coords = [22.3193 + np.random.uniform(-0.1, 0.1), 
                             114.1694 + np.random.uniform(-0.1, 0.1)]
                
                rainfall_amount = region_data['average_rainfall']
                
                # Determine marker color based on rainfall intensity
                if rainfall_amount == 0:
                    color = 'gray'
                elif rainfall_amount < 1:
                    color = 'green'
                elif rainfall_amount < 5:
                    color = 'blue'
                elif rainfall_amount < 10:
                    color = 'orange'
                else:
                    color = 'red'
                
                # Create popup text
                popup_text = f"""
                <b>{region_name}</b><br>
                Rainfall: {rainfall_amount:.1f}mm<br>
                Range: {region_data['min_rainfall']:.1f} - {region_data['max_rainfall']:.1f}mm
                """
                
                folium.CircleMarker(
                    location=coords,
                    radius=max(5, min(20, rainfall_amount * 2)),
                    popup=folium.Popup(popup_text, max_width=200),
                    color=color,
                    fill=True,
                    fillColor=color,
                    fillOpacity=0.6,
                    weight=2
                ).add_to(hk_map)
            
            # Add legend
            legend_html = '''
            <div style="position: fixed; 
                        bottom: 50px; left: 50px; width: 150px; height: 120px; 
                        background-color: white; border:2px solid grey; z-index:9999; 
                        font-size:14px; padding: 10px">
            <p><b>Rainfall Legend</b></p>
            <p><i class="fa fa-circle" style="color:gray"></i> No rain</p>
            <p><i class="fa fa-circle" style="color:green"></i> Light (< 1mm)</p>
            <p><i class="fa fa-circle" style="color:blue"></i> Moderate (1-5mm)</p>
            <p><i class="fa fa-circle" style="color:orange"></i> Heavy (5-10mm)</p>
            <p><i class="fa fa-circle" style="color:red"></i> Very Heavy (> 10mm)</p>
            </div>
            '''
            hk_map.get_root().html.add_child(folium.Element(legend_html))
            
            return hk_map
            
        except Exception as e:
            logger.error(f"Error creating rainfall map: {str(e)}")
            return folium.Map(location=[22.3193, 114.1694], zoom_start=11)
    
    def create_time_series_chart(self, historical_data: List[Dict]) -> go.Figure:
        """Create a time series chart of rainfall trends."""
        try:
            if not historical_data:
                fig = go.Figure()
                fig.add_annotation(
                    text="No historical data available",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=16)
                )
                fig.update_layout(title="Rainfall Trends Over Time")
                return fig
            
            # Extract timestamps and average rainfall
            timestamps = [data['rainfall_data']['timestamp'] for data in historical_data 
                         if 'rainfall_data' in data and 'timestamp' in data['rainfall_data']]
            avg_rainfall = [data['rainfall_data']['average_rainfall'] for data in historical_data 
                           if 'rainfall_data' in data and 'average_rainfall' in data['rainfall_data']]
            
            if not timestamps or not avg_rainfall:
                fig = go.Figure()
                fig.add_annotation(
                    text="Insufficient data for time series",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=16)
                )
                fig.update_layout(title="Rainfall Trends Over Time")
                return fig
            
            fig = go.Figure()
            
            # Add line plot
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=avg_rainfall,
                mode='lines+markers',
                name='Average Rainfall',
                line=dict(color='blue', width=2),
                marker=dict(size=6),
                hovertemplate='Time: %{x}<br>Rainfall: %{y:.1f}mm<extra></extra>'
            ))
            
            # Add trend line if enough data points
            if len(timestamps) > 2:
                # Simple linear trend
                x_numeric = pd.to_datetime(timestamps).astype(np.int64) / 10**9
                z = np.polyfit(x_numeric, avg_rainfall, 1)
                trend_line = np.poly1d(z)(x_numeric)
                
                fig.add_trace(go.Scatter(
                    x=timestamps,
                    y=trend_line,
                    mode='lines',
                    name='Trend',
                    line=dict(color='red', width=2, dash='dash'),
                    hovertemplate='Trend: %{y:.1f}mm<extra></extra>'
                ))
            
            fig.update_layout(
                title={
                    'text': 'Hong Kong Rainfall Trends Over Time',
                    'x': 0.5,
                    'xanchor': 'center'
                },
                xaxis_title="Time",
                yaxis_title="Average Rainfall (mm)",
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                hovermode='x unified'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating time series chart: {str(e)}")
            return go.Figure()
    
    def create_weather_dashboard(self, all_data: Dict) -> go.Figure:
        """Create a comprehensive weather dashboard."""
        try:
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Current Conditions', 'Rainfall Distribution', 
                               'Weather Warnings', 'Regional Statistics'),
                specs=[[{"type": "indicator"}, {"type": "bar"}],
                       [{"type": "scatter"}, {"type": "pie"}]]
            )
            
            current_weather = all_data.get('current_weather', {})
            rainfall_data = all_data.get('rainfall_data', {})
            warnings = all_data.get('weather_warnings', {})
            
            # 1. Current conditions gauge
            temp = current_weather.get('temperature', 0)
            humidity = current_weather.get('humidity', 0)
            
            fig.add_trace(go.Indicator(
                mode="gauge+number+delta",
                value=temp,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': f"Temperature (°C)<br>Humidity: {humidity}%"},
                gauge={
                    'axis': {'range': [None, 40]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 20], 'color': "lightgray"},
                        {'range': [20, 30], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 35
                    }
                }
            ), row=1, col=1)
            
            # 2. Rainfall bar chart
            if rainfall_data.get('regions'):
                regions = list(rainfall_data['regions'].keys())[:8]  # Limit for visibility
                rainfall_amounts = [rainfall_data['regions'][region]['average_rainfall'] 
                                  for region in regions]
                
                fig.add_trace(go.Bar(
                    x=regions,
                    y=rainfall_amounts,
                    name="Rainfall",
                    marker_color='lightblue'
                ), row=1, col=2)
            
            # 3. Warnings scatter plot (timeline)
            if warnings.get('active_warnings'):
                warning_levels = {'thunderstorm': 3, 'heavy_rain': 2, 'strong_wind': 1}
                x_vals = list(range(len(warnings['active_warnings'])))
                y_vals = [warning_levels.get(w, 1) for w in warnings['active_warnings']]
                
                fig.add_trace(go.Scatter(
                    x=x_vals,
                    y=y_vals,
                    mode='markers+text',
                    text=warnings['active_warnings'],
                    textposition="top center",
                    marker=dict(size=15, color='red'),
                    name="Active Warnings"
                ), row=2, col=1)
            
            # 4. Regional statistics pie chart
            if rainfall_data.get('regions'):
                dry_regions = sum(1 for r in rainfall_data['regions'].values() 
                                if r['average_rainfall'] == 0)
                light_rain = sum(1 for r in rainfall_data['regions'].values() 
                               if 0 < r['average_rainfall'] <= 2)
                heavy_rain = sum(1 for r in rainfall_data['regions'].values() 
                               if r['average_rainfall'] > 2)
                
                fig.add_trace(go.Pie(
                    labels=['Dry', 'Light Rain', 'Heavy Rain'],
                    values=[dry_regions, light_rain, heavy_rain],
                    name="Regional Stats"
                ), row=2, col=2)
            
            fig.update_layout(
                title={
                    'text': f'Hong Kong Weather Dashboard - {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                    'x': 0.5,
                    'xanchor': 'center'
                },
                height=700,
                showlegend=False
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating weather dashboard: {str(e)}")
            return go.Figure()
    
    def save_static_chart(self, fig: go.Figure, filename: str, 
                         output_dir: str = "output") -> str:
        """Save a plotly figure as a static image."""
        try:
            filepath = f"{output_dir}/{filename}"
            fig.write_image(filepath, width=1200, height=800, scale=2)
            logger.info(f"Chart saved to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving chart: {str(e)}")
            return ""
    
    def save_interactive_chart(self, fig: go.Figure, filename: str, 
                              output_dir: str = "output") -> str:
        """Save a plotly figure as an interactive HTML file."""
        try:
            filepath = f"{output_dir}/{filename}"
            fig.write_html(filepath, include_plotlyjs='cdn')
            logger.info(f"Interactive chart saved to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving interactive chart: {str(e)}")
            return ""
    
    def save_map(self, map_obj: folium.Map, filename: str, 
                 output_dir: str = "output") -> str:
        """Save a folium map as an HTML file."""
        try:
            filepath = f"{output_dir}/{filename}"
            map_obj.save(filepath)
            logger.info(f"Map saved to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving map: {str(e)}")
            return ""

def main():
    """Test the visualizer."""
    from data_fetcher import HKODataFetcher
    
    print("Testing Rainfall Visualizer...")
    print("=" * 50)
    
    # Create test data
    visualizer = RainfallVisualizer()
    fetcher = HKODataFetcher()
    
    # Fetch real data
    print("1. Fetching data...")
    all_data = fetcher.fetch_all_data()
    
    # Create visualizations
    print("2. Creating bar chart...")
    bar_chart = visualizer.create_rainfall_bar_chart(all_data['rainfall_data'])
    
    print("3. Creating map...")
    rainfall_map = visualizer.create_rainfall_map(
        all_data['rainfall_data'], 
        all_data['district_coordinates']
    )
    
    print("4. Creating dashboard...")
    dashboard = visualizer.create_weather_dashboard(all_data)
    
    # Save visualizations
    print("5. Saving visualizations...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    visualizer.save_interactive_chart(bar_chart, f"rainfall_chart_{timestamp}.html")
    visualizer.save_interactive_chart(dashboard, f"weather_dashboard_{timestamp}.html")
    visualizer.save_map(rainfall_map, f"rainfall_map_{timestamp}.html")
    
    print("Visualizations saved to output directory!")

if __name__ == "__main__":
    main()
