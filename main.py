# main.py
import yaml
import matplotlib.pyplot as plt
from collections import Counter

# Load YAML data
with open('road_severity_levels.yaml', 'r') as file:
    severities = yaml.safe_load(file)

# Convert to a dictionary for easy lookup
severity_dict = {item['severityLevel']: item['description'] for item in severities}

# Mock data for disruptions, replace this with actual TfL API calls
mock_disruptions = [
    {'severityLevel': 6, 'description': 'Major road works'},
    {'severityLevel': 8, 'description': 'Minor road works'},
    {'severityLevel': 7, 'description': 'Accident'},
    {'severityLevel': 9, 'description': 'Congestion'},
    {'severityLevel': 10, 'description': 'Traffic light failure'},
]

# Count occurrences of each severity level
severity_counts = Counter(d['severityLevel'] for d in mock_disruptions)

# Plot the data
plt.figure(figsize=(10, 6))
bars = plt.bar(range(len(severity_counts)), list(severity_counts.values()), align='center', alpha=0.7)
plt.xticks(range(len(severity_counts)), [severity_dict[k] for k in severity_counts.keys()], rotation='vertical')
plt.ylabel('Number of Disruptions')
plt.title('Road Disruption Severities')

# Add labels to each bar
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height,
             f'{height}', ha='center', va='bottom')

plt.tight_layout()
plt.show()

# Filter and print disruptions based on severity
severe_disruptions = [d for d in mock_disruptions if d['severityLevel'] <= 7]
print("Severe disruptions:")
for disruption in severe_disruptions:
    print(f" - {severity_dict[disruption['severityLevel']]}: {disruption['description']}")