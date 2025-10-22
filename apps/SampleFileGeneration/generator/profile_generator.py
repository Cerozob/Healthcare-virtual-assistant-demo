"""
Profile generator module for synthetic medical data generation.

This module provides the PatientProfileGenerator class that creates
synthetic patient profiles by combining demographic data, medical history
samples, and AI-generated content.
"""

import logging
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from bedrock_agent import MedicalDataAgent
from data_loaders import FHIRDataLoader, CSVDataLoader
from models import PatientProfile, ScannedDocumentAnalysis

logger = logging.getLogger(__name__)


class PatientProfileGenerator:
    """Generates synthetic patient profiles."""
    
    def __init__(
        self,
        fhir_loader: FHIRDataLoader,
        csv_loader: CSVDataLoader,
        agent: MedicalDataAgent,
        template_dir: Optional[str] = None
    ):
        """Initialize with data loaders and Bedrock agent.
        
        Args:
            fhir_loader: FHIR data loader instance
            csv_loader: CSV data loader instance
            agent: Bedrock agent for content generation
            template_dir: Optional path to directory containing scanned medical documents
        """
        self.fhir_loader = fhir_loader
        self.csv_loader = csv_loader
        self.agent = agent
        self.template_dir = template_dir
        
        # Cache loaded data for performance
        self._fhir_data: Optional[Dict] = None
        
        logger.info("Initialized PatientProfileGenerator")
    
    def _load_fhir_data(self) -> Dict:
        """Load and cache FHIR data.
        
        Returns:
            Dictionary containing all FHIR data types
        """
        if self._fhir_data is None:
            logger.info("Loading FHIR data...")
            self._fhir_data = {
                'patients': self.fhir_loader.load_patients(),
                'conditions': self.fhir_loader.load_conditions(),
                'observations': self.fhir_loader.load_observations(),
                'medications': self.fhir_loader.load_medications(),
                'encounters': self.fhir_loader.load_encounters(),
                'procedures': self.fhir_loader.load_procedures()
            }
            
            # Log data counts
            for data_type, data_list in self._fhir_data.items():
                logger.info(f"Loaded {len(data_list)} {data_type} records")
        
        return self._fhir_data
    
    def generate_profile(self, patient_id: Optional[str] = None, use_reference_scan: bool = True) -> Dict:
        """Generate single patient profile.
        
        Args:
            patient_id: Optional patient ID, generates UUID if not provided
            use_reference_scan: Whether to use a reference scanned document for generation
            
        Returns:
            Generated patient profile dictionary
        """
        if patient_id is None:
            patient_id = str(uuid.uuid4())
        
        logger.info(f"Generating profile for patient {patient_id}")
        
        try:
            # Sample demographic data
            demographic_sample = self.csv_loader.sample_demographics(n=1)[0]
            
            # Generate personal information
            personal_info = self._generate_personal_info(demographic_sample)
            
            # Sample medical history based on age and gender
            medical_samples = self._sample_medical_history(
                age=personal_info['edad'],
                gender=personal_info['sexo']
            )
            
            # Analyze reference scan if requested and available
            scanned_analysis = None
            if use_reference_scan and self.template_dir:
                scan_path = self._get_random_scan_path()
                if scan_path:
                    try:
                        scanned_analysis = self.agent.analyze_scanned_document(scan_path)
                        logger.info(f"Analyzed reference scan: {scan_path}")
                    except Exception as e:
                        logger.warning(f"Failed to analyze scan {scan_path}: {e}")
            
            # Use Bedrock agent to generate coherent profile with structured output
            profile_model = self.agent.generate_patient_profile(
                demographic_data=personal_info,
                medical_samples=medical_samples,
                language="es-LA",
                scanned_analysis=scanned_analysis
            )
            
            # Convert Pydantic model to dictionary for compatibility
            profile = profile_model.model_dump()
            
            # Ensure patient ID is set
            profile['patient_id'] = patient_id
            
            # Note: Coherence is now ensured by structured output validation
            
            logger.info(f"Successfully generated profile for patient {patient_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Failed to generate profile for patient {patient_id}: {e}")
            raise
    
    def generate_batch(self, count: int) -> List[Dict]:
        """Generate multiple patient profiles.
        
        Args:
            count: Number of profiles to generate
            
        Returns:
            List of generated patient profiles
        """
        logger.info(f"Generating batch of {count} patient profiles")
        
        profiles = []
        for i in range(count):
            try:
                patient_id = str(uuid.uuid4())
                profile = self.generate_profile(patient_id)
                profiles.append(profile)
                
                logger.info(f"Generated profile {i+1}/{count}")
                
            except Exception as e:
                logger.error(f"Failed to generate profile {i+1}/{count}: {e}")
                # Continue with remaining profiles
                continue
        
        logger.info(f"Successfully generated {len(profiles)}/{count} profiles")
        return profiles
    
    def _generate_personal_info(self, demographic_sample: Dict) -> Dict:
        """Generate Latin American personal information.
        
        Args:
            demographic_sample: Sample demographic data from CSV
            
        Returns:
            Generated personal information dictionary
        """
        # Latin American first names
        male_names = [
            "José", "Luis", "Carlos", "Juan", "Miguel", "Antonio", "Francisco",
            "Alejandro", "Rafael", "Daniel", "Fernando", "Ricardo", "Eduardo",
            "Roberto", "Manuel", "Jorge", "Andrés", "Diego", "Pablo", "Pedro"
        ]
        
        female_names = [
            "María", "Ana", "Carmen", "Rosa", "Isabel", "Teresa", "Patricia",
            "Laura", "Claudia", "Sandra", "Mónica", "Adriana", "Gabriela",
            "Alejandra", "Beatriz", "Silvia", "Margarita", "Elena", "Cristina", "Lucía"
        ]
        
        # Latin American surnames
        surnames = [
            "García", "Rodríguez", "González", "Fernández", "López", "Martínez",
            "Sánchez", "Pérez", "Gómez", "Martín", "Jiménez", "Ruiz", "Hernández",
            "Díaz", "Moreno", "Álvarez", "Muñoz", "Romero", "Alonso", "Gutiérrez",
            "Navarro", "Torres", "Domínguez", "Vázquez", "Ramos", "Gil", "Ramírez",
            "Serrano", "Blanco", "Suárez", "Molina", "Morales", "Ortega", "Delgado",
            "Castro", "Ortiz", "Rubio", "Marín", "Sanz", "Iglesias", "Medina",
            "Garrido", "Cortés", "Castillo", "Santos", "Lozano", "Guerrero", "Cano"
        ]
        
        # Latin American countries
        countries = [
            "Argentina", "Bolivia", "Brasil", "Chile", "Colombia", "Costa Rica",
            "Cuba", "Ecuador", "El Salvador", "Guatemala", "Honduras", "México",
            "Nicaragua", "Panamá", "Paraguay", "Perú", "República Dominicana",
            "Uruguay", "Venezuela"
        ]
        
        # Determine gender and age from demographic sample
        gender = demographic_sample.get('Gender', random.choice(['Male', 'Female']))
        gender_code = 'M' if gender == 'Male' else 'F'
        
        age = demographic_sample.get('Age', random.randint(18, 85))
        if isinstance(age, str):
            try:
                age = int(age)
            except ValueError:
                age = random.randint(18, 85)
        
        # Generate names based on gender
        if gender_code == 'M':
            primer_nombre = random.choice(male_names)
        else:
            primer_nombre = random.choice(female_names)
        
        segundo_nombre = random.choice(male_names + female_names) if random.random() < 0.3 else None
        primer_apellido = random.choice(surnames)
        segundo_apellido = random.choice(surnames)
        
        # Generate full name
        nombre_completo = f"{primer_nombre}"
        if segundo_nombre:
            nombre_completo += f" {segundo_nombre}"
        nombre_completo += f" {primer_apellido} {segundo_apellido}"
        
        # Generate birth date
        today = datetime.now()
        birth_date = today - timedelta(days=age * 365 + random.randint(0, 365))
        fecha_nacimiento = birth_date.strftime("%d/%m/%Y")
        
        # Generate document info
        document_types = ["DNI", "Cédula", "Pasaporte"]
        tipo_documento = random.choice(document_types)
        numero_documento = f"{random.randint(10000000, 99999999)}"
        
        # Generate address
        country = random.choice(countries)
        ciudad = demographic_sample.get('City', f"Ciudad {random.randint(1, 100)}")
        
        # Generate contact info
        country_codes = {
            "Argentina": "+54", "Bolivia": "+591", "Brasil": "+55", "Chile": "+56",
            "Colombia": "+57", "Costa Rica": "+506", "Cuba": "+53", "Ecuador": "+593",
            "El Salvador": "+503", "Guatemala": "+502", "Honduras": "+504", "México": "+52",
            "Nicaragua": "+505", "Panamá": "+507", "Paraguay": "+595", "Perú": "+51",
            "República Dominicana": "+1", "Uruguay": "+598", "Venezuela": "+58"
        }
        
        country_code = country_codes.get(country, "+1")
        telefono = f"{country_code} {random.randint(100000000, 999999999)}"
        
        email_domain = random.choice(["gmail.com", "hotmail.com", "yahoo.com", "outlook.com"])
        email = f"{primer_nombre.lower()}.{primer_apellido.lower()}@{email_domain}"
        
        return {
            "nombre_completo": nombre_completo,
            "primer_nombre": primer_nombre,
            "segundo_nombre": segundo_nombre,
            "primer_apellido": primer_apellido,
            "segundo_apellido": segundo_apellido,
            "fecha_nacimiento": fecha_nacimiento,
            "edad": age,
            "sexo": gender_code,
            "tipo_documento": tipo_documento,
            "numero_documento": numero_documento,
            "direccion": {
                "calle": f"Calle {random.randint(1, 100)}",
                "numero": str(random.randint(1, 9999)),
                "ciudad": ciudad,
                "provincia": f"Provincia {random.randint(1, 20)}",
                "codigo_postal": f"{random.randint(10000, 99999)}",
                "pais": country
            },
            "telefono": telefono,
            "email": email
        }
    
    def _sample_medical_history(self, age: int, gender: str) -> Dict:
        """Sample appropriate medical history from FHIR data.
        
        Args:
            age: Patient age
            gender: Patient gender ('M' or 'F')
            
        Returns:
            Dictionary containing sampled medical data
        """
        fhir_data = self._load_fhir_data()
        
        # Sample conditions appropriate for age
        conditions = self._filter_conditions_by_age(fhir_data['conditions'], age)
        sampled_conditions = random.sample(
            conditions, 
            min(len(conditions), random.randint(1, 5))
        ) if conditions else []
        
        # Sample observations (lab results)
        observations = fhir_data['observations']
        sampled_observations = random.sample(
            observations,
            min(len(observations), random.randint(2, 8))
        ) if observations else []
        
        # Sample medications
        medications = fhir_data['medications']
        sampled_medications = random.sample(
            medications,
            min(len(medications), random.randint(1, 6))
        ) if medications else []
        
        # Sample procedures
        procedures = fhir_data['procedures']
        sampled_procedures = random.sample(
            procedures,
            min(len(procedures), random.randint(0, 3))
        ) if procedures else []
        
        # Sample encounters
        encounters = fhir_data['encounters']
        sampled_encounters = random.sample(
            encounters,
            min(len(encounters), random.randint(1, 4))
        ) if encounters else []
        
        return {
            'conditions': sampled_conditions,
            'observations': sampled_observations,
            'medications': sampled_medications,
            'procedures': sampled_procedures,
            'encounters': sampled_encounters
        }
    
    def _filter_conditions_by_age(self, conditions: List[Dict], age: int) -> List[Dict]:
        """Filter conditions appropriate for patient age.
        
        Args:
            conditions: List of condition records
            age: Patient age
            
        Returns:
            Filtered list of age-appropriate conditions
        """
        # Age-based condition filtering logic
        if age < 30:
            # Younger patients: fewer chronic conditions
            return [c for c in conditions if random.random() < 0.3]
        elif age < 50:
            # Middle-aged: moderate conditions
            return [c for c in conditions if random.random() < 0.6]
        else:
            # Older patients: more likely to have conditions
            return [c for c in conditions if random.random() < 0.8]
    

    
    def _get_random_scan_path(self) -> Optional[str]:
        """Get a random scanned document path from the template directory.
        
        Returns:
            Path to a random scanned document, or None if none found
        """
        if not self.template_dir:
            return None
        
        template_path = Path(self.template_dir)
        if not template_path.exists():
            logger.warning(f"Template directory does not exist: {self.template_dir}")
            return None
        
        # Find image and PDF files
        scan_files = []
        for pattern in ['*.jpg', '*.jpeg', '*.png', '*.pdf']:
            scan_files.extend(list(template_path.glob(pattern)))
        
        if not scan_files:
            logger.warning(f"No scan files found in template directory: {self.template_dir}")
            return None
        
        # Return random scan file
        selected_scan = random.choice(scan_files)
        return str(selected_scan)
