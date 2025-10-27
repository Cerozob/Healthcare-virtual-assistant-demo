#!/usr/bin/env python3
"""
Test script for Healthcare Assistant Agent
"""
import requests
import json
import time

def test_agent():
    base_url = "http://localhost:8080"
    
    # Test ping endpoint
    print("Testing /ping endpoint...")
    try:
        response = requests.get(f"{base_url}/ping", timeout=5)
        print(f"✅ Ping response: {response.json()}")
    except Exception as e:
        print(f"❌ Ping failed: {e}")
        return
    
    # Test invocations endpoint
    print("\nTesting /invocations endpoint...")
    try:
        payload = {
            "input": {
                "prompt": "Hola, ¿puedes ayudarme con información sobre citas médicas?"
            }
        }
        response = requests.post(
            f"{base_url}/invocations",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"✅ Invocation response: {response.json()}")
    except Exception as e:
        print(f"❌ Invocation failed: {e}")

if __name__ == "__main__":
    print("Healthcare Assistant Agent Test")
    print("=" * 40)
    test_agent()
