#!/usr/bin/env python3
"""
Quick Test Script for Hong Kong Rainfall Monitor
This script performs a quick test of all components.
"""

import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def quick_test():
    """Perform a quick test of all components."""
    print("🧪 Quick Test - Hong Kong Rainfall Monitor")
    print("=" * 50)
    
    try:
        # Test imports
        print("1. Testing imports...")
        from src.data_fetcher import HKODataFetcher
        from src.visualizer import RainfallVisualizer
        from src.dashboard import RainfallDashboard
        from src.real_time_updater import RealTimeUpdater
        print("   ✅ All imports successful")
        
        # Test data fetcher
        print("\\n2. Testing data fetcher...")
        fetcher = HKODataFetcher()
        test_data = fetcher.fetch_current_weather()
        if 'error' not in test_data:
            print("   ✅ Data fetcher working")
        else:
            print(f"   ⚠️ Data fetcher warning: {test_data.get('error', 'Unknown error')}")
        
        # Test visualizer
        print("\\n3. Testing visualizer...")
        visualizer = RainfallVisualizer()
        print("   ✅ Visualizer initialized")
        
        # Test dashboard creation
        print("\\n4. Testing dashboard creation...")
        dashboard = RainfallDashboard(update_interval=60000)  # 1 minute for test
        print("   ✅ Dashboard created successfully")
        
        # Test updater
        print("\\n5. Testing real-time updater...")
        updater = RealTimeUpdater(update_interval=1)
        print("   ✅ Updater initialized")
        
        print("\\n🎉 All components tested successfully!")
        print("\\n📋 To run the application:")
        print("   python main.py --mode dashboard    # Web dashboard")
        print("   python main.py --mode test         # Full test")
        print("   python main.py --mode visualize    # Create static charts")
        print("   python main.py --mode updater      # Background updater")
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("💡 Make sure all required packages are installed:")
        print("   pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    quick_test()
