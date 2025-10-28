#!/usr/bin/env python3
"""
Test script for patient integration functionality.
Tests the patient lookup tool and agent integration.
"""

import sys
import os
import json
import logging
from datetime import datetime

# Add the agents directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.patient_lookup import extract_and_search_patient, get_patient_by_id, list_recent_patients

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_patient_extraction_and_search():
    """Test patient extraction and search functionality."""
    print("=" * 60)
    print("TESTING PATIENT EXTRACTION AND SEARCH")
    print("=" * 60)
    
    test_cases = [
        "Necesito información del paciente Juan Pérez",
        "Busca la cédula 12345678",
        "El paciente María González necesita una cita",
        "Revisa la historia clínica del paciente con cédula 87654321",
        "Agenda una cita para Carlos Rodríguez",
        "¿Qué información tienes sobre el paciente 11223344?",
        "Consulta general sin mencionar paciente específico"
    ]
    
    for i, test_message in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Input: {test_message}")
        
        try:
            result = extract_and_search_patient(test_message)
            print(f"Success: {result['success']}")
            
            if result['success']:
                patient = result['patient']
                print(f"Patient Found: {patient['full_name']} (ID: {patient['patient_id']})")
                print(f"Message: {result['message']}")
            else:
                print(f"Error: {result['error']}")
                
        except Exception as e:
            print(f"Exception: {str(e)}")
        
        print("-" * 40)

def test_direct_patient_lookup():
    """Test direct patient lookup by ID."""
    print("\n" + "=" * 60)
    print("TESTING DIRECT PATIENT LOOKUP")
    print("=" * 60)
    
    test_ids = ["12345678", "87654321", "11223344", "99999999"]
    
    for patient_id in test_ids:
        print(f"\n--- Looking up patient ID: {patient_id} ---")
        
        try:
            result = get_patient_by_id(patient_id)
            print(f"Success: {result['success']}")
            
            if result['success']:
                patient = result['patient']
                print(f"Patient: {patient['full_name']} (ID: {patient['patient_id']})")
            else:
                print(f"Error: {result['error']}")
                
        except Exception as e:
            print(f"Exception: {str(e)}")

def test_recent_patients():
    """Test listing recent patients."""
    print("\n" + "=" * 60)
    print("TESTING RECENT PATIENTS LIST")
    print("=" * 60)
    
    try:
        result = list_recent_patients(5)
        print(f"Success: {result['success']}")
        
        if result['success']:
            patients = result['patients']
            print(f"Found {len(patients)} recent patients:")
            for patient in patients:
                print(f"  - {patient['full_name']} (ID: {patient['patient_id']})")
        else:
            print(f"Error: {result['error']}")
            
    except Exception as e:
        print(f"Exception: {str(e)}")

def test_agent_response_format():
    """Test that agent responses include proper patient context."""
    print("\n" + "=" * 60)
    print("TESTING AGENT RESPONSE FORMAT")
    print("=" * 60)
    
    # Simulate what the agent would return
    test_message = "Busca información del paciente Juan Pérez"
    
    try:
        result = extract_and_search_patient(test_message)
        
        if result['success']:
            # Simulate the agent response structure
            agent_response = {
                "output": {
                    "message": result['message']
                },
                "patient_context": {
                    "patient_id": result['patient']['patient_id'],
                    "patient_name": result['patient']['full_name'],
                    "has_patient_context": True,
                    "patient_found": True,
                    "patient_data": {
                        "patient_id": result['patient']['patient_id'],
                        "full_name": result['patient']['full_name'],
                        "date_of_birth": result['patient'].get('date_of_birth', ''),
                        "created_at": result['patient'].get('created_at', ''),
                        "updated_at": result['patient'].get('updated_at', '')
                    }
                }
            }
            
            print("Agent Response Structure:")
            print(json.dumps(agent_response, indent=2, ensure_ascii=False))
            
            print("\nFrontend would receive:")
            print(f"- Patient ID: {agent_response['patient_context']['patient_id']}")
            print(f"- Patient Name: {agent_response['patient_context']['patient_name']}")
            print(f"- Auto-select: {agent_response['patient_context']['patient_found']}")
            
        else:
            print(f"No patient found: {result['error']}")
            
    except Exception as e:
        print(f"Exception: {str(e)}")

if __name__ == "__main__":
    print("PATIENT INTEGRATION TEST SUITE")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("Testing patient lookup functionality and agent integration...")
    
    test_patient_extraction_and_search()
    test_direct_patient_lookup()
    test_recent_patients()
    test_agent_response_format()
    
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETED")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Deploy the updated agent code")
    print("2. Test the frontend integration")
    print("3. Verify automatic patient selection in the UI")
