# Hong Kong Rainfall Real-time Data Visualization

This project provides dynamic real-time visualization of Hong Kong rainfall data from the Hong Kong Observatory (HKO).

## Features

- Real-time rainfall data scraping from HKO website
- Interactive visualizations using Plotly and Dash
- Automatic data refresh every few minutes
- Regional rainfall distribution mapping
- Historical data tracking and trends
- Web-based dashboard for easy access

## Installation

1. Clone or download this project
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the main application:
   ```bash
   python main.py
   ```

2. Open your web browser and go to `http://localhost:8050` to view the dashboard

## Project Structure

- `src/` - Source code modules
  - `data_fetcher.py` - HKO data scraping functionality  
  - `visualizer.py` - Data visualization components
  - `dashboard.py` - Web dashboard interface
- `data/` - Cached rainfall data
- `output/` - Generated charts and reports
- `main.py` - Main application entry point

## Data Sources

- Hong Kong Observatory: https://www.hko.gov.hk/
- Real-time rainfall data and weather radar images

## License

This project is for educational and research purposes.
