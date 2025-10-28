"""
Patient lookup tool for healthcare assistant.
Uses MCP structured output with LLM to extract patient information and queries Lambda functions for patient data.
"""

import logging
import json
import os
import boto3
from typing import Optional, Dict, Any, List
from strands import tool, Agent
from pydantic import BaseModel, Field
from botocore.exceptions import ClientError

# Configure logger
logger = logging.getLogger(__name__)

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
PATIENT_LOOKUP_LAMBDA = os.getenv("PATIENT_LOOKUP_LAMBDA", "PatientLookupFunction")

# Initialize AWS clients
lambda_client = boto3.client('lambda', region_name=AWS_REGION)

# Pydantic models for structured output
class PatientInfo(BaseModel):
    """Structured patient information extracted from natural language."""
    cedula: Optional[str] = Field(None, description="Número de cédula del paciente (8-10 dígitos)")
    first_name: Optional[str] = Field(None, description="Primer nombre del paciente")
    last_name: Optional[str] = Field(None, description="Apellido del paciente")
    full_name: Optional[str] = Field(None, description="Nombre completo del paciente")
    medical_record_number: Optional[str] = Field(None, description="Número de historia clínica (ej: MRN-001)")
    phone: Optional[str] = Field(None, description="Número de teléfono")
    email: Optional[str] = Field(None, description="Correo electrónico")
    date_of_birth: Optional[str] = Field(None, description="Fecha de nacimiento")
    search_confidence: str = Field("medium", description="Nivel de confianza en la información extraída: high, medium, low")
    has_patient_info: bool = Field(False, description="True si se encontró información de paciente en el mensaje")

# Create a dedicated extraction agent
extraction_agent = Agent(
    system_prompt="""
Eres un experto en extraer información de pacientes de mensajes médicos en español.
Tu tarea es analizar mensajes y extraer ÚNICAMENTE la información específica del paciente mencionada.

REGLAS IMPORTANTES:
1. Solo extrae información que esté EXPLÍCITAMENTE mencionada en el mensaje
2. NO inventes o asumas información que no esté presente
3. Si no hay información de paciente, marca has_patient_info como False
4. Sé muy preciso con nombres y números
5. La cédula debe ser un número de 8-10 dígitos
6. Los números de historia clínica suelen tener formato MRN-XXX

EJEMPLOS:
- "Paciente Juan Pérez cédula 12345678" → extraer nombre y cédula
- "Busca información general sobre diabetes" → has_patient_info = False
- "Historia clínica MRN-001" → extraer solo el MRN
""",
    callback_handler=None
)


@tool(
    name="extract_and_search_patient",
    description="Extract patient information from natural language and search for the patient in the database"
)
def extract_and_search_patient(
    user_message: str,
    tool_context=None
) -> Dict[str, Any]:
    """
    Use LLM to extract patient information from natural language and search for the patient.
    
    Args:
        user_message: The user's message containing patient information
        tool_context: Tool execution context
        
    Returns:
        Dict containing patient information or error message
    """
    try:
        logger.info(f"Extracting patient info from message: '{user_message[:100]}...'")
        
        if not user_message.strip():
            return {
                "success": False,
                "error": "El mensaje no puede estar vacío",
                "patient": None
            }
        
        # Use LLM with structured output to extract patient information
        extracted_info = _extract_patient_info_with_llm(user_message)
        
        if not extracted_info["success"]:
            return extracted_info
        
        # Search for patient using extracted information
        patient_data = _search_patient_via_lambda(extracted_info["extracted_data"])
        
        if patient_data["success"] and patient_data["patient"]:
            patient_info = patient_data["patient"]
            
            # Set patient context in agent state if tool_context is available
            if tool_context and hasattr(tool_context, 'agent'):
                agent = tool_context.agent
                agent.state.set("current_patient_id", patient_info.get('cedula', patient_info.get('patient_id')))
                agent.state.set("current_patient_name", patient_info['full_name'])
                agent.state.set("current_patient_data", patient_info)  # Store complete patient object
                agent.state.set("session_context", "patient_session")
                logger.info(f"Set patient context in agent state: {patient_info['full_name']} (ID: {patient_info.get('cedula', patient_info.get('patient_id'))})")
            
            return {
                "success": True,
                "patient": patient_info,
                "extracted_info": extracted_info["extracted_data"],
                "message": f"✅ **Paciente encontrado**: {patient_info['full_name']} (Cédula: {patient_info.get('cedula', patient_info.get('patient_id', 'N/A'))})\n\n**Información del paciente:**\n- **Nombre completo:** {patient_info['full_name']}\n- **Cédula:** {patient_info.get('cedula', patient_info.get('patient_id', 'N/A'))}\n- **Fecha de nacimiento:** {patient_info.get('date_of_birth', 'No disponible')}\n\nEl contexto del paciente ha sido establecido para esta conversación."
            }
        else:
            return {
                "success": False,
                "error": patient_data.get("error", "No se encontró el paciente"),
                "extracted_info": extracted_info["extracted_data"],
                "patient": None
            }
            
    except Exception as e:
        logger.error(f"Error in extract_and_search_patient: {str(e)}")
        return {
            "success": False,
            "error": f"Error procesando la solicitud: {str(e)}",
            "patient": None
        }


