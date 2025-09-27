import json

# Load the processed publications
with open('data/processed_publications.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Count research areas
areas = {}
for pub in data[:20]:  # Check first 20 publications
    area = pub['research_area']
    areas[area] = areas.get(area, 0) + 1
    print(f'{pub["title"]}: {pub["research_area"]}')

print(f'\nResearch Areas Distribution: {areas}')