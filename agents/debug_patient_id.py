#!/usr/bin/env python3
"""
Debug patient ID extraction.
"""

import requests
import json

def debug_patient_id():
    """Debug patient ID extraction."""
    test_payload = {
        "prompt": "Esta sesión es del paciente Juan_Perez_123. Necesito revisar su historial médico."
    }
    
    response = requests.post(
        "http://localhost:8080/invocations",
        json=test_payload,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        patient_context = data.get("patient_context", {})
        print(f"Patient ID detected: '{patient_context.get('patient_id')}'")
        print(f"Has patient context: {patient_context.get('has_patient_context')}")
        print(f"Session prefix: {patient_context.get('session_prefix')}")
        
        # Test the extraction function directly
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from main import extract_patient_id_from_message
        
        test_message = "Esta sesión es del paciente Juan_Perez_123. Necesito revisar su historial médico."
        extracted = extract_patient_id_from_message(test_message)
        print(f"Direct extraction result: '{extracted}'")
        
    else:
        print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    debug_patient_id()
