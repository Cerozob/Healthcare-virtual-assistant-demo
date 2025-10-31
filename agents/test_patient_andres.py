#!/usr/bin/env python3
"""
Test script to query patient "Andrés Navarro Muñoz"
"""

import requests
import json
import time

def test_patient_andres():
    """Test querying for patient Andrés Navarro Muñoz"""
    
    print("🏥 Testing Patient Query: Andrés Navarro Muñoz")
    print("=" * 80)
    
    # Test the healthcare orchestrator
    agent_url = "http://localhost:8080/invocations"
    headers = {"Content-Type": "application/json"}
    
    test_cases = [
        {
            "name": "Basic Patient Search",
            "prompt": "Busca información del paciente Andrés Navarro Muñoz",
            "timeout": 45
        },
        {
            "name": "Patient Search with Context",
            "prompt": "Necesito revisar el expediente médico de Andrés Navarro Muñoz, ¿qué información tienes?",
            "timeout": 45
        },
        {
            "name": "Patient Search by Full Name",
            "prompt": "¿Puedes encontrar al paciente llamado Andrés Navarro Muñoz en el sistema?",
            "timeout": 45
        },
        {
            "name": "Patient Medical History",
            "prompt": "Muéstrame el historial médico completo de Andrés Navarro Muñoz",
            "timeout": 50
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print("-" * 60)
        
        data = {"prompt": test_case["prompt"]}
        
        try:
            print(f"🔄 Request: {test_case['prompt']}")
            print(f"⏰ Timeout: {test_case['timeout']}s")
            
            start_time = time.time()
            response = requests.post(
                agent_url, 
                headers=headers, 
                json=data, 
                timeout=test_case["timeout"]
            )
            end_time = time.time()
            
            response.raise_for_status()
            
            result = response.json()
            actual_time = (end_time - start_time) * 1000
            
            print(f"✅ Status: {result.get('status')}")
            print(f"⏱️  Actual time: {actual_time:.0f}ms")
            print(f"📊 Performance: {result.get('performance', {}).get('total_time_ms', 0):.0f}ms")
            
            # Extract response text
            response_content = result.get('response', '')
            if isinstance(response_content, str) and response_content.startswith("{'role'"):
                import ast
                try:
                    parsed = ast.literal_eval(response_content)
                    if 'content' in parsed and parsed['content']:
                        actual_text = parsed['content'][0].get('text', '')
                        print(f"📝 Response length: {len(actual_text)} characters")
                        print(f"📄 Response preview: {actual_text[:400]}...")
                        
                        # Check for patient-specific indicators
                        patient_indicators = ['andrés', 'navarro', 'muñoz', 'paciente', 'expediente', 'historial']
                        found_indicators = [ind for ind in patient_indicators if ind.lower() in actual_text.lower()]
                        if found_indicators:
                            print(f"🎯 Patient indicators found: {', '.join(found_indicators)}")
                        
                        # Check for tool usage indicators
                        tool_indicators = ['herramienta', 'búsqueda', 'sistema', 'base de datos', 'encontrado']
                        found_tools = [tool for tool in tool_indicators if tool.lower() in actual_text.lower()]
                        if found_tools:
                            print(f"🔧 Tool usage indicators: {', '.join(found_tools)}")
                        
                except Exception as parse_error:
                    print(f"📝 Raw response: {response_content[:400]}...")
                    print(f"⚠️ Parse error: {parse_error}")
            else:
                print(f"📝 Response: {response_content}")
            
            # Check for patient context
            patient_context = result.get('patient_context', {})
            if patient_context.get('has_patient_context'):
                print(f"👤 Patient context detected:")
                print(f"   - Patient ID: {patient_context.get('patient_id', 'N/A')}")
                print(f"   - Patient Name: {patient_context.get('patient_name', 'N/A')}")
                print(f"   - Found: {patient_context.get('patient_found', False)}")
            else:
                print("👤 No patient context detected")
                
        except requests.exceptions.Timeout:
            print("⏰ Request timed out")
            print("   This might indicate:")
            print("   - MCP tools are being called (good!)")
            print("   - Complex patient search in progress")
            print("   - Database query taking time")
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        
        print("-" * 60)

    print("\n🎯 Expected Behavior:")
    print("  • Healthcare orchestrator should receive the request")
    print("  • Should use MCP tools to search for patient 'Andrés Navarro Muñoz'")
    print("  • Should call healthcare-patients-api__patients_api tool")
    print("  • Should return patient information if found")
    print("  • Should extract patient context automatically")
    print("  • Should handle Spanish characters correctly")
    print()
    print("📊 What to Look For:")
    print("  ✅ Response mentions patient search")
    print("  ✅ Tool usage indicators in response")
    print("  ✅ Patient context extraction")
    print("  ✅ Proper Spanish language handling")
    print("  ✅ Reasonable response times")

if __name__ == "__main__":
    test_patient_andres()
