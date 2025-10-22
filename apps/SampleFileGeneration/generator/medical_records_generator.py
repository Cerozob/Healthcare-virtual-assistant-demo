#!/usr/bin/env python3
"""
Main application for synthetic medical data generation.

This script orchestrates the generation of synthetic patient profiles
and medical documents using AWS Bedrock and the Strands framework.
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from bedrock_agent import MedicalDataAgent
from data_loaders import FHIRDataLoader, CSVDataLoader, PDFTemplateLoader
from document_generator import MedicalDocumentGenerator
from profile_generator import PatientProfileGenerator


def setup_logging(log_level: str = "INFO") -> None:
    """Configure application logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('generator.log')
        ]
    )

    # Reduce noise from external libraries
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def load_config(config_path: str) -> Dict:
    """Load configuration from JSON file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        logging.info(f"Loaded configuration from {config_path}")
        return config

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in configuration file: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to load configuration: {e}")


def initialize_components(config: Dict) -> Dict:
    """Initialize all components and return component dictionary.

    Args:
        config: Configuration dictionary

    Returns:
        Dictionary containing initialized components
    """
    logging.info("Initializing components...")

    try:
        # Initialize data loaders
        fhir_loader = FHIRDataLoader(config['data_sources']['fhir_dir'])
        csv_loader = CSVDataLoader(config['data_sources']['csv_path'])
        template_loader = PDFTemplateLoader(
            config['data_sources']['template_dir'])

        # Initialize Bedrock agent
        bedrock_config = config['bedrock']
        use_inference_profile = bedrock_config.get(
            'use_inference_profile', False)

        agent_kwargs = {
            'region': bedrock_config['region'],
            'use_inference_profile': use_inference_profile,
            'max_tokens': bedrock_config.get('max_tokens', 4096),
            'temperature': bedrock_config.get('temperature', 0.7)
        }

        if use_inference_profile:
            agent_kwargs['inference_profile_id'] = bedrock_config['inference_profile_id']
        else:
            agent_kwargs['model_id'] = bedrock_config['model_id']

        agent = MedicalDataAgent(**agent_kwargs)

        # Initialize generators
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

        components = {
            'fhir_loader': fhir_loader,
            'csv_loader': csv_loader,
            'template_loader': template_loader,
            'agent': agent,
            'profile_generator': profile_generator,
            'document_generator': document_generator
        }

        logging.info("Successfully initialized all components")
        return components

    except Exception as e:
        logging.error(f"Failed to initialize components: {e}")
        raise


def generate_patient_end_to_end(
    patient_number: int,
    total_count: int,
    components: Dict,
    config: Dict
) -> Dict:
    """Generate a single patient end-to-end with profile and documents.

    Workflow: patient → intermediate → document → delete intermediate
    This approach provides fault tolerance by saving intermediate results.

    Args:
        patient_number: Current patient number (for logging)
        total_count: Total number of patients to generate
        components: Dictionary of initialized components
        config: Configuration dictionary

    Returns:
        Generated patient profile with documents
    """
    logging.info(f"Generating patient {patient_number}/{total_count}")

    profile_generator = components['profile_generator']
    document_generator = components['document_generator']
    document_types = config['generation']['document_types']
    output_dir = config['output']['base_dir']
    organize_by_patient = config['output'].get('organize_by_patient', True)

    # Create intermediate directory
    intermediate_dir = Path(output_dir) / '.intermediate'
    intermediate_dir.mkdir(parents=True, exist_ok=True)

    patient_id = None
    intermediate_file = None

    try:
        # Step 1: Generate patient profile
        logging.info(f"Patient {patient_number}: Generating profile...")
        profile = profile_generator.generate_profile()
        patient_id = profile.get('patient_id', f'patient_{patient_number}')

        # Step 2: Save to intermediate storage
        intermediate_file = intermediate_dir / \
            f"{patient_id}_intermediate.json"
        logging.info(
            f"Patient {patient_number}: Saving to intermediate storage...")

        with open(intermediate_file, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)

        # Step 3: Create final output directory
        if organize_by_patient:
            patient_output_dir = Path(output_dir) / patient_id
        else:
            patient_output_dir = Path(output_dir)

        patient_output_dir.mkdir(parents=True, exist_ok=True)

        # Step 4: Generate all document narratives in one call
        logging.info(f"Patient {patient_number}: Generating document narratives...")
        try:
            agent = components['agent']
            # Convert profile dict to PatientProfile model for structured output
            from models import PatientProfile
            profile_model = PatientProfile.model_validate(profile)
            narratives_model = agent.generate_all_medical_narratives(
                profile=profile_model,
                document_types=document_types,
                language="es-LA"
            )
            # Convert back to dict for compatibility
            narratives = narratives_model.model_dump()
            logging.info(f"Patient {patient_number}: Successfully generated narratives for {len(narratives)} document types")
        except Exception as e:
            logging.error(f"Patient {patient_number}: Failed to generate narratives: {e}")
            # Create fallback narratives to allow document generation to continue
            narratives = {}
            for doc_type in document_types:
                narratives[doc_type] = f"Contenido no disponible para {doc_type} debido a limitaciones técnicas temporales."
            logging.warning(f"Patient {patient_number}: Using fallback narratives to continue processing")

        # Step 5: Generate PDF documents using pre-generated narratives
        logging.info(f"Patient {patient_number}: Generating PDF documents...")
        generated_docs = []

        for doc_type in document_types:
            try:
                logging.info(
                    f"Patient {patient_number}: Creating PDF for {doc_type}...")
                
                # Get narrative for this document type
                narrative = narratives.get(doc_type, f"Contenido no disponible para {doc_type}")
                
                doc_path = document_generator.generate_document(
                    profile=profile,
                    document_type=doc_type,
                    output_path=str(patient_output_dir),
                    narrative=narrative
                )
                generated_docs.append({
                    'tipo': doc_type,
                    'ruta_archivo': doc_path,
                    'fecha_generacion': Path(doc_path).stat().st_mtime
                })

            except Exception as e:
                logging.error(
                    f"Patient {patient_number}: Failed to generate {doc_type}: {e}")
                continue

        # Step 6: Update profile with generated documents
        profile['generated_documents'] = generated_docs

        # Step 7: Copy reference scan if used
        if profile.get('source_scan'):
            try:
                import shutil
                source_scan_path = Path(profile['source_scan'])
                if source_scan_path.exists():
                    dest_scan_path = patient_output_dir / f"reference_scan{source_scan_path.suffix}"
                    shutil.copy2(source_scan_path, dest_scan_path)
                    logging.info(f"Patient {patient_number}: Copied reference scan to {dest_scan_path}")
                    # Update profile with relative path
                    profile['source_scan'] = str(dest_scan_path.name)
            except Exception as e:
                logging.warning(f"Patient {patient_number}: Failed to copy reference scan: {e}")

        # Step 8: Save final profile
        logging.info(f"Patient {patient_number}: Saving final profile...")
        if organize_by_patient:
            profile_path = patient_output_dir / f"{patient_id}_profile.json"
        else:
            profile_path = patient_output_dir / f"{patient_id}_profile.json"

        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)

        # Step 9: Clean up intermediate file
        if intermediate_file and intermediate_file.exists():
            logging.info(
                f"Patient {patient_number}: Cleaning up intermediate file...")
            intermediate_file.unlink()

        logging.info(
            f"Patient {patient_number}: Completed successfully - {len(generated_docs)} documents generated")
        return profile

    except Exception as e:
        logging.error(f"Patient {patient_number}: Failed to generate: {e}")
        # Keep intermediate file for recovery if it exists
        if intermediate_file and intermediate_file.exists():
            logging.info(
                f"Patient {patient_number}: Intermediate file preserved for recovery: {intermediate_file}")
        raise


def recover_intermediate_patients(
    components: Dict,
    config: Dict
) -> List[Dict]:
    """Recover and complete patients from intermediate storage.

    Args:
        components: Dictionary of initialized components
        config: Configuration dictionary

    Returns:
        List of recovered and completed patient profiles
    """
    output_dir = config['output']['base_dir']
    intermediate_dir = Path(output_dir) / '.intermediate'

    if not intermediate_dir.exists():
        logging.info("No intermediate directory found - nothing to recover")
        return []

    # Find all intermediate files
    intermediate_files = list(intermediate_dir.glob("*_intermediate.json"))

    if not intermediate_files:
        logging.info("No intermediate files found - nothing to recover")
        return []

    logging.info(
        f"Found {len(intermediate_files)} intermediate files to recover")

    recovered_profiles = []
    document_generator = components['document_generator']
    document_types = config['generation']['document_types']
    organize_by_patient = config['output'].get('organize_by_patient', True)

    for i, intermediate_file in enumerate(intermediate_files, 1):
        try:
            logging.info(
                f"Recovering patient {i}/{len(intermediate_files)}: {intermediate_file.name}")

            # Load intermediate profile
            with open(intermediate_file, 'r', encoding='utf-8') as f:
                profile = json.load(f)

            patient_id = profile.get('patient_id', 'unknown')

            # Create final output directory
            if organize_by_patient:
                patient_output_dir = Path(output_dir) / patient_id
            else:
                patient_output_dir = Path(output_dir)

            patient_output_dir.mkdir(parents=True, exist_ok=True)

            # Generate missing documents
            logging.info(
                f"Recovery {i}: Generating documents for {patient_id}...")
            generated_docs = []

            for doc_type in document_types:
                try:
                    logging.info(f"Recovery {i}: Generating {doc_type}...")
                    doc_path = document_generator.generate_document(
                        profile=profile,
                        document_type=doc_type,
                        output_path=str(patient_output_dir)
                    )
                    generated_docs.append({
                        'tipo': doc_type,
                        'ruta_archivo': doc_path,
                        'fecha_generacion': Path(doc_path).stat().st_mtime
                    })

                except Exception as e:
                    logging.error(
                        f"Recovery {i}: Failed to generate {doc_type}: {e}")
                    continue

            # Update profile with generated documents
            profile['generated_documents'] = generated_docs

            # Save final profile
            logging.info(f"Recovery {i}: Saving final profile...")
            if organize_by_patient:
                profile_path = patient_output_dir / \
                    f"{patient_id}_profile.json"
            else:
                profile_path = patient_output_dir / \
                    f"{patient_id}_profile.json"

            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2, ensure_ascii=False)

            # Clean up intermediate file
            intermediate_file.unlink()

            recovered_profiles.append(profile)
            logging.info(
                f"Recovery {i}: Successfully completed {patient_id} - {len(generated_docs)} documents generated")

        except Exception as e:
            logging.error(
                f"Recovery {i}: Failed to recover {intermediate_file.name}: {e}")
            continue

    logging.info(
        f"Recovery completed: {len(recovered_profiles)}/{len(intermediate_files)} patients recovered")
    return recovered_profiles


def generate_all_patients(
    count: int,
    components: Dict,
    config: Dict
) -> List[Dict]:
    """Generate specified number of patients one by one, end-to-end.

    Args:
        count: Number of patients to generate
        components: Dictionary of initialized components
        config: Configuration dictionary

    Returns:
        List of generated patient profiles
    """
    logging.info(f"Starting end-to-end generation of {count} patients")

    profiles = []
    successful_count = 0
    consecutive_failures = 0
    max_consecutive_failures = 3

    for i in range(1, count + 1):
        try:
            profile = generate_patient_end_to_end(i, count, components, config)
            profiles.append(profile)
            successful_count += 1
            consecutive_failures = 0  # Reset failure counter on success

            # Log progress
            logging.info(
                f"Progress: {successful_count}/{count} patients completed successfully")

        except Exception as e:
            consecutive_failures += 1
            logging.error(f"Failed to generate patient {i}: {e}")
            
            # If we have too many consecutive failures, add a longer delay
            if consecutive_failures >= max_consecutive_failures:
                delay = 30 + (consecutive_failures - max_consecutive_failures) * 10
                logging.warning(
                    f"Too many consecutive failures ({consecutive_failures}). "
                    f"Adding {delay}s delay before continuing..."
                )
                time.sleep(delay)
            
            # Continue with next patient instead of failing completely
            continue

    logging.info(
        f"Completed generation: {successful_count}/{count} patients successful")
    return profiles


def save_generation_summary(
    profiles: List[Dict],
    config: Dict
) -> None:
    """Save generation summary to disk.

    Args:
        profiles: List of generated patient profiles
        config: Configuration dictionary
    """
    logging.info(f"Saving generation summary for {len(profiles)} patients")

    output_dir = Path(config['output']['base_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Create summary
        summary = {
            'total_patients_requested': config.get('_requested_count', len(profiles)),
            'total_patients_generated': len(profiles),
            'generation_timestamp': datetime.now().isoformat(),
            'config_used': {k: v for k, v in config.items() if not k.startswith('_')},
            'patients': [
                {
                    'patient_id': p.get('patient_id'),
                    'name': p.get('personal_info', {}).get('nombre_completo'),
                    'documents_generated': len(p.get('generated_documents', []))
                }
                for p in profiles
            ]
        }

        summary_path = output_dir / 'generation_summary.json'
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logging.info(f"Generation summary saved to {summary_path}")

    except Exception as e:
        logging.error(f"Failed to save generation summary: {e}")
        raise


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description='Generate synthetic medical data using AWS Bedrock'
    )
    parser.add_argument(
        '--count', '-c',
        type=int,
        default=5,
        help='Number of patients to generate (default: 5, use 0 to only recover pending patients)'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.json',
        help='Path to configuration file (default: config.json)'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )

    parser.add_argument(
        '--recover-only',
        action='store_true',
        help='Only recover incomplete patients from intermediate storage, do not generate new patients'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)

    try:
        logging.info("Starting synthetic medical data generation")
        logging.info(f"Generating {args.count} patients")

        # Load configuration
        config = load_config(args.config)

        # Initialize components
        components = initialize_components(config)

        # Store requested count for summary
        config['_requested_count'] = args.count

        # First, try to recover any incomplete patients from intermediate storage
        logging.info("Checking for incomplete patients to recover...")
        recovered_profiles = recover_intermediate_patients(components, config)

        if recovered_profiles:
            logging.info(
                f"Recovered {len(recovered_profiles)} incomplete patients")

        # Generate patients based on options
        if args.recover_only or args.count == 0:
            # Only recover, don't generate new patients
            if args.count == 0:
                logging.info("Count is 0: only recovering pending patients")
            else:
                logging.info("Recovery-only mode: skipping new patient generation")
            profiles = []
            final_profiles = recovered_profiles
        else:
            # Normal end-to-end generation with structured output and multimodal
            profiles = generate_all_patients(args.count, components, config)
            # Combine recovered and newly generated profiles
            final_profiles = recovered_profiles + profiles

        if not final_profiles:
            logging.error("No patient profiles were generated")
            sys.exit(1)

        # Save generation summary
        save_generation_summary(final_profiles, config)

        logging.info(
            "Successfully completed synthetic medical data generation")
        logging.info(f"Total patients processed: {len(final_profiles)}")

        if recovered_profiles:
            logging.info(f"Recovered patients: {len(recovered_profiles)}")

        new_patients = len(final_profiles) - len(recovered_profiles)
        logging.info(f"Newly generated patients: {new_patients}")
        total_docs = sum(len(p.get('generated_documents', []))
                         for p in final_profiles)
        logging.info(f"Total medical documents: {total_docs}")
        
        # Count patients with reference scans
        patients_with_scans = sum(1 for p in final_profiles if p.get('source_scan'))
        logging.info(f"Patients generated with reference scans: {patients_with_scans}")

        print(f"\n✅ Successfully processed {len(final_profiles)} patients")
        if recovered_profiles:
            print(f"🔄 Recovered {len(recovered_profiles)} incomplete patients")
        print(f"📁 Output saved to: {config['output']['base_dir']}")

    except KeyboardInterrupt:
        logging.info("Generation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Generation failed: {e}")
        print(f"\n❌ Generation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
