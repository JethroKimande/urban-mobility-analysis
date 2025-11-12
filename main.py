import yaml
import pandas as pd
import openpyxl
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
from shutil import copyfile

# Load YAML data for severity levels
with open('road_severity_levels.yaml', 'r') as file:
    severities = yaml.safe_load(file)
severity_dict = {item['severityLevel']: item['description'] for item in severities}

# TfL API credentials - Use environment variables for security (optional for local dev)
app_id = os.getenv('TFL_APP_ID', "")
app_key = os.getenv('TFL_APP_KEY', "")

def fetch_tfl_disruptions():
    # If credentials are missing, skip remote call
    if not app_key:
        print("Warning: TFL_APP_KEY not set. Skipping API call and using local cache if available.")
        return []
    url = f"https://api.tfl.gov.uk/Road/all/Disruption?app_id={app_id}&app_key={app_key}"
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            # Check status code if response exists
            if hasattr(http_err, 'response') and http_err.response is not None:
                if http_err.response.status_code == 429:  # Rate limit exceeded
                    print("Rate limit exceeded. Retrying in 60 seconds...")
                    sleep(60)  # Wait for a minute
                    continue
            if attempt < max_retries - 1:
                print(f"Retrying in {2**attempt} seconds...")
                sleep(2**attempt)  # Exponential backoff
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

# Local fallbacks if API not available or returned nothing
if not disruptions:
    # Try JSON cache
    if os.path.exists('disruptions.json'):
        try:
            with open('disruptions.json', 'r', encoding='utf-8') as f:
                disruptions = json.load(f)
                print("Loaded disruptions from local disruptions.json cache.")
        except Exception as e:
            print(f"Failed to read disruptions.json: {e}")
    # Try CSV
    if not disruptions and os.path.exists('disruptions.csv'):
        try:
            df_cached = pd.read_csv('disruptions.csv')
            disruptions = df_cached.to_dict(orient='records')
            print("Loaded disruptions from local disruptions.csv.")
        except Exception as e:
            print(f"Failed to read disruptions.csv: {e}")
    # Try Excel
    if not disruptions and os.path.exists('disruptions.xlsx'):
        try:
            df_cached_xlsx = pd.read_excel('disruptions.xlsx')
            disruptions = df_cached_xlsx.to_dict(orient='records')
            print("Loaded disruptions from local disruptions.xlsx.")
        except Exception as e:
            print(f"Failed to read disruptions.xlsx: {e}")

if not disruptions:
    print("No disruption data available or there was an error in fetching data.")
