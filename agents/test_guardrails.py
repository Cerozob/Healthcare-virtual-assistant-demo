#!/usr/bin/env python3
"""
Test script for PII/PHI protection and guardrails functionality.
This script tests the guardrails implementation without requiring AWS credentials.
"""

import asyncio
import sys
import os

# Add the agents directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.guardrails import PIIProtectionManager, HealthcareComplianceManager


async def test_pii_detection():
    """Test PII detection functionality."""
    print("Testing PII/PHI Detection...")
    
    pii_manager = PIIProtectionManager()
    
    # Test cases with various PII/PHI content
    test_cases = [
        {
            "text": "El paciente Juan Pérez con cédula 12345678 tiene diabetes.",
            "expected_pii": True,
            "expected_phi": True
        },
        {
            "text": "Contactar al 555-123-4567 para más información.",
            "expected_pii": True,
            "expected_phi": False
        },
        {
            "text": "El diagnóstico indica hipertensión arterial.",
            "expected_pii": False,
            "expected_phi": True
        },
        {
            "text": "La reunión es mañana a las 10 AM.",
            "expected_pii": False,
            "expected_phi": False
        },
        {
            "text": "Email: paciente@ejemplo.com, SSN: 123-45-6789",
            "expected_pii": True,
            "expected_phi": False
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['text'][:50]}...")
        
        detection = pii_manager.detect_pii_phi(test_case["text"])
        
        print(f"  Has PII: {detection['has_pii']} (expected: {test_case['expected_pii']})")
        print(f"  Has PHI: {detection['has_phi']} (expected: {test_case['expected_phi']})")
        print(f"  Detected types: {detection['detected_types']}")
        
        # Validate expectations
        if detection['has_pii'] == test_case['expected_pii'] and detection['has_phi'] == test_case['expected_phi']:
            print("  ✅ PASS")
        else:
            print("  ❌ FAIL")


def test_sanitization():
    """Test data sanitization for logging."""
    print("\n\nTesting Data Sanitization...")
    
    pii_manager = PIIProtectionManager()
    
    # Test data with PII/PHI
    test_data = {
        "patient_id": "12345",
        "full_name": "Juan Pérez",
        "cedula": "87654321",
        "phone": "555-123-4567",
        "email": "juan@ejemplo.com",
        "age": 45,
        "diagnosis": "Diabetes tipo 2",
        "safe_field": "This is safe information",
        "nested_data": {
            "medical_history": "Sensitive medical information",
            "safe_nested": "This is also safe"
        },
        "list_data": [
            "Safe item",
            "Patient SSN: 123-45-6789",
            "Another safe item"
        ]
    }
    
    print("Original data keys:", list(test_data.keys()))
    
    sanitized = pii_manager.sanitize_for_logging(test_data)
    
    print("Sanitized data:")
    for key, value in sanitized.items():
        print(f"  {key}: {value}")
    
    # Check that sensitive fields are protected
    sensitive_fields = ['patient_id', 'full_name', 'cedula', 'phone', 'email']
    protected_count = sum(1 for field in sensitive_fields if str(sanitized.get(field, '')).startswith('[PROTECTED_'))
    
    print(f"\nProtected {protected_count}/{len(sensitive_fields)} sensitive fields")
    
    if protected_count == len(sensitive_fields):
        print("✅ Sanitization PASS")
    else:
        print("❌ Sanitization FAIL")


def test_response_validation():
    """Test response safety validation."""
    print("\n\nTesting Response Safety Validation...")
    
    pii_manager = PIIProtectionManager()
    
    test_responses = [
        {
            "response": "El paciente debe tomar la medicación según las indicaciones.",
            "should_be_safe": True
        },
        {
            "response": "El paciente Juan Pérez (cédula 12345678) debe contactar al 555-123-4567.",
            "should_be_safe": False
        },
        {
            "response": "Los resultados de laboratorio muestran niveles normales de glucosa.",
            "should_be_safe": True
        },
        {
            "response": "Contacte al paciente en juan.perez@email.com para seguimiento.",
            "should_be_safe": False
        }
    ]
    
    for i, test_case in enumerate(test_responses, 1):
        print(f"\nResponse Test {i}: {test_case['response'][:50]}...")
        
        validation = pii_manager.validate_response_safety(test_case["response"])
        
        print(f"  Safe: {validation['safe']} (expected: {test_case['should_be_safe']})")
        print(f"  Issues: {validation['issues']}")
        
        if validation['safe'] == test_case['should_be_safe']:
            print("  ✅ PASS")
        else:
            print("  ❌ FAIL")


async def test_compliance_manager():
    """Test the healthcare compliance manager."""
    print("\n\nTesting Healthcare Compliance Manager...")
    
    # Note: This will not actually call Bedrock Guardrails without proper configuration
    compliance_manager = HealthcareComplianceManager()
    
    test_input = "El paciente necesita programar una cita con el Dr. García."
    
    print(f"Testing input: {test_input}")
    
    try:
        # Process input
        input_result = await compliance_manager.process_user_input(test_input)
        
        print("Input processing result:")
        print(f"  Safe for processing: {input_result['safe_for_processing']}")
        print(f"  Guardrail applied: {input_result['guardrail_applied']}")
        print(f"  Should log: {input_result['should_log']}")
        
        # Process a sample response
        sample_response = "Su cita está programada para mañana a las 10 AM con el Dr. García."
        
        response_result = await compliance_manager.process_agent_response(sample_response)
        
        print("\nResponse processing result:")
        print(f"  Safe for output: {response_result['safe_for_output']}")
        print(f"  Guardrail applied: {response_result['guardrail_applied']}")
        
        # Get compliance summary
        summary = compliance_manager.get_compliance_summary()
        
        print("\nCompliance Summary:")
        print(f"  PII protection active: {summary['pii_protection_active']}")
        print(f"  PHI protection active: {summary['phi_protection_active']}")
        print(f"  Strict no-logging policy: {summary['strict_no_logging_policy']}")
        print(f"  Healthcare compliance mode: {summary['healthcare_compliance_mode']}")
        
        print("✅ Compliance Manager PASS")
        
    except Exception as e:
        print(f"❌ Compliance Manager FAIL: {str(e)}")


async def main():
    """Run all tests."""
    print("🔒 Healthcare Assistant - PII/PHI Protection & Guardrails Test")
    print("=" * 70)
    
    # Run tests
    await test_pii_detection()
    test_sanitization()
    test_response_validation()
    await test_compliance_manager()
    
    print("\n" + "=" * 70)
    print("🏁 Test completed!")
    print("\nNote: Bedrock Guardrails integration requires proper AWS configuration.")
    print("This test validates the PII/PHI protection logic without AWS calls.")


if __name__ == "__main__":
    asyncio.run(main())
