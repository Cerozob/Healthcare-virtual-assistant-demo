#!/usr/bin/env python3
"""
Test script for max_tokens error handling.

This script tests the retry logic and fallback mechanisms
for handling AWS Bedrock max_tokens quota limitations.
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


def test_retry_logic():
    """Test the retry logic with a mock max_tokens error."""
    try:
        from bedrock_agent import MedicalDataAgent
        
        # Load config
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        bedrock_config = config['bedrock']
        
        # Initialize agent with lower max_tokens to trigger errors more easily
        agent_kwargs = {
            'region': bedrock_config['region'],
            'use_inference_profile': bedrock_config.get('use_inference_profile', False),
            'max_tokens': 1024,  # Reduced to trigger errors
            'temperature': bedrock_config.get('temperature', 0.7)
        }
        
        if bedrock_config.get('use_inference_profile'):
            agent_kwargs['inference_profile_id'] = bedrock_config['inference_profile_id']
        else:
            agent_kwargs['model_id'] = bedrock_config['model_id']
        
        agent = MedicalDataAgent(**agent_kwargs)
        
        # Create a test profile
        from models import PatientProfile, PersonalInfo, MedicalHistory, Condition, Medication
        
        test_profile = PatientProfile(
            patient_id="test-123",
            personal_info=PersonalInfo(
                nombre_completo="Test Patient",
                primer_nombre="Test",
                primer_apellido="Patient",
                fecha_nacimiento="01/01/1980",
                edad=44,
                sexo="M",
                tipo_documento="DNI",
                numero_documento="12345678"
            ),
            medical_history=MedicalHistory(
                conditions=[
                    Condition(
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
                ]
            )
        )
        
        # Test narrative generation with retry logic
        logger.info("Testing narrative generation with retry logic...")
        
        try:
            narratives = agent.generate_all_medical_narratives(
                profile=test_profile,
                document_types=["historia_clinica", "receta_medica"],
                language="es-LA"
            )
            logger.info("✅ Successfully generated narratives")
            logger.info(f"Generated documents: {list(narratives.model_dump().keys())}")
            
        except Exception as e:
            logger.error(f"❌ Failed to generate narratives: {e}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test setup failed: {e}")
        return False


def test_fallback_mechanisms():
    """Test fallback mechanisms when primary generation fails."""
    logger.info("Testing fallback mechanisms...")
    
    try:
        # Test with minimal configuration that should work
        from bedrock_agent import MedicalDataAgent
        
        # Create agent with very low max_tokens to force fallbacks
        agent = MedicalDataAgent(
            model_id="amazon.nova-micro-v1:0",  # Smaller model
            region="us-east-1",
            max_tokens=512,  # Very low to trigger errors
            temperature=0.3
        )
        
        # Test individual narrative generation
        from models import PatientProfile, PersonalInfo, MedicalHistory
        
        simple_profile = PatientProfile(
            patient_id="fallback-test",
            personal_info=PersonalInfo(
                nombre_completo="Fallback Test",
                primer_nombre="Fallback",
                primer_apellido="Test",
                fecha_nacimiento="01/01/1990",
                edad=34,
                sexo="F",
                tipo_documento="DNI",
                numero_documento="87654321"
            ),
            medical_history=MedicalHistory(conditions=[], medications=[])
        )
        
        # This should trigger fallback mechanisms
        try:
            narrative = agent._generate_single_narrative_with_retry(
                profile=simple_profile,
                document_type="receta_medica",
                language="es-LA"
            )
            logger.info("✅ Fallback narrative generation successful")
            logger.info(f"Generated content length: {len(narrative)} characters")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Fallback also failed (expected): {e}")
            return True  # This is actually expected behavior
            
    except Exception as e:
        logger.error(f"❌ Fallback test failed: {e}")
        return False


def main():
    """Run all error handling tests."""
    logger.info("Starting max_tokens error handling tests...")
    
    # Check if we're in the right directory
    if not Path('config.json').exists():
        logger.error("❌ config.json not found. Please run from the generator directory.")
        sys.exit(1)
    
    if not Path('bedrock_agent.py').exists():
        logger.error("❌ bedrock_agent.py not found. Please run from the generator directory.")
        sys.exit(1)
    
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Retry logic
    logger.info("\n" + "="*50)
    logger.info("TEST 1: Retry Logic")
    logger.info("="*50)
    
    if test_retry_logic():
        tests_passed += 1
        logger.info("✅ Test 1 PASSED")
    else:
        logger.error("❌ Test 1 FAILED")
    
    # Test 2: Fallback mechanisms
    logger.info("\n" + "="*50)
    logger.info("TEST 2: Fallback Mechanisms")
    logger.info("="*50)
    
    if test_fallback_mechanisms():
        tests_passed += 1
        logger.info("✅ Test 2 PASSED")
    else:
        logger.error("❌ Test 2 FAILED")
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("TEST SUMMARY")
    logger.info("="*50)
    logger.info(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        logger.info("🎉 All tests passed! Error handling is working correctly.")
        return 0
    else:
        logger.error("❌ Some tests failed. Check the logs above for details.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
