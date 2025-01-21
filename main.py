import yaml
import requests
import matplotlib.pyplot as plt
from collections import Counter
from datetime import datetime
import os
import base64
from io import BytesIO
from time import sleep
import folium
import json

# Load YAML data for severity levels
with open('road_severity_levels.yaml', 'r') as file:
    severities = yaml.safe_load(file)
severity_dict = {item['severityLevel']: item['description'] for item in severities}

# TfL API credentials - Use environment variables for security
app_id = os.getenv('TFL_APP_ID', "")
app_key = os.getenv('TFL_APP_KEY', "")

if not app_key:
    raise EnvironmentError("TFL_APP_KEY environment variable not set. Please set it before running the script.")

def fetch_tfl_disruptions():
    url = f"https://api.tfl.gov.uk/Road/all/Disruption?app_id={app_id}&app_key={app_key}"
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            if response.status_code == 429:  # Rate limit exceeded
                print("Rate limit exceeded. Retrying in 60 seconds...")
                sleep(60)  # Wait for a minute
            else:
                break
        except requests.exceptions.RequestException as e:
            print(f"Request error occurred: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {2**attempt} seconds...")
                sleep(2**attempt)  # Exponential backoff
            else:
                print("Max retries reached, giving up.")
                return []
    return []

# Fetch disruptions from TfL API
disruptions = fetch_tfl_disruptions()

if not disruptions:
    print("No disruption data available or there was an error in fetching data.")
else:
    # Extract severity levels from disruptions
    severity_counts = Counter(int(d['severityLevel']) for d in disruptions if 'severityLevel' in d)

    # Plot the data
    plt.figure(figsize=(12, 6))
    bars = plt.bar(range(len(severity_counts)), list(severity_counts.values()), align='center', alpha=0.7)
    plt.xticks(range(len(severity_counts)), [severity_dict[k] for k in severity_counts.keys()], rotation='vertical')
    plt.ylabel('Number of Disruptions')
    plt.title('Road Disruption Severities - TfL Data')
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                 f'{height}', ha='center', va='bottom')
    plt.tight_layout()

    # Save the plot as an image
    # severity_plot_buffer = BytesIO()
    plt.savefig('severity_plot.png')
    # severity_plot_buffer.seek(0)
    # severity_plot_data = base64.b64encode(severity_plot_buffer.getvalue()).decode()

    plt.close()

    # plt.show()

    # Print severe disruptions (adjust the severity level threshold as needed)
    severe_disruptions = [d for d in disruptions if int(d.get('severityLevel', 11)) <= 7]
    print("Severe disruptions:")
    for disruption in severe_disruptions:
        print(f" - {severity_dict.get(int(disruption['severityLevel']), 'Unknown severity')}: {disruption.get('description', 'No description')}")

    # 1. Time series analysis of disruptions
    disruption_times = [datetime.strptime(d['startDateTime'], '%Y-%m-%dT%H:%M:%S%z') for d in disruptions if 'startDateTime' in d]
    if disruption_times:
        plt.figure(figsize=(12, 6))
        plt.hist([dt.hour for dt in disruption_times], bins=24, range=(0, 24), edgecolor='black')
        plt.title('Distribution of Disruption Start Times')
        plt.xlabel('Hour of Day')
        plt.ylabel('Count of Disruptions')

        # Save this plot as an image
        # time_series_plot_buffer = BytesIO()
        plt.savefig("time_series_plot.png")
        # time_series_plot_buffer.seek(0)
        # time_series_plot_data = base64.b64encode(time_series_plot_buffer.getvalue()).decode()

        plt.close()

        # plt.show()

    # 2. Impact analysis by severity
    severity_impact = {}
    for d in disruptions:
        severity = int(d.get('severityLevel', -1))
        if severity in severity_dict:
            impact = severity_dict[severity]
            severity_impact[impact] = severity_impact.get(impact, 0) + 1

    # Sort by impact (severity level in reverse order)
    sorted_impact = sorted(severity_impact.items(), key=lambda x: list(severity_dict.values()).index(x[0]), reverse=True)

    print("\nImpact Analysis by Severity:")
    for impact, count in sorted_impact:
        print(f" - {impact}: {count} disruptions")

    # 3. Spatial analysis
# Create a base map centered on London
london_map = folium.Map(location=[51.5074, -0.1278], zoom_start=12)