def _extract_patient_info_with_llm(user_message: str) -> Dict[str, Any]:
    """
    Use MCP structured output with LLM to extract patient information from natural language.
    
    Args:
        user_message: The user's message
        
    Returns:
        Dict containing extracted patient information
    """
    try:
        logger.info(f"Extracting patient info with LLM from: {user_message[:100]}...")
        
        # Use structured output to extract patient information
        extraction_prompt = f"""
Analiza el siguiente mensaje médico y extrae ÚNICAMENTE la información específica del paciente que esté explícitamente mencionada.

Mensaje: "{user_message}"

Extrae la información del paciente si está presente. Si no hay información específica de un paciente, marca has_patient_info como False.
"""
        
        # Use structured output to get patient information
        patient_info = extraction_agent.structured_output(
            output_model=PatientInfo,
            prompt=extraction_prompt
        )
        
        logger.info(f"LLM extracted patient info: {patient_info}")
        
        # Convert to dictionary and filter out None values
        extracted_data = {}
        for field, value in patient_info.model_dump().items():
            if value is not None and value != "" and field != "has_patient_info" and field != "search_confidence":
                extracted_data[field] = value
        
        if patient_info.has_patient_info and extracted_data:
            return {
                "success": True,
                "extracted_data": extracted_data,
                "confidence": patient_info.search_confidence,
                "message": f"Información extraída con LLM: {extracted_data}"
            }
        else:
            return {
                "success": False,
                "error": "No se encontró información específica del paciente en el mensaje",
                "extracted_data": {},
                "confidence": patient_info.search_confidence
            }
            
    except Exception as e:
        logger.error(f"Error in LLM extraction: {str(e)}")
        return {
            "success": False,
            "error": f"Error extrayendo información con LLM: {str(e)}",
            "extracted_data": {}
        }


