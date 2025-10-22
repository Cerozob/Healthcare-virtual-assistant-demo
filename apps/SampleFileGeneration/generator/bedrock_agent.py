"""
Bedrock agent module for medical data generation.

This module provides the MedicalDataAgent class that interfaces with AWS Bedrock
through the Strands framework to generate synthetic medical content.
"""

import base64
import json
import logging
import time
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from strands import Agent
from strands.models import BedrockModel
from strands_tools import image_reader

from models import PatientProfile, DocumentNarratives, ScannedDocumentAnalysis


logger = logging.getLogger(__name__)


class MedicalDataAgent:
    """Strands agent for medical data generation."""

    def __init__(
        self,
        model_id: Optional[str] = None,
        inference_profile_id: Optional[str] = None,
        region: str = "us-east-1",
        use_inference_profile: bool = False,
        **model_kwargs
    ):
        """Initialize Strands agent with Bedrock model or inference profile.

        Args:
            model_id: Bedrock model identifier (used when use_inference_profile=False)
            inference_profile_id: Bedrock inference profile identifier (used when use_inference_profile=True)
            region: AWS region for Bedrock service
            use_inference_profile: Whether to use inference profile instead of direct model
            **model_kwargs: Additional model configuration parameters
        """
        self.region = region
        self.use_inference_profile = use_inference_profile

        if use_inference_profile:
            if not inference_profile_id:
                raise ValueError(
                    "inference_profile_id is required when use_inference_profile=True")
            self.model_id = inference_profile_id
            model_identifier = inference_profile_id
            logger.info(
                f"Using Bedrock inference profile: {inference_profile_id}")
        else:
            if not model_id:
                raise ValueError(
                    "model_id is required when use_inference_profile=False")
            self.model_id = model_id
            model_identifier = model_id
            logger.info(f"Using Bedrock model: {model_id}")

        try:
            # Initialize Bedrock model with the appropriate identifier
            self.model = BedrockModel(
                model_id=model_identifier,
                region=region,
                **model_kwargs
            )

            # Initialize Strands agent with ImageReader tool
            self.agent = Agent(
                model=self.model,
                tools=[image_reader]
            )

            logger.info(
                f"Initialized MedicalDataAgent with {'inference profile' if use_inference_profile else 'model'} {model_identifier} in region {region}")

        except Exception as e:
            logger.error(f"Failed to initialize Bedrock agent: {e}")
            raise

    def analyze_scanned_document(self, image_path: str) -> ScannedDocumentAnalysis:
        """Analyze a scanned medical document using Strands image_reader tool.

        Args:
            image_path: Path to the scanned medical document image

        Returns:
            Structured analysis of the scanned document
        """
        try:
            # Create prompt that instructs the agent to use the image_reader tool
            prompt = f"""Analiza el documento médico escaneado en la ruta: {image_path}

Usa la herramienta image_reader para leer la imagen y extrae información médica relevante que puedas identificar.

Identifica si es posible:
1. Tipo de documento médico (historia clínica, resultados de laboratorio, receta médica, etc.)
2. Condiciones médicas mencionadas (solo si son claramente visibles)
3. Medicamentos listados (solo si son claramente visibles)
4. Valores de laboratorio (solo si son claramente visibles)
5. Hallazgos médicos clave (solo si son claramente visibles)
6. Idioma del documento

Nota: Este documento puede estar anonimizado. Si no puedes identificar información específica, está bien dejar los campos vacíos o como null.

Responde con la información estructurada basada en lo que puedas leer claramente de la imagen."""

            # Use structured output to get validated response
            analysis = self.agent.structured_output(
                ScannedDocumentAnalysis, prompt)

            # Store the source path in the analysis for later reference
            analysis.source_path = image_path

            return analysis

        except Exception as e:
            logger.error(
                f"Failed to analyze scanned document {image_path}: {e}")
            raise

    def _call_agent(self, prompt: str) -> str:
        """Call the agent with retry logic.

        Args:
            prompt: Input prompt for the agent

        Returns:
            Agent response text
        """
        try:
            response = self.agent(prompt)

            # Handle different response types
            if hasattr(response, 'message') and hasattr(response.message, 'content'):
                # AgentResult with message.content
                return response.message.content
            elif hasattr(response, 'content'):
                # Direct content attribute
                return response.content
            elif isinstance(response, dict):
                # Dictionary response - try common keys
                if 'content' in response:
                    return response['content']
                elif 'message' in response and isinstance(response['message'], dict):
                    return response['message'].get('content', str(response))
                elif 'text' in response:
                    return response['text']
                else:
                    # Fallback to string representation
                    return str(response)
            else:
                # Fallback to string representation
                return str(response)

        except Exception as e:
            logger.error(f"Agent call failed: {e}")
            raise

    def generate_patient_profile(
        self,
        demographic_data: Dict,
        medical_samples: Dict,
        language: str = "es-LA",
        scanned_analysis: Optional[ScannedDocumentAnalysis] = None
    ) -> PatientProfile:
        """Generate complete patient profile in specified language with retry logic.

        Args:
            demographic_data: Base demographic information
            medical_samples: Sample medical data from FHIR
            language: Target language (es-LA for Latin American Spanish)
            scanned_analysis: Optional analysis of scanned medical document to base profile on

        Returns:
            Generated patient profile as structured Pydantic model
        """
        # Build a structured prompt that ensures all required fields are populated
        if scanned_analysis:
            prompt = f"""
Genera un perfil médico completo en español latinoamericano basado en:

DOCUMENTO ESCANEADO:
- Tipo: {scanned_analysis.document_type}
- Condiciones: {', '.join(scanned_analysis.medical_conditions[:3]) if scanned_analysis.medical_conditions else 'Ninguna identificada'}
- Medicamentos: {', '.join(scanned_analysis.medications[:3]) if scanned_analysis.medications else 'Ninguno identificado'}

DATOS DEMOGRÁFICOS:
- Edad: {demographic_data.get('age', 'N/A')}
- Género: {demographic_data.get('gender', 'N/A')}

ESTRUCTURA REQUERIDA:
1. DATOS PERSONALES: nombre completo (dos apellidos), DNI/Cédula, fecha nacimiento (DD/MM/YYYY), dirección completa, teléfono, email
2. HISTORIAL MÉDICO: 
   - conditions: lista de condiciones médicas (mínimo 1, máximo 5)
   - medications: lista de medicamentos (mínimo 1, máximo 8) 
   - procedures: lista de procedimientos (puede estar vacía [])
3. RESULTADOS DE LABORATORIO: lista de 8-15 pruebas de laboratorio con valores, unidades, rangos de referencia

IMPORTANTE: Todas las listas deben ser arrays válidos, nunca null. Si no hay datos, usar array vacío [].
"""
        else:
            prompt = f"""
Genera un perfil médico completo en español latinoamericano para:

PACIENTE:
- Edad: {demographic_data.get('age', 'N/A')} años
- Género: {demographic_data.get('gender', 'N/A')}

ESTRUCTURA REQUERIDA:
1. DATOS PERSONALES: nombre completo (dos apellidos), DNI/Cédula, fecha nacimiento (DD/MM/YYYY), dirección completa, teléfono, email
2. HISTORIAL MÉDICO:
   - conditions: lista de 2-4 condiciones médicas apropiadas para la edad
   - medications: lista de 3-6 medicamentos coherentes con las condiciones
   - procedures: lista de 1-3 procedimientos médicos (puede estar vacía [])
3. RESULTADOS DE LABORATORIO: lista de 10-15 pruebas con valores normales/anormales coherentes

IMPORTANTE: 
- Todas las listas (conditions, medications, procedures, lab_results) deben ser arrays válidos, nunca null
- Si no hay datos para una lista, usar array vacío []
- Generar datos realistas y coherentes clínicamente
"""

        def _generate_profile():
            try:
                profile = self.agent.structured_output(PatientProfile, prompt)
                # Add source scan path if provided
                if scanned_analysis and hasattr(scanned_analysis, 'source_path'):
                    profile.source_scan = scanned_analysis.source_path
                return profile
            except Exception as e:
                # Check if this is a Pydantic validation error
                error_msg = str(e).lower()
                if 'validation error' in error_msg and 'input should be a valid list' in error_msg:
                    logger.warning(f"Pydantic validation error detected, likely incomplete structured output: {e}")
                    # This is a validation error, not a max_tokens error - don't retry with backoff
                    raise ValueError(f"Structured output validation failed: {e}")
                else:
                    # Re-raise other errors for normal retry handling
                    raise e

        try:
            # Use retry logic for max_tokens errors
            profile = self._retry_with_backoff(
                _generate_profile,
                max_retries=3,
                base_delay=1.5
            )
            return profile

        except ValueError as e:
            # Handle Pydantic validation errors separately
            if "Structured output validation failed" in str(e):
                logger.error(f"Structured output validation failed - trying fallback generation: {e}")
                return self._generate_profile_fallback(demographic_data, scanned_analysis)
            else:
                raise e
        except Exception as e:
            logger.error(f"Failed to generate patient profile after retries: {e}")
            raise

    def _generate_profile_fallback(
        self,
        demographic_data: Dict,
        scanned_analysis: Optional[ScannedDocumentAnalysis] = None
    ) -> PatientProfile:
        """Fallback method to generate a basic profile when structured output fails.
        
        Args:
            demographic_data: Base demographic information
            scanned_analysis: Optional scanned document analysis
            
        Returns:
            Basic PatientProfile with minimal required data
        """
        logger.info("Generating fallback profile with minimal structured data")
        
        try:
            from models import PatientProfile, PersonalInfo, MedicalHistory, MedicalCondition, Medication, LabResult
            import uuid
            from datetime import datetime, timedelta
            import random
            
            # Generate basic personal info
            age = demographic_data.get('age', random.randint(25, 75))
            gender = demographic_data.get('gender', random.choice(['M', 'F']))
            
            # Create minimal personal info
            personal_info = PersonalInfo(
                nombre_completo=f"Paciente {uuid.uuid4().hex[:8].title()}",
                primer_nombre="Paciente",
                segundo_nombre=None,
                primer_apellido=f"{uuid.uuid4().hex[:6].title()}",
                segundo_apellido=f"{uuid.uuid4().hex[:6].title()}",
                fecha_nacimiento=f"{random.randint(1, 28):02d}/{random.randint(1, 12):02d}/{2024 - age}",
                edad=age,
                sexo=gender,
                tipo_documento="DNI",
                numero_documento=f"{random.randint(10000000, 99999999)}",
                direccion={
                    "calle": f"Calle {random.randint(1, 100)}",
                    "numero": f"{random.randint(100, 9999)}",
                    "ciudad": f"Ciudad {random.randint(1, 50)}",
                    "provincia": f"Provincia {random.randint(1, 25)}",
                    "codigo_postal": f"{random.randint(10000, 99999)}",
                    "pais": "Colombia"
                },
                telefono=f"+57 {random.randint(300, 350)}{random.randint(1000000, 9999999)}",
                email=f"paciente{random.randint(1000, 9999)}@email.com"
            )
            
            # Create basic medical history with at least one condition and medication
            conditions = [
                MedicalCondition(
                    codigo="Z00.00",
                    descripcion="Examen médico general",
                    fecha_diagnostico=f"{random.randint(1, 28):02d}/{random.randint(1, 12):02d}/2023",
                    estado="activo"
                )
            ]
            
            medications = [
                Medication(
                    nombre="Paracetamol",
                    dosis="500 mg",
                    frecuencia="según necesidad",
                    fecha_inicio=f"{random.randint(1, 28):02d}/{random.randint(1, 12):02d}/2023",
                    activo=True
                )
            ]
            
            # Create basic lab results
            lab_results = [
                LabResult(
                    nombre_prueba="Hemoglobina",
                    valor="14.5",
                    unidad="g/dL",
                    rango_referencia="12.0-16.0 g/dL",
                    fecha="15/01/2025",
                    estado="normal"
                ),
                LabResult(
                    nombre_prueba="Glucosa",
                    valor="95",
                    unidad="mg/dL",
                    rango_referencia="70-100 mg/dL",
                    fecha="15/01/2025",
                    estado="normal"
                )
            ]
            
            medical_history = MedicalHistory(
                conditions=conditions,
                medications=medications,
                procedures=[]  # Empty list is fine
            )
            
            # Create the profile
            profile = PatientProfile(
                patient_id=str(uuid.uuid4()),
                personal_info=personal_info,
                medical_history=medical_history,
                lab_results=lab_results
            )
            
            # Add source scan if provided
            if scanned_analysis and hasattr(scanned_analysis, 'source_path'):
                profile.source_scan = scanned_analysis.source_path
            
            logger.info("Successfully generated fallback profile")
            return profile
            
        except Exception as e:
            logger.error(f"Failed to generate fallback profile: {e}")
            raise

    def _retry_with_backoff(self, func, *args, max_retries: int = 3, base_delay: float = 1.0, **kwargs):
        """Execute a function with exponential backoff retry logic for max_tokens errors.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
            **kwargs: Keyword arguments for the function
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries are exhausted
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check if this is a max_tokens related error
                if any(keyword in error_msg for keyword in [
                    'max_tokens', 'token limit', 'context length', 
                    'stop_reason: max_tokens', 'unrecoverable state'
                ]):
                    last_exception = e
                    
                    if attempt < max_retries:
                        # Calculate delay with exponential backoff and jitter
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        
                        logger.warning(
                            f"Max tokens error on attempt {attempt + 1}/{max_retries + 1}. "
                            f"Retrying in {delay:.2f} seconds. Error: {e}"
                        )
                        
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(
                            f"Max retries ({max_retries}) exhausted for max_tokens error: {e}"
                        )
                        break
                elif 'validation error' in error_msg and ('input should be a valid list' in error_msg or 'field required' in error_msg):
                    # This is a Pydantic validation error - don't retry, let it bubble up for special handling
                    logger.warning(f"Pydantic validation error detected - not retrying: {e}")
                    raise e
                else:
                    # For other non-retryable errors, don't retry
                    logger.error(f"Non-retryable error: {e}")
                    raise e
        
        # If we get here, all retries were exhausted
        raise last_exception

    def generate_all_medical_narratives(
        self,
        profile: PatientProfile,
        document_types: List[str],
        language: str = "es-LA"
    ) -> DocumentNarratives:
        """Generate all medical document narratives in a single call with retry logic.

        Args:
            profile: Patient profile Pydantic model
            document_types: List of document types to generate
            language: Target language

        Returns:
            Structured document narratives
        """
        document_templates = {
            "historia_clinica": "historia clínica completa",
            "resultados_laboratorio": "informe de resultados de laboratorio",
            "receta_medica": "receta médica",
            "informe_medico": "informe médico general"
        }

        # Build list of documents to generate
        docs_to_generate = []
        for doc_type in document_types:
            doc_description = document_templates.get(
                doc_type, "documento médico")
            docs_to_generate.append(f"- {doc_type}: {doc_description}")

        docs_list = "\n".join(docs_to_generate)

        # Create a structured prompt that ensures proper document generation
        active_conditions = [c.descripcion for c in profile.medical_history.conditions if c.estado == 'activo']
        active_medications = [f"{m.nombre} {m.dosis}" for m in profile.medical_history.medications if m.activo]
        
        prompt = f"""
