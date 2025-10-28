#!/usr/bin/env python3
"""
Test script to verify AgentCore Runtime compliance.
"""

import requests
import json
import time
from typing import Dict, Any


def test_ping_endpoint(base_url: str = "http://localhost:8080") -> bool:
    """Test the /ping endpoint compliance."""
    try:
        response = requests.get(f"{base_url}/ping", timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Ping endpoint returned status {response.status_code}")
            return False
        
        data = response.json()
        
        # Check required fields
        if "status" not in data:
            print("❌ Ping response missing 'status' field")
            return False
        
        if "time_of_last_update" not in data:
            print("❌ Ping response missing 'time_of_last_update' field")
            return False
        
        # Check status value
        if data["status"] not in ["Healthy", "HealthyBusy"]:
            print(f"❌ Invalid status value: {data['status']}")
            return False
        
        # Check timestamp is reasonable
        current_time = int(time.time())
        last_update = data["time_of_last_update"]
        
        if abs(current_time - last_update) > 300:  # 5 minutes tolerance
            print(f"❌ Timestamp seems incorrect: {last_update} vs {current_time}")
            return False
        
        print("✅ Ping endpoint compliant")
        return True
        
    except Exception as e:
        print(f"❌ Ping endpoint test failed: {str(e)}")
        return False


def test_invocations_endpoint(base_url: str = "http://localhost:8080") -> bool:
    """Test the /invocations endpoint compliance."""
    try:
        # Test request format as specified in documentation
        test_payload = {
            "prompt": "Hello, this is a test message for AgentCore compliance"
        }
        
        response = requests.post(
            f"{base_url}/invocations",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Invocations endpoint returned status {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        # Check if response is valid JSON
        try:
            data = response.json()
        except json.JSONDecodeError:
            print("❌ Invocations response is not valid JSON")
            return False
        
        # Check for required response fields according to AgentCore HTTP protocol
        if "response" not in data:
            print("❌ Invocations response missing 'response' field (required by AgentCore)")
            return False
        
        # Check for status field as shown in AgentCore examples
        if "status" not in data:
            print("❌ Invocations response missing 'status' field (recommended by AgentCore)")
            return False
        
        print("✅ Invocations endpoint compliant")
        print(f"Response preview: {str(data)[:200]}...")
        return True
        
    except Exception as e:
        print(f"❌ Invocations endpoint test failed: {str(e)}")
        return False


def test_container_requirements() -> bool:
    """Test container requirements compliance."""
    print("📋 Container Requirements Check:")
    print("  - Platform: ARM64 (check Dockerfile)")
    print("  - Host: 0.0.0.0 (check startup command)")
    print("  - Port: 8080 (check startup command)")
    return True


def main():
    """Run all compliance tests."""
    print("🔍 Testing AgentCore Runtime Compliance")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    
    # Test container requirements
    test_container_requirements()
    print()
    
    # Test ping endpoint
    ping_ok = test_ping_endpoint(base_url)
    print()
    
    # Test invocations endpoint
    invocations_ok = test_invocations_endpoint(base_url)
    print()
    
    # Summary
    print("=" * 50)
    if ping_ok and invocations_ok:
        print("✅ All AgentCore Runtime compliance tests passed!")
        return 0
    else:
        print("❌ Some compliance tests failed. Check the issues above.")
        return 1


if __name__ == "__main__":
    exit(main())
