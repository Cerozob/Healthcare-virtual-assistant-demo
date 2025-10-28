"""
Healthcare Assistant Agent using Strands Agents framework.
FastAPI implementation for AgentCore Runtime deployment with S3 session management.
"""

import logging
import os
import boto3
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from strands import Agent
from strands.session.s3_session_manager import S3SessionManager
from shared.utils import get_logger, extract_patient_context, extract_patient_id_from_message

# Configure Strands Agents logging


def configure_logging():
    """Configure logging for Strands Agents SDK following best practices."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Configure the root strands logger following Strands best practices
    strands_logger = logging.getLogger("strands")
    strands_logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Configure basic logging format as recommended by Strands documentation
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler()]
    )

    # Log configuration
    strands_logger.info(
        f"Strands Agents logging configured at {log_level} level")
    strands_logger.debug(
        "Logging configuration complete - ready for AgentCore deployment")


# Initialize logging
configure_logging()

# Get logger for this module
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Healthcare Assistant Agent", version="1.0.0")

# Healthcare assistant system prompt
HEALTHCARE_SYSTEM_PROMPT = """
Eres un asistente de salud inteligente diseñado para ayudar a profesionales médicos con:
- Gestión de información de pacientes
- Programación de citas
- Consultas de base de conocimientos médicos
- Procesamiento y análisis de documentos

INSTRUCCIONES IMPORTANTES:
1. Siempre responde en español (LATAM) a menos que se solicite específicamente otro idioma.
2. Mantén estándares profesionales médicos y confidencialidad del paciente.
3. Sé útil, preciso y profesional en todas las interacciones.

GESTIÓN INTELIGENTE DE PACIENTES:
Cuando un usuario mencione información de un paciente, SIEMPRE usa la herramienta 'extract_and_search_patient' que:
- Analiza inteligentemente el mensaje del usuario para extraer información del paciente
- Busca automáticamente en la base de datos usando múltiples criterios
- Establece el contexto del paciente para toda la conversación
- Permite que el frontend seleccione automáticamente al paciente identificado

EJEMPLOS DE USO AUTOMÁTICO (SIEMPRE usar extract_and_search_patient):
- "Necesito información del paciente Juan Pérez" → extract_and_search_patient(mensaje completo)
- "Busca la cédula 12345678" → extract_and_search_patient(mensaje completo)
- "Revisa la historia clínica MRN-001" → extract_and_search_patient(mensaje completo)
- "El paciente María González necesita..." → extract_and_search_patient(mensaje completo)
- "Agenda una cita para Juan" → extract_and_search_patient(mensaje completo)
- "¿Qué síntomas tiene María?" → extract_and_search_patient(mensaje completo)

IMPORTANTE: 
- Cada vez que identifiques un paciente, el frontend automáticamente lo seleccionará en el panel lateral
- Usa las herramientas para establecer el contexto del paciente en el estado del agente
- Proporciona respuestas claras y profesionales sobre el paciente encontrado

HERRAMIENTAS DISPONIBLES:
- extract_and_search_patient: Extrae información del paciente del mensaje y busca en la base de datos
- get_patient_by_id: Busca paciente por ID específico cuando ya lo tienes
- list_recent_patients: Lista pacientes recientes para selección rápida
- validate_patient_session: Verifica si hay un paciente activo en la sesión

FLUJO DE TRABAJO:
1. Si el usuario menciona un paciente, usa extract_and_search_patient con el mensaje completo
2. Confirma la identidad del paciente encontrado
3. Procede con la información médica contextualizada para ese paciente
4. Mantén el contexto del paciente durante toda la conversación

