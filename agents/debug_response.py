#!/usr/bin/env python3
"""
Debug the agent response to see the exact format.
"""

import requests
import json

def debug_response():
    """Debug the agent response format."""
    try:
        test_payload = {
            "prompt": "Necesito información del paciente Juan Pérez con cédula 12345678"
        }
        
        response = requests.post(
            "http://localhost:8080/invocations",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print("=== FULL RESPONSE ===")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            print("\n=== MESSAGE CONTENT ===")
            message = data.get('message', {})
            content = message.get('content', [])
            if content:
                text_content = content[0].get('text', '')
                print(f"Text content:\n{text_content}")
            
        else:
            print(f"Error: {response.status_code} - {response.text}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    debug_response()
