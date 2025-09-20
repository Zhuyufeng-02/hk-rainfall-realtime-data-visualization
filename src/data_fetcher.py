"""
HKO Data Fetcher Module
This module handles fetching real-time rainfall and weather data from the Hong Kong Observatory website.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import re
from datetime import datetime, timedelta
import time
import logging
from typing import Dict, List, Optional, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HKODataFetcher:
    """Class to fetch real-time weather and rainfall data from HKO website."""
    
    def __init__(self):
        self.base_url = "https://www.hko.gov.hk"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Hong Kong district coordinates (approximate centers)
        self.hk_districts = {
            'Central & Western': {'lat': 22.2855, 'lon': 114.1577},
            'Eastern': {'lat': 22.2783, 'lon': 114.2367},
            'Southern': {'lat': 22.2461, 'lon': 114.1628},
            'Wan Chai': {'lat': 22.2767, 'lon': 114.1759},
            'Kowloon City': {'lat': 22.3251, 'lon': 114.1944},
            'Kwun Tong': {'lat': 22.3127, 'lon': 114.2267},
            'Sham Shui Po': {'lat': 22.3309, 'lon': 114.1639},
            'Wong Tai Sin': {'lat': 22.3418, 'lon': 114.1946},
            'Yau Tsim Mong': {'lat': 22.3093, 'lon': 114.1694},
            'Islands': {'lat': 22.2587, 'lon': 113.9447},
            'Kwai Tsing': {'lat': 22.3573, 'lon': 114.1378},
            'North': {'lat': 22.4964, 'lon': 114.1476},
            'Sai Kung': {'lat': 22.3816, 'lon': 114.2723},
            'Sha Tin': {'lat': 22.3817, 'lon': 114.1973},
            'Tai Po': {'lat': 22.4455, 'lon': 114.1645},
            'Tsuen Wan': {'lat': 22.3736, 'lon': 114.1177},
            'Tuen Mun': {'lat': 22.3943, 'lon': 113.9766},
            'Yuen Long': {'lat': 22.4473, 'lon': 114.0305}
        }
    
    def fetch_current_weather(self) -> Dict:
        """Fetch current weather data from HKO main page."""
        try:
            url = f"{self.base_url}/tc/index.html"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            weather_data = {
                'timestamp': datetime.now(),
                'temperature': None,
                'humidity': None,
                'rainfall_status': None,
                'weather_conditions': None
            }
            
            # Extract temperature
            temp_elements = soup.find_all(text=re.compile(r'\d+\.?\d*°C'))
            if temp_elements:
                for temp in temp_elements:
                    match = re.search(r'(\d+\.?\d*)°C', temp)
                    if match:
                        weather_data['temperature'] = float(match.group(1))
                        break
            
            # Extract humidity
            humidity_elements = soup.find_all(text=re.compile(r'\d+%'))
            if humidity_elements:
                for humidity in humidity_elements:
                    match = re.search(r'(\d+)%', humidity)
                    if match:
                        weather_data['humidity'] = int(match.group(1))
                        break
            
            # Extract weather conditions
            weather_text = soup.get_text()
            if '雨' in weather_text or '驟雨' in weather_text:
                weather_data['rainfall_status'] = 'raining'
            elif '多雲' in weather_text:
                weather_data['rainfall_status'] = 'cloudy'
            elif '天晴' in weather_text:
                weather_data['rainfall_status'] = 'sunny'
            else:
                weather_data['rainfall_status'] = 'unknown'
                
            logger.info(f"Current weather fetched: {weather_data}")
            return weather_data
            
        except Exception as e:
            logger.error(f"Error fetching current weather: {str(e)}")
            return {'timestamp': datetime.now(), 'error': str(e)}
    
    def fetch_rainfall_data(self) -> Dict:
        """Fetch detailed rainfall data from different regions."""
        try:
            url = f"{self.base_url}/textonly/current/rainfall_sr_uc.htm"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            text_content = soup.get_text()
            
            rainfall_data = {
                'timestamp': datetime.now(),
                'regions': {},
                'total_regions': 0,
                'average_rainfall': 0
            }
            
            # Parse rainfall data using regex patterns
            # Look for patterns like "中西區1毫米" or "西貢0至5毫米"
            patterns = [
                r'([中西東南北]+\s*[區]?)\s*(\d+)\s*毫\s*米',
                r'([中西東南北]+\s*[區]?)\s*(\d+)\s*至\s*(\d+)\s*毫\s*米',
                r'(九龍城|葵青|荃灣|灣仔|離島區|西貢|沙田|大埔|屯門|元朗)\s*(\d+)\s*至?\s*(\d+)?\s*毫\s*米'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text_content)
                for match in matches:
                    if len(match) == 2:  # Single value
                        region, rainfall = match
                        rainfall_data['regions'][region.strip()] = {
                            'min_rainfall': float(rainfall),
                            'max_rainfall': float(rainfall),
                            'average_rainfall': float(rainfall)
                        }
                    elif len(match) == 3:  # Range value
                        region, min_rain, max_rain = match
                        if max_rain:
                            avg_rain = (float(min_rain) + float(max_rain)) / 2
                        else:
                            avg_rain = float(min_rain)
                        rainfall_data['regions'][region.strip()] = {
                            'min_rainfall': float(min_rain),
                            'max_rainfall': float(max_rain) if max_rain else float(min_rain),
                            'average_rainfall': avg_rain
                        }
            
            # Calculate statistics
            if rainfall_data['regions']:
                rainfall_data['total_regions'] = len(rainfall_data['regions'])
                avg_values = [region['average_rainfall'] for region in rainfall_data['regions'].values()]
                rainfall_data['average_rainfall'] = sum(avg_values) / len(avg_values)
            
            logger.info(f"Rainfall data fetched for {rainfall_data['total_regions']} regions")
            return rainfall_data
            
        except Exception as e:
            logger.error(f"Error fetching rainfall data: {str(e)}")
            return {'timestamp': datetime.now(), 'error': str(e)}
    
    def fetch_weather_warnings(self) -> Dict:
        """Fetch current weather warnings and alerts."""
        try:
            url = f"{self.base_url}/tc/index.html"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            warnings = {
                'timestamp': datetime.now(),
                'active_warnings': [],
                'warning_level': 'none'
            }
            
            # Look for warning indicators
            warning_elements = soup.find_all('img', {'src': re.compile(r'warn.*\.png')})
            for element in warning_elements:
                src = element.get('src', '')
                if 'ts' in src:  # Thunderstorm warning
                    warnings['active_warnings'].append('thunderstorm')
                    warnings['warning_level'] = 'high'
                elif 'rain' in src:  # Rain warning
                    warnings['active_warnings'].append('heavy_rain')
                    warnings['warning_level'] = 'medium'
                elif 'wind' in src:  # Wind warning
                    warnings['active_warnings'].append('strong_wind')
                    warnings['warning_level'] = 'medium'
            
            # Check text content for warning keywords
            text_content = soup.get_text().lower()
            if '雷暴警告' in text_content:
                if 'thunderstorm' not in warnings['active_warnings']:
                    warnings['active_warnings'].append('thunderstorm')
                warnings['warning_level'] = 'high'
            
            if '暴雨警告' in text_content:
                if 'heavy_rain' not in warnings['active_warnings']:
                    warnings['active_warnings'].append('heavy_rain')
                warnings['warning_level'] = 'high'
            
            logger.info(f"Weather warnings: {warnings['active_warnings']}")
            return warnings
            
        except Exception as e:
            logger.error(f"Error fetching weather warnings: {str(e)}")
            return {'timestamp': datetime.now(), 'error': str(e)}
    
    def get_district_coordinates(self) -> Dict:
        """Return Hong Kong district coordinates for mapping."""
        return self.hk_districts.copy()
    
    def fetch_all_data(self) -> Dict:
        """Fetch all available weather and rainfall data."""
        logger.info("Fetching all weather data from HKO...")
        
        all_data = {
            'fetch_time': datetime.now(),
            'current_weather': self.fetch_current_weather(),
            'rainfall_data': self.fetch_rainfall_data(),
            'weather_warnings': self.fetch_weather_warnings(),
            'district_coordinates': self.get_district_coordinates()
        }
        
        return all_data
    
    def save_data_to_file(self, data: Dict, filename: Optional[str] = None) -> str:
        """Save fetched data to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hko_data_{timestamp}.json"
        
        filepath = f"data/{filename}"
        
        # Convert datetime objects to strings for JSON serialization
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=convert_datetime)
            
            logger.info(f"Data saved to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving data: {str(e)}")
            return ""

def main():
    """Test the data fetcher."""
    fetcher = HKODataFetcher()
    
    print("Testing HKO Data Fetcher...")
    print("=" * 50)
    
    # Test current weather
    print("1. Fetching current weather...")
    current_weather = fetcher.fetch_current_weather()
    print(f"Current weather: {current_weather}")
    print()
    
    # Test rainfall data
    print("2. Fetching rainfall data...")
    rainfall_data = fetcher.fetch_rainfall_data()
    print(f"Rainfall data: {rainfall_data}")
    print()
    
    # Test weather warnings
    print("3. Fetching weather warnings...")
    warnings = fetcher.fetch_weather_warnings()
    print(f"Weather warnings: {warnings}")
    print()
    
    # Test fetch all data
    print("4. Fetching all data...")
    all_data = fetcher.fetch_all_data()
    
    # Save data
    print("5. Saving data...")
    filepath = fetcher.save_data_to_file(all_data)
    print(f"Data saved to: {filepath}")

if __name__ == "__main__":
    main()
