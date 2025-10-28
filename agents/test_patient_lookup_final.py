#!/usr/bin/env python3
"""
Comprehensive test for patient lookup functionality and AgentCore compliance.
"""

import requests
import json
import time
from typing import Dict, Any


def test_patient_lookup_by_cedula(base_url: str = "http://localhost:8080") -> bool:
    """Test patient lookup by cedula."""
    try:
        print("🔍 Testing patient lookup by cedula...")
        
        test_payload = {
            "prompt": "Necesito información del paciente con cédula 12345678"
        }
        
        response = requests.post(
            f"{base_url}/invocations",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        
        # Check that patient context was established
        patient_context = data.get("patient_context", {})
        if not patient_context.get("has_patient_context"):
            print("❌ Patient context not established")
            return False
        
        if patient_context.get("patient_id") != "12345678":
            print(f"❌ Incorrect patient ID: {patient_context.get('patient_id')}")
            return False
        
        # Check that response mentions the patient
        message_str = str(data.get("message", ""))
        if "juan" not in message_str.lower() or "pérez" not in message_str.lower():
            print("❌ Response doesn't mention the correct patient")
            return False
        
        print("✅ Patient lookup by cedula successful")
        return True
        
    except Exception as e:
        print(f"❌ Patient lookup by cedula failed: {str(e)}")
        return False


def test_patient_lookup_by_name(base_url: str = "http://localhost:8080") -> bool:
    """Test patient lookup by name."""
    try:
        print("🔍 Testing patient lookup by name...")
        
        test_payload = {
            "prompt": "Busca información de la paciente María González"
        }
        
        response = requests.post(
            f"{base_url}/invocations",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            return False
        
        data = response.json()
        
        # Check that patient context was established
        patient_context = data.get("patient_context", {})
        if not patient_context.get("has_patient_context"):
            print("❌ Patient context not established")
            return False
        
        if patient_context.get("patient_id") != "87654321":
            print(f"❌ Incorrect patient ID: {patient_context.get('patient_id')}")
            return False
        
        # Check patient name
        if patient_context.get("patient_name") != "María González":
            print(f"❌ Incorrect patient name: {patient_context.get('patient_name')}")
            return False
        
        print("✅ Patient lookup by name successful")
        return True
        
    except Exception as e:
        print(f"❌ Patient lookup by name failed: {str(e)}")
        return False


def test_patient_lookup_by_mrn(base_url: str = "http://localhost:8080") -> bool:
    """Test patient lookup by medical record number."""
    try:
        print("🔍 Testing patient lookup by MRN...")
        
        test_payload = {
            "prompt": "Necesito ver la historia clínica MRN-003"
        }
        
        response = requests.post(
            f"{base_url}/invocations",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            return False
        
        data = response.json()
        
        # Check that patient context was established
        patient_context = data.get("patient_context", {})
        if not patient_context.get("has_patient_context"):
            print("❌ Patient context not established")
            return False
        
        if patient_context.get("patient_id") != "11223344":
            print(f"❌ Incorrect patient ID: {patient_context.get('patient_id')}")
            return False
        
        if patient_context.get("patient_name") != "Carlos Rodríguez":
            print(f"❌ Incorrect patient name: {patient_context.get('patient_name')}")
            return False
        
        print("✅ Patient lookup by MRN successful")
        return True
        
    except Exception as e:
        print(f"❌ Patient lookup by MRN failed: {str(e)}")
        return False


def test_no_patient_scenario(base_url: str = "http://localhost:8080") -> bool:
    """Test scenario with no patient mentioned."""
    try:
        print("🔍 Testing no patient scenario...")
        
        test_payload = {
            "prompt": "¿Cuáles son los síntomas comunes de la gripe?"
        }
        
        response = requests.post(
            f"{base_url}/invocations",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            return False
        
        data = response.json()
        
        # Check that no patient context was established
        patient_context = data.get("patient_context", {})
        if patient_context.get("has_patient_context"):
            print("❌ Patient context incorrectly established")
            return False
        
        if patient_context.get("patient_id") != "unknown":
            print(f"❌ Expected 'unknown' patient ID, got: {patient_context.get('patient_id')}")
            return False
        
        print("✅ No patient scenario handled correctly")
        return True
        
    except Exception as e:
        print(f"❌ No patient scenario test failed: {str(e)}")
        return False


def test_invalid_patient(base_url: str = "http://localhost:8080") -> bool:
    """Test lookup of non-existent patient."""
    try:
        print("🔍 Testing invalid patient lookup...")
        
        test_payload = {
            "prompt": "Busca información del paciente con cédula 99999999"
        }
        
        response = requests.post(
            f"{base_url}/invocations",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            return False
        
        data = response.json()
        
        # Check that no patient context was established
        patient_context = data.get("patient_context", {})
        if patient_context.get("has_patient_context"):
            print("❌ Patient context incorrectly established for invalid patient")
            return False
        
        # Check that response indicates patient not found
        message_str = str(data.get("message", "")).lower()
        if "no se encontró" not in message_str and "not found" not in message_str:
            print("❌ Response doesn't indicate patient not found")
            return False
        
        print("✅ Invalid patient lookup handled correctly")
        return True
        
    except Exception as e:
        print(f"❌ Invalid patient test failed: {str(e)}")
        return False


def test_tools_availability(base_url: str = "http://localhost:8080") -> bool:
    """Test that patient lookup tools are available."""
    try:
        print("🔍 Testing tools availability...")
        
        test_payload = {
            "prompt": "¿Qué herramientas tienes disponibles para buscar pacientes?"
        }
        
        response = requests.post(
            f"{base_url}/invocations",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            return False
        
        data = response.json()
        
        # Check that tools are listed in session_info
        session_info = data.get("session_info", {})
        tools_available = session_info.get("tools_available", [])
        
        expected_tools = ["search_patient", "get_patient_by_id", "list_recent_patients", "validate_patient_session"]
        for tool in expected_tools:
            if tool not in tools_available:
                print(f"❌ Missing expected tool: {tool}")
                return False
        
        print("✅ All patient lookup tools are available")
        return True
        
    except Exception as e:
        print(f"❌ Tools availability test failed: {str(e)}")
        return False


def test_agentcore_compliance(base_url: str = "http://localhost:8080") -> bool:
    """Test basic AgentCore compliance."""
    try:
        print("🔍 Testing AgentCore compliance...")
        
        # Test ping endpoint
        ping_response = requests.get(f"{base_url}/ping", timeout=10)
        if ping_response.status_code != 200:
            print(f"❌ Ping endpoint failed: {ping_response.status_code}")
            return False
        
        ping_data = ping_response.json()
        if "status" not in ping_data or "time_of_last_update" not in ping_data:
            print("❌ Ping endpoint missing required fields")
            return False
        
        # Test basic invocation
        test_payload = {"prompt": "Hola, soy un médico"}
        inv_response = requests.post(
            f"{base_url}/invocations",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if inv_response.status_code != 200:
            print(f"❌ Invocations endpoint failed: {inv_response.status_code}")
            return False
        
        inv_data = inv_response.json()
        required_fields = ["message", "timestamp", "session_id"]
        for field in required_fields:
            if field not in inv_data:
                print(f"❌ Missing required field: {field}")
                return False
        
        print("✅ AgentCore compliance verified")
        return True
        
    except Exception as e:
        print(f"❌ AgentCore compliance test failed: {str(e)}")
        return False


def main():
    """Run all patient lookup and compliance tests."""
    print("🚀 Running Patient Lookup and AgentCore Compliance Tests")
    print("=" * 80)
    
    base_url = "http://localhost:8080"
    
    tests = [
        ("AgentCore Compliance", test_agentcore_compliance),
        ("Patient Lookup by Cedula", test_patient_lookup_by_cedula),
        ("Patient Lookup by Name", test_patient_lookup_by_name),
        ("Patient Lookup by MRN", test_patient_lookup_by_mrn),
        ("No Patient Scenario", test_no_patient_scenario),
        ("Invalid Patient Lookup", test_invalid_patient),
        ("Tools Availability", test_tools_availability),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        try:
            result = test_func(base_url)
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("-" * 80)
    print(f"Total Tests: {len(results)} | Passed: {passed} | Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Patient lookup and AgentCore compliance verified!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the issues above.")
        return 1


if __name__ == "__main__":
    exit(main())
