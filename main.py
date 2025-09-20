#!/usr/bin/env python3
"""
Hong Kong Rainfall Real-time Data Visualization
Main Application Entry Point

This application provides real-time monitoring and visualization of Hong Kong rainfall data
from the Hong Kong Observatory website.

Usage:
    python main.py [options]

Options:
    --mode dashboard    Run interactive web dashboard (default)
    --mode updater     Run background data updater only
    --mode test        Run data fetching tests
    --mode visualize   Create static visualizations
    --interval N       Update interval in minutes (default: 5)
    --port N          Web dashboard port (default: 8050)
    --host HOST       Web dashboard host (default: 127.0.0.1)
    --help            Show this help message

Author: HK Rainfall Monitor
Date: 2025-09-20
"""

import sys
import os
import argparse
import logging
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data_fetcher import HKODataFetcher
from src.visualizer import RainfallVisualizer
from src.dashboard import RainfallDashboard
from src.real_time_updater import RealTimeUpdater

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hk_rainfall_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def print_banner():
    """Print application banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║    🌧️  Hong Kong Rainfall Real-time Monitor  🌧️             ║
    ║                                                              ║
    ║    Real-time rainfall data visualization from HKO           ║
    ║    香港降雨實時監測系統                                       ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def run_dashboard_mode(args):
    """Run the interactive web dashboard."""
    print("🚀 Starting Interactive Web Dashboard...")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Update interval: {args.interval} minutes")
    print()
    
    try:
        # Create dashboard with specified update interval
        dashboard = RainfallDashboard(update_interval=args.interval * 60 * 1000)  # Convert to milliseconds
        
        print("🌐 Dashboard will be available at:")
        print(f"   http://{args.host}:{args.port}")
        print()
        print("📊 Features available:")
        print("   • Real-time rainfall monitoring")
        print("   • Interactive regional maps")
        print("   • Weather warnings and alerts")
        print("   • Historical trend analysis")
        print("   • Auto-refresh functionality")
        print()
        print("⚡ Press Ctrl+C to stop the server")
        print("=" * 60)
        
        dashboard.run(host=args.host, port=args.port, debug=False)
        
    except KeyboardInterrupt:
        print("\\n🛑 Dashboard stopped by user")
    except Exception as e:
        logger.error(f"Error running dashboard: {str(e)}")
        print(f"❌ Error: {str(e)}")

def run_updater_mode(args):
    """Run background data updater only."""
    print("🔄 Starting Background Data Updater...")
    print(f"   Update interval: {args.interval} minutes")
    print()
    
    try:
        updater = RealTimeUpdater(update_interval=args.interval)
        updater.start_background_updates()
        
        print("✅ Background updater started successfully")
        print("📁 Data will be saved to:")
        print("   • data/ - Raw data files")
        print("   • output/ - Generated visualizations")
        print()
        print("⚡ Press Ctrl+C to stop the updater")
        print("=" * 50)
        
        # Keep running
        import time
        while True:
            time.sleep(30)
            latest_data = updater.get_latest_data()
            if latest_data:
                rainfall_avg = latest_data.get('rainfall_data', {}).get('average_rainfall', 0)
                regions_count = len(latest_data.get('rainfall_data', {}).get('regions', {}))
                print(f"🌧️  Latest: {rainfall_avg:.1f}mm avg, {regions_count} regions monitored")
    
    except KeyboardInterrupt:
        print("\\n🛑 Updater stopped by user")
        updater.stop_background_updates()
    except Exception as e:
        logger.error(f"Error running updater: {str(e)}")
        print(f"❌ Error: {str(e)}")

def run_test_mode(args):
    """Run data fetching and visualization tests."""
    print("🧪 Running Data Fetching Tests...")
    print("=" * 50)
    
    try:
        # Test data fetcher
        print("1️⃣ Testing HKO Data Fetcher...")
        fetcher = HKODataFetcher()
        
        print("   📡 Fetching current weather...")
        current_weather = fetcher.fetch_current_weather()
        if 'error' not in current_weather:
            temp = current_weather.get('temperature', 'N/A')
            humidity = current_weather.get('humidity', 'N/A')
            print(f"   ✅ Temperature: {temp}°C, Humidity: {humidity}%")
        else:
            print(f"   ❌ Error: {current_weather['error']}")
        
        print("   🌧️ Fetching rainfall data...")
        rainfall_data = fetcher.fetch_rainfall_data()
        if 'error' not in rainfall_data:
            regions = len(rainfall_data.get('regions', {}))
            avg_rain = rainfall_data.get('average_rainfall', 0)
            print(f"   ✅ {regions} regions monitored, avg rainfall: {avg_rain:.1f}mm")
        else:
            print(f"   ❌ Error: {rainfall_data['error']}")
        
        print("   ⚠️ Fetching weather warnings...")
        warnings = fetcher.fetch_weather_warnings()
        if 'error' not in warnings:
            active_warnings = len(warnings.get('active_warnings', []))
            print(f"   ✅ {active_warnings} active warnings")
        else:
            print(f"   ❌ Error: {warnings['error']}")
        
        # Test visualizer
        print("\\n2️⃣ Testing Visualization Components...")
        visualizer = RainfallVisualizer()
        
        if 'error' not in rainfall_data:
            print("   📊 Creating bar chart...")
            bar_chart = visualizer.create_rainfall_bar_chart(rainfall_data)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            visualizer.save_interactive_chart(bar_chart, f"test_chart_{timestamp}.html")
            print("   ✅ Bar chart created")
            
            print("   🗺️ Creating rainfall map...")
            district_coords = fetcher.get_district_coordinates()
            rainfall_map = visualizer.create_rainfall_map(rainfall_data, district_coords)
            visualizer.save_map(rainfall_map, f"test_map_{timestamp}.html")
            print("   ✅ Rainfall map created")
        
        print("\\n3️⃣ Test Summary:")
        print("   📁 Check 'output/' directory for generated files")
        print("   ✅ All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in test mode: {str(e)}")
        print(f"❌ Test failed: {str(e)}")

def run_visualize_mode(args):
    """Create static visualizations from current data."""
    print("📊 Creating Static Visualizations...")
    print("=" * 50)
    
    try:
        # Fetch current data
        print("📡 Fetching latest data from HKO...")
        fetcher = HKODataFetcher()
        all_data = fetcher.fetch_all_data()
        
        # Create visualizations
        print("🎨 Creating visualizations...")
        visualizer = RainfallVisualizer()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Bar chart
        print("   📊 Rainfall bar chart...")
        bar_chart = visualizer.create_rainfall_bar_chart(all_data['rainfall_data'])
        visualizer.save_interactive_chart(bar_chart, f"rainfall_chart_{timestamp}.html")
        visualizer.save_static_chart(bar_chart, f"rainfall_chart_{timestamp}.png")
        
        # Map
        print("   🗺️ Rainfall distribution map...")
        rainfall_map = visualizer.create_rainfall_map(
            all_data['rainfall_data'], all_data['district_coordinates'])
        visualizer.save_map(rainfall_map, f"rainfall_map_{timestamp}.html")
        
        # Dashboard
        print("   📈 Weather dashboard...")
        dashboard_chart = visualizer.create_weather_dashboard(all_data)
        visualizer.save_interactive_chart(dashboard_chart, f"weather_dashboard_{timestamp}.html")
        visualizer.save_static_chart(dashboard_chart, f"weather_dashboard_{timestamp}.png")
        
        # Save raw data
        print("   💾 Saving raw data...")
        fetcher.save_data_to_file(all_data, f"visualization_data_{timestamp}.json")
        
        print("\\n✅ Visualizations created successfully!")
        print("📁 Files saved to 'output/' directory:")
        print(f"   • rainfall_chart_{timestamp}.html/.png")
        print(f"   • rainfall_map_{timestamp}.html")
        print(f"   • weather_dashboard_{timestamp}.html/.png")
        print(f"   • data/visualization_data_{timestamp}.json")
        
    except Exception as e:
        logger.error(f"Error in visualize mode: {str(e)}")
        print(f"❌ Visualization failed: {str(e)}")

def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description="Hong Kong Rainfall Real-time Data Visualization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # Run web dashboard (default)
  python main.py --mode dashboard         # Run web dashboard explicitly
  python main.py --mode updater           # Run background updater only
  python main.py --mode test              # Run data fetching tests
  python main.py --mode visualize         # Create static visualizations
  python main.py --interval 10            # Update every 10 minutes
  python main.py --port 8080              # Use port 8080 for dashboard
  python main.py --host 0.0.0.0           # Allow external connections
        """
    )
    
    parser.add_argument('--mode', 
                       choices=['dashboard', 'updater', 'test', 'visualize'],
                       default='dashboard',
                       help='Application mode (default: dashboard)')
    
    parser.add_argument('--interval', 
                       type=int, 
                       default=5,
                       help='Update interval in minutes (default: 5)')
    
    parser.add_argument('--port', 
                       type=int, 
                       default=8050,
                       help='Web dashboard port (default: 8050)')
    
    parser.add_argument('--host', 
                       type=str, 
                       default='127.0.0.1',
                       help='Web dashboard host (default: 127.0.0.1)')
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('output', exist_ok=True)
    
    # Log startup
    logger.info(f"Starting Hong Kong Rainfall Monitor in {args.mode} mode")
    
    # Route to appropriate mode
    try:
        if args.mode == 'dashboard':
            run_dashboard_mode(args)
        elif args.mode == 'updater':
            run_updater_mode(args)
        elif args.mode == 'test':
            run_test_mode(args)
        elif args.mode == 'visualize':
            run_visualize_mode(args)
    except Exception as e:
        logger.error(f"Fatal error in {args.mode} mode: {str(e)}")
        print(f"\\n❌ Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
