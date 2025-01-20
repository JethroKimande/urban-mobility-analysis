import yaml
import requests
import matplotlib.pyplot as plt
from collections import Counter
from datetime import datetime
import os
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
    plt.show()

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
        plt.show()

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
london_map.save('london_disruptions.html')

print("\nSpatial Analysis:")
print("A map of disruptions has been saved as 'london_disruptions.html'.")