#!/usr/bin/env python3
"""
Example usage of the synthetic medical data generator.

This script demonstrates how to use the structured output and multimodal
capabilities of the medical data generator.
"""

import json
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Demonstrate the medical data generator capabilities."""
    
    print("🏥 Synthetic Medical Data Generator Example")
    print("=" * 50)
    
    try:
        # Import components
        from bedrock_agent import MedicalDataAgent
        from data_loaders import FHIRDataLoader, CSVDataLoader, PDFTemplateLoader
        from profile_generator import PatientProfileGenerator
        from document_generator import MedicalDocumentGenerator
        from models import PatientProfile, DocumentNarratives
        
        # Load configuration
        print("📋 Loading configuration...")
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        # Initialize data loaders
        print("📊 Initializing data loaders...")
        fhir_loader = FHIRDataLoader(config['data_sources']['fhir_dir'])
        csv_loader = CSVDataLoader(config['data_sources']['csv_path'])
        template_loader = PDFTemplateLoader(config['data_sources']['template_dir'])
        
        # Initialize Bedrock agent
        print("🤖 Initializing AI agent...")
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
        
        # Initialize generators
        print("🏭 Initializing generators...")
        profile_generator = PatientProfileGenerator(
            fhir_loader=fhir_loader,
            csv_loader=csv_loader,
            agent=agent,
            template_dir=config['data_sources']['template_dir']
        )
        
        document_generator = MedicalDocumentGenerator(
            template_loader=template_loader,
            agent=agent
        )
        
        # Example 1: Generate a single patient with multimodal input
        print("\n🎯 Example 1: Generate Patient with Reference Scan")
        print("-" * 40)
        
        profile = profile_generator.generate_profile(use_reference_scan=True)
        
        print(f"✅ Generated patient: {profile['personal_info']['nombre_completo']}")
        print(f"   Age: {profile['personal_info']['edad']} years")
        print(f"   Gender: {'Male' if profile['personal_info']['sexo'] == 'M' else 'Female'}")
        print(f"   Medical conditions: {len(profile['medical_history']['conditions'])}")
        print(f"   Lab results: {len(profile['lab_results'])}")
        
        if profile.get('source_scan'):
            print(f"   📄 Reference scan used: {Path(profile['source_scan']).name}")
        
        # Example 2: Generate structured document narratives
        print("\n📝 Example 2: Generate Document Narratives")
        print("-" * 40)
        
        # Convert to PatientProfile model for structured output
        profile_model = PatientProfile.model_validate(profile)
        
        # Generate all narratives at once
        narratives_model = agent.generate_all_medical_narratives(
            profile=profile_model,
            document_types=['historia_clinica', 'resultados_laboratorio', 'receta_medica'],
            language="es-LA"
        )
        
        narratives = narratives_model.model_dump()
        
        print("✅ Generated structured narratives:")
        for doc_type, content in narratives.items():
            if content:
                print(f"   📋 {doc_type}: {len(content)} characters")
        
        # Example 3: Generate PDF documents
        print("\n📄 Example 3: Generate PDF Documents")
        print("-" * 40)
        
        output_dir = Path("example_output")
        output_dir.mkdir(exist_ok=True)
        
        generated_docs = []
        for doc_type in ['historia_clinica', 'resultados_laboratorio']:
            narrative = narratives.get(doc_type, f"Contenido no disponible para {doc_type}")
            
            doc_path = document_generator.generate_document(
                profile=profile,
                document_type=doc_type,
                output_path=str(output_dir),
                narrative=narrative
            )
            
            generated_docs.append(doc_path)
            print(f"✅ Generated: {Path(doc_path).name}")
        
        # Example 4: Analyze a scanned document (if available)
        print("\n🔍 Example 4: Analyze Scanned Document")
        print("-" * 40)
        
        template_dir = Path(config['data_sources']['template_dir'])
        if template_dir.exists():
            scan_files = list(template_dir.glob('*.jpg')) + list(template_dir.glob('*.png'))
            if scan_files:
                scan_path = str(scan_files[0])
                
                try:
                    analysis = agent.analyze_scanned_document(scan_path)
                    
                    print(f"✅ Analyzed scan: {Path(scan_path).name}")
                    print(f"   Document type: {analysis.document_type}")
                    print(f"   Patient name: {analysis.patient_name or 'Not visible'}")
                    print(f"   Medical conditions: {len(analysis.medical_conditions)}")
                    print(f"   Medications: {len(analysis.medications)}")
                    print(f"   Legibility score: {analysis.legibility_score:.2f}")
                    
                except Exception as e:
                    print(f"⚠️ Scan analysis failed: {e}")
            else:
                print("ℹ️ No scan files found for analysis")
        else:
            print("ℹ️ Template directory not found")
        
        print(f"\n🎉 Example completed successfully!")
        print(f"📁 Output saved to: {output_dir}")
        
    except Exception as e:
        print(f"❌ Example failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