else:
    # Extract severity levels from disruptions
    severity_counts = Counter(int(d['severityLevel']) for d in disruptions if 'severityLevel' in d)
    print(f"Total disruptions fetched: {len(disruptions)}")
    # Assuming disruptions is your list or dictionary of disruptions
    df = pd.DataFrame(disruptions)

    # To save as CSV
    df.to_csv('disruptions.csv', index=False)

    # To save as Excel
    df.to_excel('disruptions.xlsx', index=False)
    # To save as JSON
    try:
        with open('disruptions.json', 'w', encoding='utf-8') as jf:
            json.dump(disruptions, jf, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Failed to write disruptions.json: {e}")
    for d in disruptions:
        print(f"Disruption ID: {d.get('id', 'No ID')}, Severity: {d.get('severity', 'No severity level')}")
    

    # Print severe disruptions (adjust the severity level threshold as needed)
    severe_disruptions = [d for d in disruptions if d.get('severity', 'No severity') in ['Serious']]

    print("Severe disruptions:")
    for disruption in severe_disruptions:
        print(f" - {disruption.get('severity', 'Unknown severity')}: {disruption.get('comments', 'No description')}")

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
    # Initialize an empty dictionary to count impacts by severity
    severity_impact = {}

    # Loop through each disruption in the dataset
    for d in disruptions:
        # Get the severity directly as a string
        severity = d.get('severity', 'Unknown severity')
        
        # Count the occurrences of each severity level
        severity_impact[severity] = severity_impact.get(severity, 0) + 1

    # Sort by impact (severity in a custom order)
    # Here we define a custom order since we're dealing with string values
    severity_order = ['Serious', 'Moderate', 'Minimal', 'No impact']
    sorted_impact = sorted(severity_impact.items(), key=lambda x: severity_order.index(x[0]) if x[0] in severity_order else len(severity_order))

    # Print the impact analysis
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
                
                # Ensure point is a list with 2 elements
                if isinstance(point, list) and len(point) == 2:
                    lat, lon = point[1], point[0]  # Assuming [lon, lat]
                else:
                    print(f"Point data for disruption {disruption.get('id', 'No ID')} is not in expected format: {point}")
                    continue

                # Add a marker for each disruption
                folium.Marker(
                    [lat, lon],
                    popup=f"{disruption.get('comments', 'No description')}<br>Severity: {disruption.get('severity', 'Unknown severity')}",
                    icon=folium.Icon(color='red' if disruption.get('severity', 'No severity') in ['Serious'] else 'blue')
                ).add_to(london_map)
            except (KeyError, IndexError, TypeError, ValueError) as e:
                print(f"Could not plot disruption: {disruption.get('id', 'No ID')} - Error: {e}")

    # Save the map
    london_map.save("map.html")

# Create a blog-like HTML content
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Urban Mobility Analysis</title>
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
        iframe {{ width: 100%; height: 600px; border: none; margin-bottom: 20px; }} /* Adjusted height for dashboard visibility */
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
    </nav>

    <div class="content">
        <main class="main-content">
            <article class="post">
                <h2 id="analysis">Weekly Urban Mobility Analysis</h2>
                <p>Published on: {datetime.now().strftime('%Y-%m-%d')}</p>
                <section>
                    <h3>Introduction</h3>
                    <p>Welcome to our weekly urban mobility analysis focusing on road disruptions in London. This analysis aims to provide insights into the severity, timing, and location of disruptions to help in planning and understanding urban mobility issues.</p>
                </section>

                <section>
                    <h3>Analysis Summary</h3>
                    <p><strong>Severe disruptions:</strong> There are {len(severe_disruptions)} severe disruptions now.</p>
                    <ul>
                        {''.join([f"<li>{d.get('severity', 'Unknown severity')}: {d.get('comments', 'No description')}</li>" for d in severe_disruptions])}
                    </ul>
                    <p><strong>Impact Analysis by Severity:</strong></p>
                    <ul>
                        {''.join([f"<li>{impact}: {count} disruptions</li>" for impact, count in sorted_impact])}
                    </ul>
                </section>

                <section>
                    <h3>Dashboard</h3>
                    <p>Explore our interactive dashboard for real-time disruption analysis:</p>
                    <iframe src="https://expert-broccoli-j66pjqx7jrw3564w-8050.app.github.dev/" title="TfL Disruption Dashboard" width="100%" height="600"></iframe>
                </section>

                <section>
                    <h3>Map of Road Disruptions in London</h3>
                    <iframe src="map.html" title="London Disruptions Map"></iframe>
                </section>

                <section>
                    <h3>Visualizations</h3>
                    <h4>Time Series of Disruptions</h4>
                    <img src="time_series_plot.png" alt="Time Series Plot" width="100%"/>
                </section>

                <section>
                    <h3>Conclusion</h3>
                    <p>Based on the analysis, we observe that the majority of disruptions occur during peak hours, and severe disruptions are more frequent than anticipated. This map and data visualization help in understanding the spatial distribution and severity of these disruptions, aiding in better urban planning and traffic management strategies.</p>
                </section>
            </article>
        </main>

        <aside class="sidebar">
            <h2>About This Blog</h2>
            <p>This blog provides weekly insights into urban mobility issues in London, focusing on road disruptions. Our aim is to inform and engage the community in discussions about traffic management and urban planning.</p>
            
            <h2>Recent Posts</h2>
            <ul>
                <li><a href="#post1">Last Week's Analysis</a></li>
                <li><a href="#post2">Impact of Weather on Traffic</a></li>
                <li><a href="#post3">Future of Urban Mobility</a></li>
            </ul>
            
            <h2>Contact Us</h2>
            <p>For inquiries or to contribute, reach us at <a href="mailto:urbanmobility@example.com">urbanmobility@example.com</a></p>
        </aside>
    </div>

    <footer>
        <p>Data sourced from Transport for London API. Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </footer>
</body>
</html>
"""

# Write the new HTML content to index.html
with open('index.html', 'w') as f:
    f.write(html_content)

print("\nSpatial Analysis:")
print("A blog post with comprehensive analysis has been saved as 'index.html'.")

# -------------------------------------------
# Archival: Save weekly snapshots under data/YYYY-MM-DD and build archives.html
# -------------------------------------------
def ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def write_json(path: str, data_obj) -> None:
    with open(path, 'w', encoding='utf-8') as fobj:
        json.dump(data_obj, fobj, ensure_ascii=False, indent=2)

today_str = datetime.now().strftime('%Y-%m-%d')
archive_dir = os.path.join('data', today_str)
ensure_dir('data')
ensure_dir(archive_dir)

# Copy latest outputs into archive folder
for src, dst_name in [
    ('disruptions.csv', 'disruptions.csv'),
    ('disruptions.xlsx', 'disruptions.xlsx'),
    ('disruptions.json', 'disruptions.json'),
    ('map.html', 'map.html'),
    ('time_series_plot.png', 'time_series_plot.png'),
    ('index.html', 'index.html'),
]:
    if os.path.exists(src):
        try:
            copyfile(src, os.path.join(archive_dir, dst_name))
        except Exception as e:
            print(f"Archive copy failed for {src} -> {archive_dir}: {e}")

# Maintain an index of available archive dates
archives_index_path = os.path.join('data', 'index.json')
archives = []
if os.path.exists(archives_index_path):
    try:
        with open(archives_index_path, 'r', encoding='utf-8') as idxf:
            archives = json.load(idxf)
    except Exception as e:
        print(f"Failed to read archives index: {e}")
if today_str not in archives:
    archives.append(today_str)
    archives.sort(reverse=True)
    write_json(archives_index_path, archives)

# Generate a simple archives.html page
archives_items = '\n'.join(
    [f'<li><a href="data/{d}/index.html">{d} report</a> — '
     f'<a href="data/{d}/map.html">map</a> — '
     f'<a href="data/{d}/disruptions.json">json</a> — '
     f'<a href="data/{d}/disruptions.csv">csv</a> — '
     f'<a href="data/{d}/disruptions.xlsx">xlsx</a></li>'
     for d in archives]
)
archives_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Urban Mobility Archives</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f8fafc; }}
        h1 {{ margin-top: 0; }}
        .muted {{ color: #6b7280; }}
        .card {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; max-width: 900px; }}
    </style>
    <link rel="icon" href="data:,">
</head>
<body>
    <h1>Urban Mobility Archives</h1>
    <p class="muted">Weekly snapshots of reports and datasets.</p>
    <div class="card">
        <ol>
            {archives_items}
        </ol>
    </div>
    <p><a href="./">Back to latest report</a></p>
    <footer class="muted"><small>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></footer>
</body>
</html>
"""
try:
    with open('archives.html', 'w', encoding='utf-8') as archf:
        archf.write(archives_html)
    print("Archives page generated at 'archives.html'.")
except Exception as e:
    print(f"Failed to write archives.html: {e}")