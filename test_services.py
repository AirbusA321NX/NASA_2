#!/usr/bin/env python3
"""
Test script to verify that all services can start correctly
"""
import subprocess
import time
import requests
import sys
import os

def test_service(url, service_name, timeout=10):
    """Test if a service is responding"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            print(f"✅ {service_name} is running")
            return True
        else:
            print(f"❌ {service_name} returned status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {service_name} is not responding: {e}")
        return False

def main():
    print("Testing NASA Space Biology Knowledge Engine services...")
    
    # Test frontend (Next.js)
    frontend_ok = test_service("http://localhost:3000", "Frontend")
    
    # Test backend (Express)
    backend_ok = test_service("http://localhost:4003", "Backend")
    
    # Test data pipeline (FastAPI)
    datapipeline_ok = test_service("http://localhost:8003", "Data Pipeline")
    
    if frontend_ok and backend_ok and datapipeline_ok:
        print("\n🎉 All services are running correctly!")
        return 0
    else:
        print("\n⚠️  Some services are not running correctly")
        return 1

if __name__ == "__main__":
    sys.exit(main())