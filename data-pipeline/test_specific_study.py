import requests
import json

# Test the scientific data analysis endpoint with a specific study
url = "http://localhost:8003/scientific-data-analysis"
data = {
    "study_id": "OSD-100"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")