for disruption in disruptions:
    # Check if the disruption has a point
    if 'point' in disruption:
        try:
            point = disruption['point']
            print(f"Point data for disruption {disruption.get('id', 'No ID')}: {point}")
            
            # Check if point is a list
            if isinstance(point, list) and len(point) == 2:
                lat, lon = point[1], point[0]  # Assuming [lon, lat]
            else:
                raise ValueError("Point data format not recognized")

            # Add a marker for each disruption
            folium.Marker(
                [lat, lon],
                popup=f"{disruption.get('description', 'No description')}<br>Severity: {severity_dict.get(int(disruption['severityLevel']), 'Unknown')}",
                icon=folium.Icon(color='red' if int(disruption['severityLevel']) <= 7 else 'blue')
            ).add_to(london_map)
        except (KeyError, IndexError, TypeError, ValueError) as e:
            print(f"Could not plot disruption: {disruption.get('id', 'No ID')} - Error: {e}")

# Save the map
london_map.save("map.html")

# Create a blog-like HTML content with detailed explanations
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Urban Mobility Blog</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }}
        .header {{ background-color: #333; color: white; padding: 15px 0; text-align: center; }}
        .nav {{ background-color: #444; overflow: hidden; }}
        .nav a {{ float: left; display: block; color: white; text-align: center; padding: 14px 16px; text-decoration: none; }}
        .nav a:hover {{ background-color: #ddd; color: black; }}
        .content {{ display: flex; flex-wrap: wrap; max-width: 1200px; margin: 20px auto; }}
        .main-content {{ flex: 3; background-color: white; padding: 20px; margin-right: 20px; }}
        .sidebar {{ flex: 1; background-color: white; padding: 20px; }}
        .post {{ margin-bottom: 20px; }}
        .post h2 {{ color: #333; }}
        iframe {{ width: 100%; height: 400px; border: none; margin-bottom: 20px; }}
        img {{ max-width: 100%; height: auto; margin-bottom: 20px; }}
        @media (max-width: 768px) {{ 
            .content {{ flex-direction: column; }}
            .main-content, .sidebar {{ flex: 1 1 100%; margin-right: 0; margin-bottom: 20px; }}
        }}
    </style>
</head>
<body>
    <header class="header">
        <h1>Urban Mobility Blog</h1>
    </header>

    <nav class="nav">
        <a href="#home">Home</a>
        <a href="#about">About</a>
        <a href="#analysis">Analysis</a>
        <a href="#contact">Contact</a>
    </nav>

    <div class="content">
        <main class="main-content">
            <article class="post">
                <h2 id="analysis">Weekly Urban Mobility Analysis</h2>
                <p>Published on: {datetime.now().strftime('%Y-%m-%d')}</p>
                
                <section>
                    <h3>Introduction</h3>
                    <p>Welcome to our weekly urban mobility analysis focusing on road disruptions in London. This analysis aims to provide insights into the severity, timing, and location of disruptions to help in planning and understanding urban mobility issues. By analyzing data from Transport for London (TfL), we can offer a comprehensive view of how disruptions impact the city's transportation network.</p>
                </section>

                <section>
                    <h3>Analysis Summary</h3>
                    <p><strong>Severe disruptions:</strong> There are {len(severe_disruptions)} severe disruptions this week. These are disruptions with a severity level of 7 or less, indicating significant impact on traffic flow, often requiring alternative routes or causing considerable delays.</p>
                    <ul>
                        {''.join([f"<li><strong>{severity_dict.get(int(d['severityLevel']), 'Unknown severity')}</strong>: {d.get('description', 'No description')} - This disruption might affect major roads or public transport routes, leading to rerouting or increased congestion.</li>" for d in severe_disruptions])}
                    </ul>
                    <p><strong>Impact Analysis by Severity:</strong> Below is a breakdown of how many disruptions occurred at each severity level this week:</p>
                    <ul>
                        {''.join([f"<li><strong>{impact}</strong>: {count} disruptions - This indicates the frequency of disruptions at this severity, where higher counts suggest more common issues of this type affecting urban mobility.</li>" for impact, count in sorted_impact])}
                    </ul>
                </section>

                <section>
                    <h3>Map of Road Disruptions in London</h3>
                    <p>This interactive map visualizes the locations of all reported road disruptions in London. Each marker represents a disruption, with red markers indicating severe disruptions (severity level 7 or below) and blue markers for less severe issues. By clicking on a marker, you can see the description of the disruption and its severity level, providing a spatial understanding of where and how often disruptions occur across the city. This can be particularly useful for urban planners to identify hotspots for frequent disruptions.</p>
                    <iframe src="map.html" title="London Disruptions Map"></iframe>
                </section>

                <section>
                    <h3>Visualizations</h3>
                    <h4>Severity of Disruptions</h4>
                    <p>This bar chart shows the distribution of disruptions