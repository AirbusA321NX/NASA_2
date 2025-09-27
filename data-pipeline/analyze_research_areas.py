import json
from collections import Counter

# Load the processed publications data
with open('data/processed_publications.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extract research areas
areas = [item.get('research_area', 'Unknown') for item in data]
counter = Counter(areas)

print('Research Areas:')
for area, count in counter.most_common():
    percentage = (count / len(data)) * 100
    print(f'{area}: {count} studies ({percentage:.1f}%)')

# Look for studies with "test" or "debug" in their research area
test_studies = [item for item in data if 'test' in item.get('research_area', '').lower()]
debug_studies = [item for item in data if 'debug' in item.get('research_area', '').lower()]

print(f"\nStudies with 'test' in research area ({len(test_studies)} found):")
for study in test_studies:
    print(f"  - {study.get('osdr_id', 'Unknown ID')}: {study.get('title', 'No title')}")

print(f"\nStudies with 'debug' in research area ({len(debug_studies)} found):")
for study in debug_studies:
    print(f"  - {study.get('osdr_id', 'Unknown ID')}: {study.get('title', 'No title')}")