#!/usr/bin/env python3
"""
Test script to verify OSDR files endpoint is working correctly
"""

import requests
import json

def test_osdr_endpoint():
    """Test the OSDR files endpoint"""
    print("🧪 Testing NASA OSDR Files Endpoint")
    print("=" * 40)
    
    # Test data pipeline endpoint
    try:
        print("Testing Data Pipeline Endpoint (http://localhost:8001/osdr-files)...")
        response = requests.get("http://localhost:8001/osdr-files", timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {len(data)} OSDR files")
            if data:
                print("Sample file data:")
                print(json.dumps(data[0], indent=2))
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to data pipeline. Is it running?")
        print("   Please start the data pipeline with: python main.py")
        return False
    except requests.exceptions.Timeout:
        print("❌ Error: Request timed out. The service might be busy.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_backend_proxy():
    """Test the backend proxy endpoint"""
    print("\nTesting Backend Proxy Endpoint (http://localhost:4001/api/osdr/files)...")
    
    try:
        response = requests.get("http://localhost:4001/api/osdr/files", timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Success! Found {data.get('count', 0)} OSDR files")
                files_data = data.get("data", [])
                if files_data:
                    print("Sample file data:")
                    print(json.dumps(files_data[0], indent=2))
                return True
            else:
                print(f"❌ Error from backend: {data.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to backend. Is it running?")
        print("   Please start the backend with: npm run dev")
        return False
    except requests.exceptions.Timeout:
        print("❌ Error: Request timed out. The service might be busy.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("NASA Space Biology Knowledge Engine - OSDR Endpoint Test")
    print("Make sure all services are running before running this test.")
    print()
    
    # Test both endpoints
    data_pipeline_success = test_osdr_endpoint()
    backend_success = test_backend_proxy()
    
    print("\n" + "=" * 40)
    if data_pipeline_success and backend_success:
        print("🎉 All tests passed! The OSDR integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")