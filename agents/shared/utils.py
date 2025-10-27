"""
Utility functions for agent communication and response formatting.
"""

import logging
import json
from typing import Any, Dict, Optional
from datetime import datetime


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
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
