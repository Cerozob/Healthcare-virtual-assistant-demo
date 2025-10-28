#!/usr/bin/env python3
"""
Comprehensive final test for AgentCore compliance and state management.
"""

import requests
import json
import time
from typing import Dict, Any


def test_ping_endpoint(base_url: str = "http://localhost:8080") -> bool:
    """Test the /ping endpoint compliance."""
    try:
        print("🔍 Testing ping endpoint...")
        response = requests.get(f"{base_url}/ping", timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Ping endpoint returned status {response.status_code}")
            return False
        
        data = response.json()
        
        # Check required fields
        required_fields = ["status", "time_of_last_update"]
        for field in required_fields:
            if field not in data:
                print(f"❌ Ping response missing '{field}' field")
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


def test_invocations_basic(base_url: str = "http://localhost:8080") -> bool:
    """Test basic invocations endpoint functionality."""
    try:
        print("🔍 Testing basic invocations...")
        
        test_payload = {
            "prompt": "Hola, soy un médico y necesito ayuda con información general"
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
        
        data = response.json()
        
        # Check required response fields
        required_fields = ["message", "timestamp", "session_id", "patient_context"]
        for field in required_fields:
            if field not in data:
                print(f"❌ Response missing '{field}' field")
                return False
        
        # Check message structure
        if not isinstance(data["message"], dict) or "role" not in data["message"]:
            print("❌ Invalid message structure")
            return False
        
        # Check Spanish response (should respond in Spanish)
        message_content = str(data["message"])
        spanish_indicators = ["hola", "soy", "ayuda", "información", "médico", "salud"]
        if not any(indicator in message_content.lower() for indicator in spanish_indicators):
            print("⚠️  Warning: Response may not be in Spanish as expected")
        
        print("✅ Basic invocations test passed")
        return True
        
    except Exception as e:
        print(f"❌ Basic invocations test failed: {str(e)}")
        return False


def test_patient_context_detection(base_url: str = "http://localhost:8080") -> bool:
    """Test patient context detection and state management."""
    try:
        print("🔍 Testing patient context detection...")
        
        # Test with patient ID
        test_payload = {
            "prompt": "Esta sesión es del paciente Juan_Perez_123. Necesito revisar su historial médico."
        }
        
        response = requests.post(
            f"{base_url}/invocations",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Patient context test returned status {response.status_code}")
            return False
        
        data = response.json()
        
        # Check patient context detection
        patient_context = data.get("patient_context", {})
        if not patient_context.get("has_patient_context"):
            print("❌ Failed to detect patient context")
            return False
        
        if patient_context.get("patient_id") != "Juan_Perez_123":
            print(f"❌ Incorrect patient ID detected: {patient_context.get('patient_id')}")
            return False
        
        # Check session prefix structure
        expected_prefix = "processed/Juan_Perez_123_medical_notes/"
        if patient_context.get("session_prefix") != expected_prefix:
            print(f"❌ Incorrect session prefix: {patient_context.get('session_prefix')}")
            return False
        
        print("✅ Patient context detection test passed")
        return True
        
    except Exception as e:
        print(f"❌ Patient context test failed: {str(e)}")
        return False


def test_no_patient_context(base_url: str = "http://localhost:8080") -> bool:
    """Test handling when no patient context is provided."""
    try:
        print("🔍 Testing no patient context scenario...")
        
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
            print(f"❌ No patient context test returned status {response.status_code}")
            return False
        
        data = response.json()
        
        # Check that no patient context is detected
        patient_context = data.get("patient_context", {})
        if patient_context.get("has_patient_context"):
            print("❌ Incorrectly detected patient context when none provided")
            return False
        
        if patient_context.get("patient_id") != "unknown":
            print(f"❌ Expected 'unknown' patient ID, got: {patient_context.get('patient_id')}")
            return False
        
        # Check session prefix for unknown patient
        expected_prefix = "processed/unknown_medical_notes/"
        if patient_context.get("session_prefix") != expected_prefix:
            print(f"❌ Incorrect session prefix for unknown patient: {patient_context.get('session_prefix')}")
            return False
        
        print("✅ No patient context test passed")
        return True
        
    except Exception as e:
        print(f"❌ No patient context test failed: {str(e)}")
        return False


def test_session_consistency(base_url: str = "http://localhost:8080") -> bool:
    """Test session ID consistency and structure."""
    try:
        print("🔍 Testing session consistency...")
        
        # Test with explicit session ID
        session_id = "test_session_12345"
        test_payload = {
            "prompt": "Hola, necesito información sobre vacunas",
            "sessionId": session_id
        }
        
        response = requests.post(
            f"{base_url}/invocations",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Session consistency test returned status {response.status_code}")
            return False
        
        data = response.json()
        
        # Check session ID is preserved
        if data.get("session_id") != session_id:
            print(f"❌ Session ID not preserved: expected {session_id}, got {data.get('session_id')}")
            return False
        
        # Check session info structure
        session_info = data.get("session_info", {})
        required_session_fields = ["bucket", "region", "structure_pattern"]
        for field in required_session_fields:
            if field not in session_info:
                print(f"❌ Session info missing '{field}' field")
                return False
        
        print("✅ Session consistency test passed")
        return True
        
    except Exception as e:
        print(f"❌ Session consistency test failed: {str(e)}")
        return False


def test_response_format_compliance(base_url: str = "http://localhost:8080") -> bool:
    """Test that response format matches AgentCore requirements."""
    try:
        print("🔍 Testing response format compliance...")
        
        test_payload = {
            "prompt": "Test message for format compliance"
        }
        
        response = requests.post(
            f"{base_url}/invocations",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Response format test returned status {response.status_code}")
            return False
        
        # Check response is valid JSON
        try:
            data = response.json()
        except json.JSONDecodeError:
            print("❌ Response is not valid JSON")
            return False
        
        # Check response is not wrapped in "output" key (AgentCore expects direct response)
        if "output" in data and len(data) == 1:
            print("❌ Response incorrectly wrapped in 'output' key")
            return False
        
        # Check content type
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            print(f"❌ Incorrect content type: {content_type}")
            return False
        
        print("✅ Response format compliance test passed")
        return True
        
    except Exception as e:
        print(f"❌ Response format test failed: {str(e)}")
        return False


def main():
    """Run all comprehensive tests."""
    print("🚀 Running Comprehensive AgentCore Compliance and State Management Tests")
    print("=" * 80)
    
    base_url = "http://localhost:8080"
    
    tests = [
        ("Ping Endpoint", test_ping_endpoint),
        ("Basic Invocations", test_invocations_basic),
        ("Patient Context Detection", test_patient_context_detection),
        ("No Patient Context", test_no_patient_context),
        ("Session Consistency", test_session_consistency),
        ("Response Format Compliance", test_response_format_compliance),
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
        print("\n🎉 ALL TESTS PASSED! AgentCore compliance and state management verified!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the issues above.")
        return 1


if __name__ == "__main__":
    exit(main())
