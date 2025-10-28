#!/usr/bin/env python3
"""
Simple test for patient lookup functionality.
"""

import requests
import json

def test_patient_lookup():
    """Test patient lookup with a simple request."""
    try:
        print("🔍 Testing patient lookup...")
        
        test_payload = {
            "prompt": "Necesito información del paciente Juan Pérez con cédula 12345678"
        }
        
        print("Sending request...")
        response = requests.post(
            "http://localhost:8080/invocations",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=60  # Longer timeout for LLM processing
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Request successful!")
            print(f"Message: {str(data.get('message', {}))[:300]}...")
            
            # Check patient context
            patient_context = data.get("patient_context", {})
            print(f"Patient Context: {patient_context}")
            
            # Check if tools are available
            session_info = data.get("session_info", {})
            tools = session_info.get("tools_available", [])
            print(f"Available Tools: {tools}")
            
            return True
        else:
            print(f"❌ Request failed: {response.text}")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_patient_lookup()
