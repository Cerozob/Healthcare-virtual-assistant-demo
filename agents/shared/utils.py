"""
Utility functions for agent communication and response formatting.
"""

import logging
import json
from typing import Any, Dict, Optional
from datetime import datetime


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance following Strands best practices.
    
    Args:
        name: Logger name (should be __name__ from calling module)
        
    Returns:
        logging.Logger: Configured logger that inherits from strands root logger
    """
    # Use the standard Python logging approach that integrates with Strands
    # The logger will inherit configuration from the "strands" root logger
    logger = logging.getLogger(name)
    
    # Don't add handlers here - let the root strands logger handle configuration
    # This follows Strands best practices for hierarchical logging
    
    return logger


def format_response(content: str, response_type: str = "markdown") -> str:
    """
    Format response content for frontend compatibility.
    
    Args:
        content: Response content
        response_type: Format type (markdown, plain)
        
    Returns:
        str: Formatted response
    """
    if response_type == "markdown":
        # Ensure proper markdown formatting
        if not content.strip().startswith("#") and not content.strip().startswith("*"):
            # Add basic formatting if none exists
            return content.strip()
        return content.strip()
    
    return content.strip()


def sanitize_for_logging(data: Any) -> Any:
    """
    Basic sanitization for logging by removing common PII/PHI fields.
    
    Args:
        data: Data to sanitize
        
    Returns:
        Any: Sanitized data safe for logging
    """
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            # Remove common PII/PHI fields
            if key.lower() in [
                'patient_id', 'cedula', 'ssn', 'phone', 'email', 
                'address', 'full_name', 'first_name', 'last_name',
                'medical_history', 'lab_results', 'diagnosis'
            ]:
                sanitized[key] = "[PROTECTED]"
            else:
                sanitized[key] = sanitize_for_logging(value)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_for_logging(item) for item in data]
    elif isinstance(data, str):
        # Basic pattern matching for common PII formats
        if len(data) > 5 and (data.isdigit() or '@' in data):
            return "[PROTECTED]"
        return data
    else:
        return data


def create_error_response(
    error_message: str, 
    error_type: str = "general_error",
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create standardized error response.
    
    Args:
        error_message: Human-readable error message
        error_type: Type of error for categorization
        context: Additional context (will be sanitized)
        
    Returns:
        Dict[str, Any]: Standardized error response
    """
    response = {
        "success": False,
        "message": error_message,
        "error_type": error_type,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if context:
        response["context"] = sanitize_for_logging(context)
    
    return response


def extract_patient_context(message: str) -> Optional[Dict[str, str]]:
    """
    Extract patient context from user message.
    
    Args:
        message: User message
        
    Returns:
        Optional[Dict[str, str]]: Extracted patient context
    """
    import re
    
    # Pattern for Spanish patient session context
    session_pattern = r"esta sesión es del paciente\s+([^.]+)"
    match = re.search(session_pattern, message.lower())
    
    if match:
        patient_name = match.group(1).strip()
        return {"patient_name": patient_name}
    
    # Pattern for cedula/ID numbers
    cedula_pattern = r"cedula\s+(\d+)"
    match = re.search(cedula_pattern, message.lower())
    
    if match:
        cedula = match.group(1)
        return {"cedula": cedula}
    
    return None


def extract_patient_id_from_message(message: str) -> Optional[str]:
    """
    Extract patient ID from user message using various patterns.
    
    Args:
        message: User message
        
    Returns:
        Optional[str]: Extracted patient ID or None
    """
    import re
    
    # Pattern for explicit patient ID
    patient_id_patterns = [
        r"paciente\s+id[:\s]+([a-zA-Z0-9\-_]+)",
        r"patient\s+id[:\s]+([a-zA-Z0-9\-_]+)",
        r"cedula[:\s]+(\d+)",
        r"cédula[:\s]+(\d+)",
        r"id\s+paciente[:\s]+([a-zA-Z0-9\-_]+)",
        r"esta sesión es del paciente\s+([a-zA-Z0-9\-_\s]+)",
        r"notas del paciente\s+([a-zA-Z0-9\-_\s]+)",
        r"patient\s+([a-zA-Z0-9\-_\s]+)\s+notes",
    ]
    
    message_lower = message.lower()
    
    for pattern in patient_id_patterns:
        match = re.search(pattern, message_lower)
        if match:
            patient_id = match.group(1).strip()
            # Clean up patient ID (remove spaces, normalize)
            patient_id = re.sub(r'\s+', '_', patient_id)
            return patient_id
    
    return None


def create_session_metadata(patient_id: Optional[str] = None, additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create session metadata for medical notes storage using consistent structure.
    
    Args:
        patient_id: Patient identifier
        additional_context: Additional context to include
        
    Returns:
        Dict[str, Any]: Session metadata
    """
    # Use consistent structure with document processing
    if patient_id:
        storage_prefix = f"processed/{patient_id}_medical_notes/"
    else:
        storage_prefix = f"processed/unknown_medical_notes/"
    
    metadata = {
        "timestamp": datetime.utcnow().isoformat(),
        "session_type": "medical_consultation",
        "patient_context": {
            "patient_id": patient_id if patient_id else "unknown",
            "has_patient_context": patient_id is not None,
            "storage_prefix": storage_prefix,
            "consistent_with_documents": True
        },
        "storage_structure": {
            "pattern": "processed/{patient_id}_{data_type}/",
            "data_type": "medical_notes",
            "follows_document_structure": True
        }
    }
    
    if additional_context:
        metadata.update(additional_context)
    
    return metadata


def validate_spanish_medical_terms(text: str) -> bool:
    """
    Validate if text contains Spanish medical terminology.
    
    Args:
        text: Text to validate
        
    Returns:
        bool: True if contains Spanish medical terms
    """
    spanish_medical_terms = [
        'paciente', 'médico', 'cita', 'consulta', 'examen',
        'laboratorio', 'diagnóstico', 'tratamiento', 'medicamento',
        'síntoma', 'enfermedad', 'hospital', 'clínica'
    ]
    
    text_lower = text.lower()
    return any(term in text_lower for term in spanish_medical_terms)
