import requests
import time

def trigger_data_processing():
    """Trigger data processing via the API"""
    url = "http://localhost:8002/process"
    
    try:
        print("Sending request to trigger data processing...")
        response = requests.post(url)
        
        if response.status_code == 200:
            print("Data processing started successfully!")
            print(response.json())
            
            # Check status periodically
            status_url = "http://localhost:8002/status"
            while True:
                time.sleep(5)
                status_response = requests.get(status_url)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"Processing status: {status_data['status']} - {status_data['message']}")
                    if status_data['status'] == 'completed':
                        print("Data processing completed!")
                        break
                    elif status_data['status'] == 'error':
                        print(f"Processing error: {status_data['message']}")
                        break
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the data pipeline service")
        print("Please make sure the data pipeline is running on port 8002")
    except Exception as e:
        print(f"Error triggering data processing: {e}")

if __name__ == "__main__":
    trigger_data_processing()