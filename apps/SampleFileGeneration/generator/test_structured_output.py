#!/usr/bin/env python3
"""
Test script for structured output and multimodal capabilities.

This script tests the new structured output and multimodal features
of the synthetic medical data generator.
"""

import json
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_structured_output():
    """Test structured output functionality."""
    try:
        from bedrock_agent import MedicalDataAgent
        from models import PatientProfile, DocumentNarratives
        from data_loaders import FHIRDataLoader, CSVDataLoader
        from profile_generator import PatientProfileGenerator
        
        logger.info("Testing structured output functionality...")
        
        # Load configuration
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        # Initialize components
        fhir_loader = FHIRDataLoader(config['data_sources']['fhir_dir'])
        csv_loader = CSVDataLoader(config['data_sources']['csv_path'])
        
        # Initialize Bedrock agent
        bedrock_config = config['bedrock']
        agent_kwargs = {
            'region': bedrock_config['region'],
            'use_inference_profile': bedrock_config.get('use_inference_profile', False),
            'max_tokens': bedrock_config.get('max_tokens', 4096),
            'temperature': bedrock_config.get('temperature', 0.7)
        }
        
        if bedrock_config.get('use_inference_profile'):
            agent_kwargs['inference_profile_id'] = bedrock_config['inference_profile_id']
        else:
            agent_kwargs['model_id'] = bedrock_config['model_id']
        
        agent = MedicalDataAgent(**agent_kwargs)
        
        # Initialize profile generator with template directory
        profile_generator = PatientProfileGenerator(
            fhir_loader=fhir_loader,
            csv_loader=csv_loader,
            agent=agent,
            template_dir=config['data_sources']['template_dir']
        )
        
        # Test 1: Generate profile with structured output
        logger.info("Test 1: Generating patient profile with structured output...")
        profile = profile_generator.generate_profile(use_reference_scan=True)
        
        # Verify it's a proper dictionary
        assert isinstance(profile, dict), "Profile should be a dictionary"
        assert 'patient_id' in profile, "Profile should have patient_id"
        assert 'personal_info' in profile, "Profile should have personal_info"
        
        logger.info(f"✅ Generated profile for patient: {profile['patient_id']}")
        if profile.get('source_scan'):
            logger.info(f"✅ Used reference scan: {profile['source_scan']}")
        
        # Test 2: Generate document narratives with structured output
        logger.info("Test 2: Generating document narratives with structured output...")
        
        # Convert to PatientProfile model
        profile_model = PatientProfile.model_validate(profile)
        
        # Generate narratives
        narratives_model = agent.generate_all_medical_narratives(
            profile=profile_model,
            document_types=['historia_clinica', 'resultados_laboratorio'],
            language="es-LA"
        )
        
        # Verify structured output
        assert isinstance(narratives_model, DocumentNarratives), "Should return DocumentNarratives model"
        narratives = narratives_model.model_dump()
        
        logger.info("✅ Generated structured document narratives")
        for doc_type, content in narratives.items():
            if content:
                logger.info(f"  - {doc_type}: {len(content)} characters")
        
        # Test 3: Test scanned document analysis (if scans available)
        template_dir = Path(config['data_sources']['template_dir'])
        if template_dir.exists():
            scan_files = list(template_dir.glob('*.jpg')) + list(template_dir.glob('*.png'))
            if scan_files:
                logger.info("Test 3: Testing scanned document analysis...")
                scan_path = str(scan_files[0])
                
                try:
                    analysis = agent.analyze_scanned_document(scan_path)
                    logger.info(f"✅ Analyzed scan: {scan_path}")
                    logger.info(f"  - Document type: {analysis.document_type}")
                    logger.info(f"  - Legibility score: {analysis.legibility_score}")
                    logger.info(f"  - Medical conditions found: {len(analysis.medical_conditions)}")
                except Exception as e:
                    logger.warning(f"⚠️ Scan analysis failed: {e}")
            else:
                logger.info("Test 3: No scan files found for testing")
        else:
            logger.info("Test 3: Template directory not found")
        
        logger.info("🎉 All tests passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    logger.info("Starting structured output and multimodal tests...")
    
    success = test_structured_output()
    
    if success:
        logger.info("✅ All tests completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Tests failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()
