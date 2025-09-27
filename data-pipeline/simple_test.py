import requests
import json

# Test the scientific data analysis endpoint
url = "http://localhost:8003/scientific-data-analysis"

# Test data - analyze all studies with a limit of 1 and sample 3 files per study
payload = {
    "study_id": None,
    "limit": 1,
    "sample_files_per_study": 3
}

headers = {
    "Content-Type": "application/json"
}

print("Sending request to scientific data analysis endpoint...")
try:
    response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")