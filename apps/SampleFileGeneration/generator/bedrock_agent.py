"""
Bedrock agent module for medical data generation.

This module provides the MedicalDataAgent class that interfaces with AWS Bedrock
through the Strands framework to generate synthetic medical content.
"""

import base64
import json
import logging
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
        """Generate complete patient profile in specified language.

        Args:
            demographic_data: Base demographic information
            medical_samples: Sample medical data from FHIR
            language: Target language (es-LA for Latin American Spanish)
            scanned_analysis: Optional analysis of scanned medical document to base profile on

        Returns:
            Generated patient profile as structured Pydantic model
        """
        # Build prompt based on whether we have scanned document analysis
        if scanned_analysis:
            prompt = f"""
Genera un perfil completo de paciente médico en español latinoamericano basado en el análisis del documento escaneado y los datos adicionales:

ANÁLISIS DEL DOCUMENTO ESCANEADO:
- Tipo de documento: {scanned_analysis.document_type}
- Condiciones médicas: {', '.join(scanned_analysis.medical_conditions) if scanned_analysis.medical_conditions else 'Ninguna identificada'}
- Medicamentos: {', '.join(scanned_analysis.medications) if scanned_analysis.medications else 'Ninguno identificado'}
- Valores de laboratorio: {', '.join(scanned_analysis.lab_values) if scanned_analysis.lab_values else 'Ninguno identificado'}
- Hallazgos clave: {', '.join(scanned_analysis.key_findings) if scanned_analysis.key_findings else 'Ninguno identificado'}

DATOS DEMOGRÁFICOS ADICIONALES:
{json.dumps(demographic_data, indent=2, ensure_ascii=False)}

MUESTRAS MÉDICAS PARA REFERENCIA:
{json.dumps(medical_samples, indent=2, ensure_ascii=False)}

INSTRUCCIONES:
1. Usa la información del documento escaneado como base principal para el perfil médico
2. Complementa con información personal realista en formato latinoamericano (dos apellidos, DNI/Cédula, formato DD/MM/YYYY)
3. Mantén coherencia con las condiciones médicas identificadas en el documento
4. Genera resultados de laboratorio coherentes con las condiciones
5. Incluye medicamentos apropiados basados en el documento y las condiciones
6. Asegura coherencia clínica entre todos los elementos
7. Si el documento no tiene información clara, usa los datos demográficos y muestras médicas como respaldo

Genera un perfil médico completo y coherente basado en esta información.
"""
        else:
            prompt = f"""
Genera un perfil completo de paciente médico en español latinoamericano usando los siguientes datos base:

DATOS DEMOGRÁFICOS:
{json.dumps(demographic_data, indent=2, ensure_ascii=False)}

MUESTRAS MÉDICAS PARA REFERENCIA:
{json.dumps(medical_samples, indent=2, ensure_ascii=False)}

INSTRUCCIONES:
1. Crea información personal realista en formato latinoamericano (dos apellidos, DNI/Cédula, formato DD/MM/YYYY)
2. Selecciona condiciones médicas apropiadas para la edad y género del paciente
3. Genera resultados de laboratorio coherentes con las condiciones
4. Incluye medicamentos apropiados para las condiciones diagnosticadas
5. Asegura coherencia clínica entre todos los elementos

Genera un perfil médico completo y coherente.
"""

        try:
            # Use structured output for type-safe, validated response
            profile = self.agent.structured_output(PatientProfile, prompt)

            # Add source scan path if provided
            if scanned_analysis and hasattr(scanned_analysis, 'source_path'):
                profile.source_scan = scanned_analysis.source_path

            return profile

        except Exception as e:
            logger.error(f"Failed to generate patient profile: {e}")
            raise

    def generate_all_medical_narratives(
        self,
        profile: PatientProfile,
        document_types: List[str],
        language: str = "es-LA"
    ) -> DocumentNarratives:
        """Generate all medical document narratives in a single call.

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

        prompt = f"""
Genera TODOS los siguientes documentos médicos en español latinoamericano para el paciente:

PERFIL DEL PACIENTE:
{profile.model_dump_json(indent=2, ensure_ascii=False)}

DOCUMENTOS A GENERAR:
{docs_list}

INSTRUCCIONES:
1. Usa terminología médica apropiada en español latinoamericano
2. Incluye todas las secciones estándar para cada tipo de documento
3. Mantén coherencia con la información del perfil del paciente
4. Usa formato profesional médico
5. Incluye fechas en formato DD/MM/YYYY
6. Usa nombres de medicamentos en español cuando sea posible

Genera contenido completo y profesional para todos los documentos solicitados.
"""

        try:
            # Use structured output for type-safe, validated response
            narratives = self.agent.structured_output(
                DocumentNarratives, prompt)
            return narratives

        except Exception as e:
            logger.error(f"Failed to generate medical narratives: {e}")
            raise

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
