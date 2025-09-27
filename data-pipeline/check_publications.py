import json

# Load the processed publications data
with open('data/processed_publications.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Number of publications: {len(data)}")

if data:
    print("First publication:")
    print(json.dumps(data[0], indent=2))
else:
    print("No publications found in the file.")