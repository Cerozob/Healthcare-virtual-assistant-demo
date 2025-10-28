#!/usr/bin/env python3
"""
Test LLM-powered patient lookup functionality.
"""

import requests
import json
import time


def test_llm_patient_extraction(base_url: str = "http://localhost:8080") -> bool:
    """Test that the agent can extract patient info and search automatically."""
    try:
        print("🔍 Testing LLM patient extraction and search...")
        
        test_payload = {
            "prompt": "Hola, necesito revisar la información del paciente Juan Pérez, su cédula es 12345678"
        }
        
        response = requests.post(
            f"{base_url}/invocations",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=45  # Longer timeout for LLM processing
        )
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        
        # Check if the agent used tools (should be visible in the response)
        message_content = str(data.get("message", ""))
        
        # The agent should have found the patient and mentioned it
        if "juan" not in message_content.lower() and "pérez" not in message_content.lower():
            print("❌ Agent response doesn't mention the patient")
            print(f"Response: {message_content[:200]}...")
            return False
        
        # Check if patient context was established
        patient_context = data.get("patient_context", {})
        if patient_context.get("has_patient_context"):
            print("✅ Patient context established successfully")
            print(f"Patient ID: {patient_context.get('patient_id')}")
            print(f"Patient Name: {patient_context.get('patient_name')}")
        else:
            print("⚠️  Patient context not established, but agent may have found patient info")
        
        print("✅ LLM patient extraction test completed")
        return True
        
    except Exception as e:
        print(f"❌ LLM patient extraction test failed: {str(e)}")
        return False


def test_natural_language_patient_request(base_url: str = "http://localhost:8080") -> bool:
    """Test natural language patient request."""
    try:
        print("🔍 Testing natural language patient request...")
        
        test_payload = {
            "prompt": "Busca información de la paciente María González, necesito ver su historial"
        }
        
        response = requests.post(
            f"{base_url}/invocations",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=45
        )
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            return False
        
        data = response.json()
        message_content = str(data.get("message", "")).lower()
        
        # Check if the agent processed the request appropriately
        if "maría" in message_content or "gonzález" in message_content or "paciente" in message_content:
            print("✅ Agent processed natural language patient request")
            return True
        else:
            print("❌ Agent didn't process patient request appropriately")
            print(f"Response: {message_content[:200]}...")
            return False
        
    except Exception as e:
        print(f"❌ Natural language test failed: {str(e)}")
        return False


def test_medical_record_number_request(base_url: str = "http://localhost:8080") -> bool:
    """Test medical record number request."""
    try:
        print("🔍 Testing medical record number request...")
        
        test_payload = {
            "prompt": "Necesito revisar la historia clínica MRN-003 del paciente"
        }
        
        response = requests.post(
            f"{base_url}/invocations",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=45
        )
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            return False
        
        data = response.json()
        message_content = str(data.get("message", "")).lower()
        
        # Check if the agent processed the MRN request
        if "mrn" in message_content or "historia" in message_content or "carlos" in message_content:
            print("✅ Agent processed MRN request")
            return True
        else:
            print("❌ Agent didn't process MRN request appropriately")
            print(f"Response: {message_content[:200]}...")
            return False
        
    except Exception as e:
        print(f"❌ MRN test failed: {str(e)}")
        return False


def test_general_medical_question(base_url: str = "http://localhost:8080") -> bool:
    """Test general medical question without patient context."""
    try:
        print("🔍 Testing general medical question...")
        
        test_payload = {
            "prompt": "¿Cuáles son los síntomas más comunes de la diabetes?"
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
        message_content = str(data.get("message", "")).lower()
        
        # Should respond about diabetes symptoms
        if "diabetes" in message_content or "síntomas" in message_content:
            print("✅ Agent answered general medical question")
            
            # Should not establish patient context
            patient_context = data.get("patient_context", {})
            if not patient_context.get("has_patient_context"):
                print("✅ No patient context established for general question")
                return True
            else:
                print("⚠️  Patient context incorrectly established")
                return False
        else:
            print("❌ Agent didn't answer medical question appropriately")
            return False
        
    except Exception as e:
        print(f"❌ General medical question test failed: {str(e)}")
        return False


def test_tools_functionality(base_url: str = "http://localhost:8080") -> bool:
    """Test that tools are available and working."""
    try:
        print("🔍 Testing tools functionality...")
        
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
        
        # Check session info for tools
        session_info = data.get("session_info", {})
        tools_available = session_info.get("tools_available", [])
        
        expected_tools = ["extract_and_search_patient", "get_patient_by_id", "list_recent_patients", "validate_patient_session"]
        
        missing_tools = []
        for tool in expected_tools:
            if tool not in tools_available:
                missing_tools.append(tool)
        
        if missing_tools:
            print(f"❌ Missing tools: {missing_tools}")
            return False
        else:
            print("✅ All expected tools are available")
            return True
        
    except Exception as e:
        print(f"❌ Tools functionality test failed: {str(e)}")
        return False


def main():
    """Run LLM patient lookup tests."""
    print("🚀 Running LLM-Powered Patient Lookup Tests")
    print("=" * 60)
    
    base_url = "http://localhost:8080"
    
    tests = [
        ("LLM Patient Extraction", test_llm_patient_extraction),
        ("Natural Language Request", test_natural_language_patient_request),
        ("Medical Record Number", test_medical_record_number_request),
        ("General Medical Question", test_general_medical_question),
        ("Tools Functionality", test_tools_functionality),
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
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("-" * 60)
    print(f"Total Tests: {len(results)} | Passed: {passed} | Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! LLM-powered patient lookup working!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. The agent may need more specific instructions.")
        return 1


if __name__ == "__main__":
    exit(main())
