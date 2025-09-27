import requests
import json

def test_frontend_backend_connection():
    """
    Test if the frontend can connect to the backend services
    """
    try:
        # Test the analytics endpoint
        print("Testing connection to backend analytics API...")
        response = requests.get('http://localhost:4004/api/analytics')
        print(f"Analytics API Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Analytics API Success: {data.get('success', False)}")
            if data.get('success'):
                print(f"Total Publications: {data['data']['overview']['total_publications']}")
            else:
                print(f"Analytics API Error: {data.get('error', 'Unknown error')}")
        else:
            print(f"Analytics API Error: {response.text}")
        
        print("\n" + "="*50 + "\n")
        
        # Test the publications endpoint
        print("Testing connection to backend publications API...")
        response = requests.get('http://localhost:4004/api/publications')
        print(f"Publications API Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Publications API Success: {data.get('success', False)}")
            if data.get('success'):
                print(f"Total Publications: {len(data['data']['publications'])}")
                print("First publication:", data['data']['publications'][0]['title'] if data['data']['publications'] else "None")
            else:
                print(f"Publications API Error: {data.get('error', 'Unknown error')}")
        else:
            print(f"Publications API Error: {response.text}")
            
    except Exception as e:
        print(f"Error connecting to backend: {e}")

if __name__ == "__main__":
    test_frontend_backend_connection()