Genera documentos médicos profesionales en español latinoamericano para:

PACIENTE: {profile.personal_info.nombre_completo} ({profile.personal_info.edad} años, {profile.personal_info.sexo})

CONDICIONES MÉDICAS ACTIVAS:
{', '.join(active_conditions) if active_conditions else 'Ninguna condición activa registrada'}

MEDICAMENTOS ACTUALES:
{', '.join(active_medications) if active_medications else 'Ningún medicamento activo'}

DOCUMENTOS REQUERIDOS:
{docs_list}

INSTRUCCIONES:
- Genera contenido profesional médico completo para cada documento
- Usa terminología médica apropiada en español
- Mantén coherencia con la información del paciente
- Incluye todas las secciones estándar para cada tipo de documento
- Formato profesional con fechas en DD/MM/YYYY

IMPORTANTE: Debes generar contenido para TODOS los documentos solicitados.
"""

        def _generate_narratives():
            return self.agent.structured_output(DocumentNarratives, prompt)

        try:
            # Use retry logic for max_tokens errors
            narratives = self._retry_with_backoff(
                _generate_narratives,
                max_retries=3,
                base_delay=2.0
            )
            return narratives

        except Exception as e:
            logger.error(f"Failed to generate medical narratives after retries: {e}")
            
            # Fallback: try generating documents individually
            logger.info("Attempting fallback: generating documents individually")
            return self._generate_narratives_individually(profile, document_types, language)

    def _generate_narratives_individually(
        self,
        profile: PatientProfile,
        document_types: List[str],
        language: str = "es-LA"
    ) -> DocumentNarratives:
        """Fallback method to generate documents individually when batch generation fails.
        
        Args:
            profile: Patient profile Pydantic model
            document_types: List of document types to generate
            language: Target language
            
        Returns:
            DocumentNarratives with individually generated content
        """
        logger.info("Generating documents individually as fallback")
        
        narratives_dict = {}
        
        for doc_type in document_types:
            try:
                logger.info(f"Generating individual document: {doc_type}")
                narrative = self._generate_single_narrative_with_retry(
                    profile, doc_type, language
                )
                narratives_dict[doc_type] = narrative
                
            except Exception as e:
                logger.error(f"Failed to generate {doc_type} individually: {e}")
                # Provide a minimal fallback content
                narratives_dict[doc_type] = f"Contenido no disponible para {doc_type} debido a limitaciones técnicas."
        
        # Create DocumentNarratives object with generated content
        return DocumentNarratives(**narratives_dict)

    def _generate_single_narrative_with_retry(
        self,
        profile: PatientProfile,
        document_type: str,
        language: str = "es-LA"
    ) -> str:
        """Generate a single document narrative with retry logic.
        
        Args:
            profile: Patient profile
            document_type: Type of document to generate
            language: Target language
            
        Returns:
            Generated narrative text
        """
        # Create a very concise prompt for individual document generation
        prompt = f"""
