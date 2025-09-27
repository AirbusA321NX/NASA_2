#!/usr/bin/env python3
"""
Test script to call the analyze endpoint and demonstrate progress bar functionality
"""

import requests
import json
import time

def test_analyze_endpoint():
    """Test the analyze endpoint with sample data"""
    print("Testing AI Engine analyze endpoint...")
    print("=" * 50)
    
    # Load test data
    with open('test_data.json', 'r') as f:
        test_data = json.load(f)
    
    print(f"Sending {len(test_data['publications'])} publications to AI Engine for analysis...")
    
    # Make request to analyze endpoint
    try:
        response = requests.post(
            "http://localhost:8003/analyze",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("AI Engine analysis completed successfully!")
            print(f"Response keys: {list(result['data'].keys())}")
            
            # Show some sample results
            if 'overview' in result['data']:
                print("\nSample Overview Results:")
                for item in result['data']['overview'][:2]:
                    print(f"  - {item}")
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the data pipeline server")
        print("Please make sure the server is running on port 8003")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_analyze_endpoint()