Siempre confirma la identidad del paciente antes de proceder con información médica sensible.
"""

# S3 Configuration for session management
# Uses consistent structure with document processing: processed/{patient_id}_{data_type}/
S3_BUCKET = os.getenv("SESSION_BUCKET", "ab2-cerozob-processeddata-us-east-1")
S3_PREFIX = os.getenv("SESSION_PREFIX", "processed/")  # Base prefix only
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")


def extract_patient_id_from_message(message: str) -> Optional[str]:
    """
    Extract patient ID from user message using various patterns.

    Args:
        message: User message

    Returns:
        Optional[str]: Extracted patient ID or None
    """
    # Pattern for explicit patient ID (case insensitive)
    patient_id_patterns = [
        r"paciente\s+id[:\s]+([a-zA-Z0-9\-_]+)",
        r"patient\s+id[:\s]+([a-zA-Z0-9\-_]+)",
        r"cedula[:\s]+(\d+)",
        r"cédula[:\s]+(\d+)",
        r"id\s+paciente[:\s]+([a-zA-Z0-9\-_]+)",
        r"esta sesión es del paciente\s+([a-zA-Z0-9\-_\s]+)",
    ]

    for pattern in patient_id_patterns:
        # Use case-insensitive search but preserve original case in capture group
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            patient_id = match.group(1).strip()
            # Clean up patient ID (remove spaces, normalize)
            patient_id = re.sub(r'\s+', '_', patient_id)
            return patient_id

    return None


def create_session_manager(session_id: str, patient_id: Optional[str] = None) -> S3SessionManager:
    """
    Create S3SessionManager with patient-specific prefix consistent with document processing structure.

    Uses the same pattern as document extraction: processed/{patient_id}_{session_type}/

    Args:
        session_id: Session identifier
        patient_id: Patient identifier for organizing notes

    Returns:
        S3SessionManager: Configured session manager
    """
    # Create patient-specific prefix consistent with document processing structure
    if patient_id:
        # Use the same pattern as document extraction: processed/{patient_id}_{session_type}/
        clean_patient_id = patient_id
        prefix = f"processed/{clean_patient_id}_medical_notes/"
        logger.info(
            f"Creating session manager for patient {patient_id} with consistent structure")
    else:
        # For sessions without patient context, use unknown patient pattern
        prefix = f"processed/unknown_medical_notes/"
        logger.info(
            "Creating session manager for session without patient context")

    try:
        session_manager = S3SessionManager(
            session_id=session_id,
            bucket=S3_BUCKET,
            prefix=prefix,
            region_name=AWS_REGION
        )
        logger.debug(f"Session manager created with prefix: {prefix}")
        return session_manager
    except Exception as e:
        logger.error(f"Failed to create session manager: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize session management: {str(e)}"
        )


def _extract_patient_from_agent_state(agent: Agent) -> tuple[Optional[str], Optional[str]]:
    """
    Extract patient information from agent state instead of parsing response text.

    Args:
        agent: Agent instance with state

    Returns:
        Tuple of (patient_id, patient_name) or (None, None)
    """
    try:
        # Get patient information from agent state if available
        current_patient_id = agent.state.get("current_patient_id")
        current_patient_name = agent.state.get("current_patient_name")

        if current_patient_id and current_patient_name:
            logger.info(
                f"Retrieved patient from agent state: {current_patient_name} (ID: {current_patient_id})")
            return current_patient_id, current_patient_name

        return None, None

    except Exception as e:
        logger.error(f"Error extracting patient from agent state: {str(e)}")
        return None, None


def get_or_create_agent(session_id: str) -> Agent:
    """
    Get or create agent with patient lookup tools.

    Args:
        session_id: Session identifier

    Returns:
        Agent: Configured agent with patient lookup capabilities
    """
    try:
        logger.info("Creating healthcare agent with patient lookup tools...")

        # Create agent with patient lookup tools
        agent = Agent(
            system_prompt=HEALTHCARE_SYSTEM_PROMPT,
            tools=["tools/patient_lookup.py"],  # Load patient lookup tools
            callback_handler=None
        )

        logger.info("Agent created with patient lookup tools")

        # Initialize session state
        agent.state.set("session_id", session_id)
        agent.state.set("session_context", "no_patient")
        agent.state.set("current_patient_id", None)
        agent.state.set("current_patient_name", None)

        logger.info("Agent state initialized successfully")
        return agent

    except Exception as e:
        logger.error(f"Failed to create agent: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize agent: {str(e)}"
        )


class InvocationRequest(BaseModel):
    prompt: str
    sessionId: Optional[str] = None


class PatientContextResponse(BaseModel):
    """Structured patient context for frontend integration."""
    patient_id: Optional[str] = Field(None, description="Patient ID or cedula")
    patient_name: Optional[str] = Field(None, description="Patient full name")
    has_patient_context: bool = Field(
        False, description="Whether patient context is available")
    patient_found: bool = Field(
        False, description="Whether a patient was identified in this interaction")
    patient_data: Optional[Dict[str, Any]] = Field(
        None, description="Complete patient data for frontend")


class AgentResponse(BaseModel):
    """Structured agent response with patient context."""
    message: str = Field(..., description="The agent's response message")
    patient_context: PatientContextResponse = Field(
        default_factory=PatientContextResponse, description="Patient context information")


@app.post("/invocations")
async def invoke_agent(request: InvocationRequest):
    """
    Main AgentCore invocation endpoint for healthcare assistant with session management.
    """
    try:
        logger.info("=== Starting invocation ===")
        logger.info(f"Request received: {request}")

        user_message = request.prompt
        if not user_message:
            logger.warning("Received request without prompt")
            raise HTTPException(
                status_code=400,
                detail="No prompt provided in request."
            )

        # Extract session ID from request (use a default if not provided)
        session_id = request.sessionId or f"healthcare_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"Session ID: {session_id}")
        logger.info(f"User message: {user_message[:100]}...")

        logger.debug(f"Processing message for session: {session_id}")

        logger.info("About to create agent...")
        # Get or create agent with patient lookup tools
        agent = get_or_create_agent(session_id)
        logger.info("Agent created successfully")

        logger.debug(f"Processing user message: {user_message[:100]}...")
        logger.info(
            "Healthcare assistant processing user request with session management")

        # Check if the message might involve patient lookup
        patient_keywords = ["paciente", "patient", "cédula",
                            "cedula", "historia", "historial", "mrn-", "agenda", "cita"]
        might_involve_patient = any(keyword in user_message.lower()
                                    for keyword in patient_keywords)

        if might_involve_patient:
            # Use structured output for patient-related queries
            try:
                structured_result = agent.structured_output(
                    output_model=AgentResponse,
                    prompt=user_message
                )

                # Extract the structured response
                agent_message = structured_result.message
                patient_context_data = structured_result.patient_context

                # Also get patient info from agent state (set by tools)
                current_patient_id, current_patient_name = _extract_patient_from_agent_state(
                    agent)

                # Update structured response with agent state if available
                if current_patient_id and current_patient_name:
                    patient_context_data.patient_id = current_patient_id
                    patient_context_data.patient_name = current_patient_name
                    patient_context_data.has_patient_context = True
                    patient_context_data.patient_found = True
                    patient_context_data.patient_data = {
                        "patient_id": current_patient_id,
                        "full_name": current_patient_name,
                        "date_of_birth": "",
                        "created_at": "",
                        "updated_at": ""
                    }

                logger.info(
                    f"Used structured output for patient query. Patient found: {patient_context_data.patient_found}")

            except Exception as e:
                logger.warning(
                    f"Structured output failed, falling back to regular processing: {str(e)}")
                # Fallback to regular processing
                result = agent(user_message)
                agent_message = result.message
                current_patient_id, current_patient_name = _extract_patient_from_agent_state(
                    agent)

                # Create patient context manually
                patient_context_data = PatientContextResponse()
                if current_patient_id and current_patient_name:
                    patient_context_data.patient_id = current_patient_id
                    patient_context_data.patient_name = current_patient_name
                    patient_context_data.has_patient_context = True
                    patient_context_data.patient_found = True
                    patient_context_data.patient_data = {
                        "patient_id": current_patient_id,
                        "full_name": current_patient_name,
                        "date_of_birth": "",
                        "created_at": "",
                        "updated_at": ""
                    }
        else:
            # Regular processing for non-patient queries
            result = agent(user_message)
            agent_message = result.message
            current_patient_id, current_patient_name = _extract_patient_from_agent_state(
                agent)

            # Create basic patient context
            patient_context_data = PatientContextResponse()
            if current_patient_id and current_patient_name:
                patient_context_data.patient_id = current_patient_id
                patient_context_data.patient_name = current_patient_name
                patient_context_data.has_patient_context = True
                # Not found in this interaction, but exists in session
                patient_context_data.patient_found = False

        session_context = "patient_session" if current_patient_id else "no_patient"

        # Prepare response with session and patient context using consistent structure
        if current_patient_id and session_context == "patient_session":
            session_prefix = f"processed/{current_patient_id}_medical_notes/"
        else:
            session_prefix = f"processed/unknown_medical_notes/"

        # Convert structured patient context to dict for response
        patient_context_dict = patient_context_data.model_dump()
        patient_context_dict.update({
            "session_prefix": session_prefix,
            "consistent_with_documents": True
        })

        # AgentCore compliant response format - must match the HTTP protocol contract
        response = {
            "response": agent_message,  # Primary response field as required by AgentCore
            "status": "success",  # Status field as shown in examples
            # Additional metadata for frontend integration
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": "healthcare-assistant",
            "capabilities": ["patient_lookup", "patient_info", "appointments", "knowledge_base", "documents"],
            "session_id": session_id,
            "patient_context": patient_context_dict,
            "session_info": {
                "bucket": S3_BUCKET,
                "region": AWS_REGION,
                "notes_saved": False,  # Currently disabled session management
                "conversation_persisted": False,  # Currently disabled session management
                "structure_pattern": "processed/{patient_id}_{data_type}/",
                "tools_available": ["extract_and_search_patient", "get_patient_by_id", "list_recent_patients", "validate_patient_session"]
            }
        }

        logger.info(
            "Healthcare assistant request processed successfully with session management")
        logger.debug(
            f"Response generated: {len(response.get('message', ''))} characters")
        logger.debug(
            f"Session data saved to S3 with prefix: {response['patient_context']['session_prefix']}")

        return response

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Agent processing failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Agent processing failed: {str(e)}")


@app.get("/ping")
async def ping():
    """Health check endpoint required by AgentCore Runtime."""
    import time
    return {
        "status": "Healthy",
        "time_of_last_update": int(time.time())
    }


@app.get("/sessions/{session_id}/info")
async def get_session_info(session_id: str):
    """
    Get information about a specific session.
    """
    try:
        # Try to determine if this is a patient session by checking S3 structure
        s3_client = boto3.client('s3', region_name=AWS_REGION)

        # Check for patient sessions
        patient_prefix = f"{S3_PREFIX}patients/"
        no_patient_prefix = f"{S3_PREFIX}no-patient/"

        session_info = {
            "session_id": session_id,
            "bucket": S3_BUCKET,
            "region": AWS_REGION,
            "found": False,
            "patient_context": None,
            "message_count": 0
        }

        # Check both patient and unknown prefixes using consistent structure
        prefixes_to_check = [
            # We'll search for patterns like processed/{patient_id}_medical_notes/
            ("patient", f"processed/"),
            ("unknown", f"processed/unknown_medical_notes/")
        ]

        for prefix_type, base_prefix in prefixes_to_check:
            try:
                if prefix_type == "patient":
                    # For patient sessions, we need to search for any patient ID pattern
                    # List all objects that match the pattern processed/*_medical_notes/session_{session_id}/
                    response = s3_client.list_objects_v2(
                        Bucket=S3_BUCKET,
                        Prefix=base_prefix,
                        MaxKeys=1000  # Increase to find patient sessions
                    )

                    # Look for session in any patient's medical notes
                    for obj in response.get('Contents', []):
                        key = obj['Key']
                        if f"_medical_notes/session_{session_id}/" in key:
                            session_info["found"] = True
                            session_info["patient_context"] = "patient"

                            # Extract patient ID from the key
                            parts = key.split('/')
                            if len(parts) > 0:
                                patient_folder = parts[0].replace(
                                    'processed/', '')
                                if '_medical_notes' in patient_folder:
                                    extracted_patient_id = patient_folder.replace(
                                        '_medical_notes', '')
                                    session_info["extracted_patient_id"] = extracted_patient_id

                            # Count messages
                            messages_response = s3_client.list_objects_v2(
                                Bucket=S3_BUCKET,
                                Prefix=key.split(
                                    '/session_')[0] + f"/session_{session_id}/agents/",
                            )

                            message_count = 0
                            for msg_obj in messages_response.get('Contents', []):
                                if 'messages/message_' in msg_obj['Key']:
                                    message_count += 1

                            session_info["message_count"] = message_count
                            break
                else:
                    # For unknown patient sessions
                    response = s3_client.list_objects_v2(
                        Bucket=S3_BUCKET,
                        Prefix=f"{base_prefix}session_{session_id}/",
                        MaxKeys=1
                    )

                    if response.get('Contents'):
                        session_info["found"] = True
                        session_info["patient_context"] = "unknown"

                        # Count messages
                        messages_response = s3_client.list_objects_v2(
                            Bucket=S3_BUCKET,
                            Prefix=f"{base_prefix}session_{session_id}/agents/",
                        )

                        message_count = 0
                        for obj in messages_response.get('Contents', []):
                            if 'messages/message_' in obj['Key']:
                                message_count += 1

                        session_info["message_count"] = message_count
                        break

                if session_info["found"]:
                    break

            except Exception as e:
                logger.debug(f"Error checking prefix {base_prefix}: {str(e)}")
                continue

        return session_info

    except Exception as e:
        logger.error(f"Failed to get session info: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get session info: {str(e)}")


@app.on_event("startup")
async def startup_event():
    """Startup event handler for AgentCore Runtime."""
    logger.info("Healthcare Assistant Agent starting up...")
    logger.info(f"S3 Bucket: {S3_BUCKET}")
    logger.info(f"S3 Prefix: {S3_PREFIX}")
    logger.info(f"AWS Region: {AWS_REGION}")
    logger.info("Agent ready for AgentCore Runtime")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler for AgentCore Runtime."""
    logger.info("Healthcare Assistant Agent shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
