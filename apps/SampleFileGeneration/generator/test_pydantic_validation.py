#!/usr/bin/env python3
"""
Test script for Pydantic validation handling.

This script tests that the PatientProfile model validation works correctly
and that our fallback mechanisms handle validation errors properly.
"""

import json
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_pydantic_model_structure():
    """Test that the PatientProfile model accepts valid data."""
    try:
        from models import PatientProfile, PersonalInfo, MedicalHistory, MedicalCondition, Medication, LabResult
        
        # Create a valid profile
        personal_info = PersonalInfo(
            nombre_completo="Test Patient García",
            primer_nombre="Test",
            segundo_nombre=None,
            primer_apellido="Patient",
            segundo_apellido="García",
            fecha_nacimiento="01/01/1980",
            edad=44,
            sexo="M",
            tipo_documento="DNI",
            numero_documento="12345678",
            direccion={
                "calle": "Calle Test",
                "numero": "123",
                "ciudad": "Test City",
                "provincia": "Test Province",
                "codigo_postal": "12345",
                "pais": "Colombia"
            },
            telefono="+57 300 1234567",
            email="test@example.com"
        )
        
        medical_history = MedicalHistory(
            conditions=[
                MedicalCondition(
                    codigo="E11.9",
                    descripcion="Diabetes mellitus tipo 2",
                    fecha_diagnostico="01/01/2020",
                    estado="activo"
                )
            ],
            medications=[
                Medication(
                    nombre="Metformina",
                    dosis="850 mg",
                    frecuencia="2 veces al día",
                    fecha_inicio="01/01/2020",
                    activo=True
                )
            ],
            procedures=[]  # Empty list should be fine
        )
        
        lab_results = [
            LabResult(
                nombre_prueba="Glucosa",
                valor="120",
                unidad="mg/dL",
                rango_referencia="70-100 mg/dL",
                fecha="15/01/2025",
                estado="anormal"
            )
        ]
        
        profile = PatientProfile(
            patient_id="test-123",
            personal_info=personal_info,
            medical_history=medical_history,
            lab_results=lab_results
        )
        
        logger.info("✅ Valid PatientProfile created successfully")
        logger.info(f"Profile ID: {profile.patient_id}")
        logger.info(f"Patient: {profile.personal_info.nombre_completo}")
        logger.info(f"Conditions: {len(profile.medical_history.conditions)}")
        logger.info(f"Medications: {len(profile.medical_history.medications)}")
        logger.info(f"Lab results: {len(profile.lab_results)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create valid PatientProfile: {e}")
        return False


def test_invalid_pydantic_data():
    """Test that invalid data properly raises validation errors."""
    try:
        from models import PatientProfile
        
        # Try to create a profile with None for required list fields
        invalid_data = {
            "patient_id": "test-invalid",
            "personal_info": {
                "nombre_completo": "Invalid Patient",
                "primer_nombre": "Invalid",
                "primer_apellido": "Patient",
                "segundo_apellido": "Test",
                "fecha_nacimiento": "01/01/1980",
                "edad": 44,
                "sexo": "M",
                "tipo_documento": "DNI",
                "numero_documento": "12345678",
                "direccion": {
                    "calle": "Test Street",
                    "numero": "123",
                    "ciudad": "Test City",
                    "provincia": "Test Province",
                    "codigo_postal": "12345",
                    "pais": "Colombia"
                },
                "telefono": "+57 300 1234567",
                "email": "test@example.com"
            },
            "medical_history": {
                "conditions": None,  # This should cause validation error
                "medications": None,  # This should cause validation error
                "procedures": None   # This should cause validation error
            },
            "lab_results": []
        }
        
        try:
            profile = PatientProfile.model_validate(invalid_data)
            logger.error("❌ Expected validation error but profile was created")
            return False
        except Exception as e:
            if "validation error" in str(e).lower() and "input should be a valid list" in str(e).lower():
                logger.info("✅ Validation error correctly caught for None list fields")
                logger.info(f"Error details: {e}")
                return True
            else:
                logger.error(f"❌ Unexpected error type: {e}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Test setup failed: {e}")
        return False


def test_fallback_profile_generation():
    """Test the fallback profile generation method."""
    try:
        from bedrock_agent import MedicalDataAgent
        
        # Create a minimal agent (we won't actually call Bedrock)
        agent = MedicalDataAgent(
            model_id="amazon.nova-micro-v1:0",
            region="us-east-1",
            max_tokens=1024,
            temperature=0.3
        )
        
        # Test fallback generation
        demographic_data = {
            "age": 45,
            "gender": "F"
        }
        
        profile = agent._generate_profile_fallback(demographic_data)
        
        logger.info("✅ Fallback profile generated successfully")
        logger.info(f"Profile ID: {profile.patient_id}")
        logger.info(f"Patient: {profile.personal_info.nombre_completo}")
        logger.info(f"Age: {profile.personal_info.edad}")
        logger.info(f"Gender: {profile.personal_info.sexo}")
        logger.info(f"Conditions: {len(profile.medical_history.conditions)}")
        logger.info(f"Medications: {len(profile.medical_history.medications)}")
        logger.info(f"Procedures: {len(profile.medical_history.procedures)}")
        logger.info(f"Lab results: {len(profile.lab_results)}")
        
        # Verify all required fields are present and valid
        assert profile.medical_history.conditions is not None
        assert profile.medical_history.medications is not None
        assert profile.medical_history.procedures is not None
        assert isinstance(profile.medical_history.conditions, list)
        assert isinstance(profile.medical_history.medications, list)
        assert isinstance(profile.medical_history.procedures, list)
        assert len(profile.medical_history.conditions) >= 1
        assert len(profile.medical_history.medications) >= 1
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fallback profile generation failed: {e}")
        return False


def main():
    """Run all Pydantic validation tests."""
    logger.info("Starting Pydantic validation tests...")
    
    # Check if we're in the right directory
    if not Path('models.py').exists():
        logger.error("❌ models.py not found. Please run from the generator directory.")
        sys.exit(1)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Valid model structure
    logger.info("\n" + "="*50)
    logger.info("TEST 1: Valid PatientProfile Structure")
    logger.info("="*50)
    
    if test_pydantic_model_structure():
        tests_passed += 1
        logger.info("✅ Test 1 PASSED")
    else:
        logger.error("❌ Test 1 FAILED")
    
    # Test 2: Invalid data handling
    logger.info("\n" + "="*50)
    logger.info("TEST 2: Invalid Data Validation")
    logger.info("="*50)
    
    if test_invalid_pydantic_data():
        tests_passed += 1
        logger.info("✅ Test 2 PASSED")
    else:
        logger.error("❌ Test 2 FAILED")
    
    # Test 3: Fallback generation
    logger.info("\n" + "="*50)
    logger.info("TEST 3: Fallback Profile Generation")
    logger.info("="*50)
    
    if test_fallback_profile_generation():
        tests_passed += 1
        logger.info("✅ Test 3 PASSED")
    else:
        logger.error("❌ Test 3 FAILED")
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("TEST SUMMARY")
    logger.info("="*50)
    logger.info(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        logger.info("🎉 All tests passed! Pydantic validation is working correctly.")
        return 0
    else:
        logger.error("❌ Some tests failed. Check the logs above for details.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