def _search_patient_via_lambda(extracted_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search for patient using Lambda function with extracted information.
    
    Args:
        extracted_info: Extracted patient information
        
    Returns:
        Dict containing patient search results
    """
    try:
        logger.info(f"Searching patient via Lambda with info: {extracted_info}")
        
        # Prepare payload for Lambda function
        lambda_payload = {
            "action": "search_patient",
            "search_criteria": extracted_info,
            "region": AWS_REGION
        }
        
        # Invoke Lambda function
        try:
            response = lambda_client.invoke(
                FunctionName=PATIENT_LOOKUP_LAMBDA,
                InvocationType='RequestResponse',
                Payload=json.dumps(lambda_payload)
            )
            
            # Parse Lambda response
            response_payload = json.loads(response['Payload'].read())
            
            if response_payload.get("statusCode") == 200:
                body = json.loads(response_payload.get("body", "{}"))
                return {
                    "success": True,
                    "patient": body.get("patient"),
                    "message": body.get("message", "Paciente encontrado")
                }
            else:
                error_body = json.loads(response_payload.get("body", "{}"))
                return {
                    "success": False,
                    "error": error_body.get("error", "Error en la búsqueda"),
                    "patient": None
                }
                
        except ClientError as e:
            logger.error(f"Lambda invocation error: {str(e)}")
            return {
                "success": False,
                "error": f"Error invocando Lambda: {str(e)}",
                "patient": None
            }
            
    except Exception as e:
        logger.error(f"Error in Lambda patient search: {str(e)}")
        return {
            "success": False,
            "error": f"Error buscando paciente: {str(e)}",
            "patient": None
        }


@tool(
    name="get_patient_by_id", 
    description="Get patient information by exact patient ID or cedula"
)
def get_patient_by_id(
    patient_id: str
) -> Dict[str, Any]:
    """
    Get patient information by exact patient ID or cedula via Lambda function.
    
    Args:
        patient_id: The patient ID or cedula
        tool_context: Tool execution context
        
    Returns:
        Dict containing patient information or error message
    """
    try:
        logger.info(f"Getting patient by ID: {patient_id}")
        
        patient_id = patient_id.strip()
        if not patient_id:
            return {
                "success": False,
                "error": "ID de paciente no puede estar vacío",
                "patient": None
            }
        
        # Search using Lambda with exact ID
        search_result = _search_patient_via_lambda({"cedula": patient_id, "patient_id": patient_id})
        
        if search_result["success"] and search_result["patient"]:
            return search_result
        else:
            return {
                "success": False,
                "error": f"No se encontró paciente con ID: {patient_id}",
                "patient": None
            }
            
    except Exception as e:
        logger.error(f"Error getting patient by ID: {str(e)}")
        return {
            "success": False,
            "error": f"Error obteniendo paciente: {str(e)}",
            "patient": None
        }


@tool(
    name="list_recent_patients",
    description="List recently accessed patients for quick selection"
)
def list_recent_patients(
    limit: int = 5
) -> Dict[str, Any]:
    """
    List recently accessed patients via Lambda function.
    
    Args:
        limit: Maximum number of patients to return
        tool_context: Tool execution context
        
    Returns:
        Dict containing list of recent patients
    """
    try:
        logger.info(f"Listing recent patients (limit: {limit})")
        
        # Prepare payload for Lambda function
        lambda_payload = {
            "action": "list_recent_patients",
            "limit": limit,
            "region": AWS_REGION
        }
        
        try:
            # Invoke Lambda function
            response = lambda_client.invoke(
                FunctionName=PATIENT_LOOKUP_LAMBDA,
                InvocationType='RequestResponse',
                Payload=json.dumps(lambda_payload)
            )
            
            # Parse Lambda response
            response_payload = json.loads(response['Payload'].read())
            
            if response_payload.get("statusCode") == 200:
                body = json.loads(response_payload.get("body", "{}"))
                return {
                    "success": True,
                    "patients": body.get("patients", []),
                    "count": len(body.get("patients", [])),
                    "message": f"Se encontraron {len(body.get('patients', []))} pacientes recientes"
                }
            else:
                error_body = json.loads(response_payload.get("body", "{}"))
                return {
                    "success": False,
                    "error": error_body.get("error", "Error listando pacientes"),
                    "patients": []
                }
                
        except ClientError as e:
            logger.error(f"Lambda invocation error: {str(e)}")
            # Fallback to mock data
            return _fallback_list_recent_patients(limit)
            
    except Exception as e:
        logger.error(f"Error listing recent patients: {str(e)}")
        return {
            "success": False,
            "error": f"Error listando pacientes: {str(e)}",
            "patients": []
        }


def _fallback_list_recent_patients(limit: int = 5) -> Dict[str, Any]:
    """Fallback function for listing recent patients using mock data."""
    mock_patients = [
        {
            "patient_id": "12345678",
            "cedula": "12345678",
            "full_name": "Juan Pérez",
            "medical_record_number": "MRN-001"
        },
        {
            "patient_id": "87654321",
            "cedula": "87654321",
            "full_name": "María González",
            "medical_record_number": "MRN-002"
        },
        {
            "patient_id": "11223344",
            "cedula": "11223344",
            "full_name": "Carlos Rodríguez",
            "medical_record_number": "MRN-003"
        }
    ]
    
    recent_patients = mock_patients[:limit]
    
    return {
        "success": True,
        "patients": recent_patients,
        "count": len(recent_patients),
        "message": f"Se encontraron {len(recent_patients)} pacientes recientes (datos de prueba)"
    }


# Additional utility functions for patient management

@tool(
    name="validate_patient_session",
    description="Validate that a patient session is properly established"
)
def validate_patient_session() -> Dict[str, Any]:
    """
    Validate that a patient session is properly established.
    
    Args:
        tool_context: Tool execution context
        
    Returns:
        Dict containing session validation results
    """
    try:
        # This is a simplified version since we can't access agent state directly
        # In a real implementation, this would check session state via API
        return {
            "success": True,
            "message": "Función de validación de sesión disponible. Use extract_and_search_patient para establecer contexto de paciente.",
            "note": "Esta herramienta requiere integración con el estado del agente para funcionar completamente."
        }
        
    except Exception as e:
        logger.error(f"Error validating patient session: {str(e)}")
        return {
            "success": False,
            "error": f"Error validando sesión: {str(e)}",
            "has_patient": False
        }
