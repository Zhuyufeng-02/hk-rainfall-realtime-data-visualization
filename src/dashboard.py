"""
Interactive Web Dashboard for Hong Kong Rainfall Data
This module creates a real-time web dashboard using Dash.
"""

import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional

from data_fetcher import HKODataFetcher
from visualizer import RainfallVisualizer

logger = logging.getLogger(__name__)

class RainfallDashboard:
    """Interactive web dashboard for Hong Kong rainfall data."""
    
    def __init__(self, update_interval: int = 300000):  # 5 minutes default
        self.app = dash.Dash(
            __name__, 
            external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME]
        )
        self.fetcher = HKODataFetcher()
        self.visualizer = RainfallVisualizer()
        self.update_interval = update_interval  # milliseconds
        self.data_cache = {}
        self.historical_data = []
        
        self.setup_layout()
        self.setup_callbacks()
    
    def setup_layout(self):
        """Setup the dashboard layout."""
        self.app.layout = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("香港降雨實時監測 Hong Kong Rainfall Monitor", 
                           className="text-center mb-4",
                           style={'color': '#2c3e50', 'fontWeight': 'bold'}),
                    html.Hr()
                ], width=12)
            ]),
            
            # Status indicators
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("🌡️ Current Temperature", className="card-title"),
                            html.H2(id="current-temp", children="--°C", 
                                   className="text-primary")
                        ])
                    ], color="light")
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("💧 Average Rainfall", className="card-title"),
                            html.H2(id="avg-rainfall", children="--mm", 
                                   className="text-info")
                        ])
                    ], color="light")
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("🌧️ Active Regions", className="card-title"),
                            html.H2(id="active-regions", children="--", 
                                   className="text-success")
                        ])
                    ], color="light")
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("⚠️ Warnings", className="card-title"),
                            html.H2(id="warning-status", children="None", 
                                   className="text-warning")
                        ])
                    ], color="light")
                ], width=3)
            ], className="mb-4"),
            
            # Control panel
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Control Panel", className="card-title"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button("🔄 Refresh Data", id="refresh-btn", 
                                             color="primary", className="me-2"),
                                    dbc.Button("📊 Export Data", id="export-btn", 
                                             color="secondary")
                                ], width=6),
                                dbc.Col([
                                    html.Label("Auto-refresh:", className="form-label"),
                                    dbc.Switch(id="auto-refresh", value=True, 
                                             label="Enabled")
                                ], width=6)
                            ])
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),
            
            # Main charts
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Regional Rainfall Distribution"),
                        dbc.CardBody([
                            dcc.Graph(id="rainfall-bar-chart", 
                                    style={'height': '400px'})
                        ])
                    ])
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Rainfall Intensity Map"),
                        dbc.CardBody([
                            html.Div(id="rainfall-map-container",
                                   style={'height': '400px'})
                        ])
                    ])
                ], width=6)
            ], className="mb-4"),
            
            # Time series and additional info
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Rainfall Trends (Last 24 Hours)"),
                        dbc.CardBody([
                            dcc.Graph(id="time-series-chart", 
                                    style={'height': '300px'})
                        ])
                    ])
                ], width=8),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Data Information"),
                        dbc.CardBody([
                            html.Div(id="data-info", 
                                   children="Loading data information...")
                        ])
                    ])
                ], width=4)
            ], className="mb-4"),
            
            # Footer with auto-refresh
            dbc.Row([
                dbc.Col([
                    html.Hr(),
                    html.P([
                        "Last updated: ",
                        html.Span(id="last-updated", children="--"),
                        html.Br(),
                        "Data source: Hong Kong Observatory (HKO)",
                        html.Br(),
                        "⚡ Real-time updates every 5 minutes"
                    ], className="text-muted text-center")
                ], width=12)
            ]),
            
            # Auto-refresh component
            dcc.Interval(
                id='interval-component',
                interval=self.update_interval,
                n_intervals=0,
                disabled=False
            ),
            
            # Store components for data
            dcc.Store(id='data-store'),
            dcc.Store(id='historical-store', data=[])
        ], fluid=True)
    
    def setup_callbacks(self):
        """Setup dashboard callbacks."""
        
        @self.app.callback(
            [Output('data-store', 'data'),
             Output('historical-store', 'data')],
            [Input('interval-component', 'n_intervals'),
             Input('refresh-btn', 'n_clicks')],
            [dash.dependencies.State('historical-store', 'data')]
        )
        def update_data(n_intervals, refresh_clicks, historical_data):
            """Fetch and update data."""
            try:
                # Fetch new data
                new_data = self.fetcher.fetch_all_data()
                
                # Update historical data
                if historical_data is None:
                    historical_data = []
                
                # Add current data to history
                historical_data.append({
                    'timestamp': new_data['fetch_time'].isoformat(),
                    'data': new_data
                })
                
                # Keep only last 24 hours of data
                cutoff_time = datetime.now() - timedelta(hours=24)
                historical_data = [
                    item for item in historical_data 
                    if datetime.fromisoformat(item['timestamp']) > cutoff_time
                ]
                
                return new_data, historical_data
                
            except Exception as e:
                logger.error(f"Error updating data: {str(e)}")
                return {}, []
        
        @self.app.callback(
            [Output('current-temp', 'children'),
             Output('avg-rainfall', 'children'),
             Output('active-regions', 'children'),
             Output('warning-status', 'children'),
             Output('last-updated', 'children')],
            [Input('data-store', 'data')]
        )
        def update_status_cards(data):
            """Update status indicator cards."""
            if not data:
                return "--°C", "--mm", "--", "No Data", "--"
            
            try:
                # Temperature
                temp = data.get('current_weather', {}).get('temperature', 0)
                temp_str = f"{temp:.1f}°C" if temp else "--°C"
                
                # Average rainfall
                avg_rain = data.get('rainfall_data', {}).get('average_rainfall', 0)
                rain_str = f"{avg_rain:.1f}mm" if avg_rain else "--mm"
                
                # Active regions (regions with rainfall > 0)
                regions = data.get('rainfall_data', {}).get('regions', {})
                active_count = sum(1 for r in regions.values() 
                                 if r.get('average_rainfall', 0) > 0)
                total_count = len(regions)
                active_str = f"{active_count}/{total_count}"
                
                # Warning status
                warnings = data.get('weather_warnings', {}).get('active_warnings', [])
                if warnings:
                    warning_str = f"{len(warnings)} Active"
                else:
                    warning_str = "None"
                
                # Last updated
                fetch_time = data.get('fetch_time', datetime.now())
                if isinstance(fetch_time, str):
                    fetch_time = datetime.fromisoformat(fetch_time.replace('Z', '+00:00'))
                last_updated_str = fetch_time.strftime("%H:%M:%S")
                
                return temp_str, rain_str, active_str, warning_str, last_updated_str
                
            except Exception as e:
                logger.error(f"Error updating status cards: {str(e)}")
                return "--°C", "--mm", "--", "Error", "--"
        
        @self.app.callback(
            Output('rainfall-bar-chart', 'figure'),
            [Input('data-store', 'data')]
        )
        def update_bar_chart(data):
            """Update rainfall bar chart."""
            if not data:
                return go.Figure()
            
            try:
                rainfall_data = data.get('rainfall_data', {})
                return self.visualizer.create_rainfall_bar_chart(rainfall_data)
            except Exception as e:
                logger.error(f"Error updating bar chart: {str(e)}")
                return go.Figure()
        
        @self.app.callback(
            Output('time-series-chart', 'figure'),
            [Input('historical-store', 'data')]
        )
        def update_time_series(historical_data):
            """Update time series chart."""
            if not historical_data:
                return go.Figure()
            
            try:
                # Convert historical data format
                processed_data = []
                for item in historical_data:
                    processed_data.append({
                        'rainfall_data': {
                            'timestamp': datetime.fromisoformat(item['timestamp']),
                            'average_rainfall': item['data'].get('rainfall_data', {}).get('average_rainfall', 0)
                        }
                    })
                
                return self.visualizer.create_time_series_chart(processed_data)
            except Exception as e:
                logger.error(f"Error updating time series: {str(e)}")
                return go.Figure()
        
        @self.app.callback(
            Output('rainfall-map-container', 'children'),
            [Input('data-store', 'data')]
        )
        def update_map(data):
            """Update rainfall map."""
            if not data:
                return html.Div("Loading map...")
            
            try:
                rainfall_data = data.get('rainfall_data', {})
                district_coords = data.get('district_coordinates', {})
                
                # Create map
                rainfall_map = self.visualizer.create_rainfall_map(
                    rainfall_data, district_coords)
                
                # Convert to HTML string for embedding
                map_html = rainfall_map._repr_html_()
                
                return html.Iframe(
                    srcDoc=map_html,
                    width="100%",
                    height="400px",
                    style={"border": "none"}
                )
                
            except Exception as e:
                logger.error(f"Error updating map: {str(e)}")
                return html.Div(f"Error loading map: {str(e)}")
        
        @self.app.callback(
            Output('data-info', 'children'),
            [Input('data-store', 'data')]
        )
        def update_data_info(data):
            """Update data information panel."""
            if not data:
                return "No data available"
            
            try:
                rainfall_data = data.get('rainfall_data', {})
                current_weather = data.get('current_weather', {})
                warnings = data.get('weather_warnings', {})
                
                regions_count = len(rainfall_data.get('regions', {}))
                avg_rainfall = rainfall_data.get('average_rainfall', 0)
                humidity = current_weather.get('humidity', 0)
                warning_count = len(warnings.get('active_warnings', []))
                
                info_content = [
                    html.P([html.Strong("Data Summary:"), html.Br()]),
                    html.P(f"• Regions monitored: {regions_count}"),
                    html.P(f"• Average rainfall: {avg_rainfall:.1f}mm"),
                    html.P(f"• Humidity: {humidity}%"),
                    html.P(f"• Active warnings: {warning_count}"),
                    html.Hr(),
                    html.P([html.Strong("Weather Status:")]),
                    html.P(f"• Conditions: {current_weather.get('rainfall_status', 'Unknown')}"),
                    html.P(f"• Warning level: {warnings.get('warning_level', 'None')}")
                ]
                
                return info_content
                
            except Exception as e:
                logger.error(f"Error updating data info: {str(e)}")
                return f"Error: {str(e)}"
        
        @self.app.callback(
            Output('interval-component', 'disabled'),
            [Input('auto-refresh', 'value')]
        )
        def toggle_auto_refresh(auto_refresh_enabled):
            """Toggle auto-refresh functionality."""
            return not auto_refresh_enabled
    
    def run(self, host: str = '127.0.0.1', port: int = 8050, debug: bool = False):
        """Run the dashboard server."""
        print(f"Starting Hong Kong Rainfall Dashboard...")
        print(f"Dashboard will be available at: http://{host}:{port}")
        print(f"Auto-refresh interval: {self.update_interval/1000} seconds")
        
        self.app.run(host=host, port=port, debug=debug)

def main():
    """Run the dashboard."""
    dashboard = RainfallDashboard(update_interval=300000)  # 5 minutes
    dashboard.run(debug=True)

if __name__ == "__main__":
    main()