Genera un {document_type} conciso para:
Paciente: {profile.personal_info.nombre_completo}
Edad: {profile.personal_info.edad} años
Condiciones: {', '.join([c.descripcion for c in profile.medical_history.conditions[:3] if c.estado == 'activo'])}
Medicamentos: {', '.join([m.nombre for m in profile.medical_history.medications[:3] if m.activo])}

Formato profesional médico en español.
"""

        def _generate_single():
            response = self.agent(prompt)
            # Handle different response types
            if hasattr(response, 'message') and hasattr(response.message, 'content'):
                return response.message.content
            elif hasattr(response, 'content'):
                return response.content
            else:
                return str(response)

        return self._retry_with_backoff(
            _generate_single,
            max_retries=2,
            base_delay=1.0
        )

    def generate_medical_narrative(
        self,
        profile: PatientProfile,
        document_type: str,
        language: str = "es-LA"
    ) -> str:
        """Generate single medical document narrative text (fallback method).

        Args:
            profile: Patient profile Pydantic model
            document_type: Type of document to generate
            language: Target language

        Returns:
            Generated medical narrative text
        """
        # Use the batch method for single document
        narratives = self.generate_all_medical_narratives(
            profile, [document_type], language)
        return getattr(narratives, document_type, "Contenido no disponible")
