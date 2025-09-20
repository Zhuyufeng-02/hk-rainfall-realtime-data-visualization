"""
Real-time Data Updater for Hong Kong Rainfall Monitor
This module handles scheduled data updates and background data collection.
"""

import schedule
import time
import json
import os
from datetime import datetime, timedelta
import threading
import logging
from typing import Dict, List, Optional

from data_fetcher import HKODataFetcher
from visualizer import RainfallVisualizer

logger = logging.getLogger(__name__)

class RealTimeUpdater:
    """Background service for real-time data updates."""
    
    def __init__(self, update_interval: int = 5, data_dir: str = "data"):
        self.update_interval = update_interval  # minutes
        self.data_dir = data_dir
        self.fetcher = HKODataFetcher()
        self.visualizer = RainfallVisualizer()
        self.is_running = False
        self.update_thread = None
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs("output", exist_ok=True)
        
        # Historical data storage
        self.historical_file = os.path.join(data_dir, "historical_data.json")
        self.historical_data = self.load_historical_data()
    
    def load_historical_data(self) -> List[Dict]:
        """Load historical data from file."""
        try:
            if os.path.exists(self.historical_file):
                with open(self.historical_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Filter data to last 24 hours
                    cutoff_time = datetime.now() - timedelta(hours=24)
                    filtered_data = []
                    for item in data:
                        timestamp = datetime.fromisoformat(item['timestamp'])
                        if timestamp > cutoff_time:
                            filtered_data.append(item)
                    return filtered_data
            return []
        except Exception as e:
            logger.error(f"Error loading historical data: {str(e)}")
            return []
    
    def save_historical_data(self):
        """Save historical data to file."""
        try:
            # Convert datetime objects to strings
            serializable_data = []
            for item in self.historical_data:
                serializable_item = item.copy()
                if 'timestamp' in serializable_item and isinstance(serializable_item['timestamp'], datetime):
                    serializable_item['timestamp'] = serializable_item['timestamp'].isoformat()
                if 'data' in serializable_item:
                    # Handle nested datetime objects
                    data_copy = self._convert_datetimes_to_strings(serializable_item['data'])
                    serializable_item['data'] = data_copy
                serializable_data.append(serializable_item)
            
            with open(self.historical_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Historical data saved: {len(serializable_data)} records")
        except Exception as e:
            logger.error(f"Error saving historical data: {str(e)}")
    
    def _convert_datetimes_to_strings(self, obj):
        """Recursively convert datetime objects to strings."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self._convert_datetimes_to_strings(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_datetimes_to_strings(item) for item in obj]
        else:
            return obj
    
    def fetch_and_store_data(self):
        """Fetch current data and add to historical storage."""
        try:
            logger.info("Fetching new data...")
            
            # Fetch current data
            current_data = self.fetcher.fetch_all_data()
            
            # Add to historical data
            self.historical_data.append({
                'timestamp': current_data['fetch_time'],
                'data': current_data
            })
            
            # Keep only last 24 hours
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.historical_data = [
                item for item in self.historical_data 
                if item['timestamp'] > cutoff_time
            ]
            
            # Save current data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            current_file = os.path.join(self.data_dir, f"current_data_{timestamp}.json")
            self.fetcher.save_data_to_file(current_data, f"current_data_{timestamp}.json")
            
            # Save historical data
            self.save_historical_data()
            
            # Create latest visualizations
            self.create_latest_visualizations(current_data)
            
            logger.info(f"Data update completed. Historical records: {len(self.historical_data)}")
            
        except Exception as e:
            logger.error(f"Error in fetch_and_store_data: {str(e)}")
    
    def create_latest_visualizations(self, data: Dict):
        """Create and save latest visualizations."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create bar chart
            bar_chart = self.visualizer.create_rainfall_bar_chart(data['rainfall_data'])
            self.visualizer.save_interactive_chart(
                bar_chart, f"latest_rainfall_chart.html", "output")
            
            # Create map
            rainfall_map = self.visualizer.create_rainfall_map(
                data['rainfall_data'], data['district_coordinates'])
            self.visualizer.save_map(rainfall_map, f"latest_rainfall_map.html", "output")
            
            # Create dashboard
            dashboard_chart = self.visualizer.create_weather_dashboard(data)
            self.visualizer.save_interactive_chart(
                dashboard_chart, f"latest_dashboard.html", "output")
            
            # Create time series if we have historical data
            if len(self.historical_data) > 1:
                # Convert historical data for visualizer
                viz_historical_data = []
                for item in self.historical_data:
                    viz_item = {
                        'rainfall_data': {
                            'timestamp': item['timestamp'],
                            'average_rainfall': item['data'].get('rainfall_data', {}).get('average_rainfall', 0)
                        }
                    }
                    viz_historical_data.append(viz_item)
                
                time_series = self.visualizer.create_time_series_chart(viz_historical_data)
                self.visualizer.save_interactive_chart(
                    time_series, f"latest_time_series.html", "output")
            
            logger.info("Latest visualizations created")
            
        except Exception as e:
            logger.error(f"Error creating visualizations: {str(e)}")
    
    def start_background_updates(self):
        """Start background data updates."""
        if self.is_running:
            logger.warning("Background updates already running")
            return
        
        self.is_running = True
        
        # Schedule regular updates
        schedule.every(self.update_interval).minutes.do(self.fetch_and_store_data)
        
        # Initial data fetch
        self.fetch_and_store_data()
        
        def run_schedule():
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        # Start scheduler in background thread
        self.update_thread = threading.Thread(target=run_schedule, daemon=True)
        self.update_thread.start()
        
        logger.info(f"Background updates started (interval: {self.update_interval} minutes)")
    
    def stop_background_updates(self):
        """Stop background data updates."""
        self.is_running = False
        schedule.clear()
        if self.update_thread:
            self.update_thread.join(timeout=5)
        logger.info("Background updates stopped")
    
    def get_latest_data(self) -> Optional[Dict]:
        """Get the most recent data."""
        if self.historical_data:
            return self.historical_data[-1]['data']
        return None
    
    def get_historical_data(self, hours: int = 24) -> List[Dict]:
        """Get historical data for specified number of hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            item for item in self.historical_data 
            if item['timestamp'] > cutoff_time
        ]
    
    def cleanup_old_files(self, days: int = 7):
        """Clean up old data files."""
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            
            for filename in os.listdir(self.data_dir):
                if filename.startswith('current_data_') and filename.endswith('.json'):
                    filepath = os.path.join(self.data_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                    if file_time < cutoff_time:
                        os.remove(filepath)
                        logger.info(f"Deleted old file: {filename}")
            
            # Clean up old output files
            for filename in os.listdir("output"):
                if filename.endswith('.html') and not filename.startswith('latest_'):
                    filepath = os.path.join("output", filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                    if file_time < cutoff_time:
                        os.remove(filepath)
                        logger.info(f"Deleted old output file: {filename}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up old files: {str(e)}")

def main():
    """Test the real-time updater."""
    print("Testing Real-time Updater...")
    print("=" * 50)
    
    updater = RealTimeUpdater(update_interval=1)  # 1 minute for testing
    
    try:
        # Start background updates
        updater.start_background_updates()
        
        print(f"Background updates started. Press Ctrl+C to stop.")
        print(f"Check the 'data' and 'output' directories for updates.")
        
        # Keep running
        while True:
            time.sleep(10)
            latest_data = updater.get_latest_data()
            if latest_data:
                rainfall_avg = latest_data.get('rainfall_data', {}).get('average_rainfall', 0)
                print(f"Latest average rainfall: {rainfall_avg:.1f}mm")
    
    except KeyboardInterrupt:
        print("\nStopping background updates...")
        updater.stop_background_updates()
        print("Updater stopped.")

if __name__ == "__main__":
    main()
