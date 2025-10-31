"""
Essential utility functions for agent system.
Simplified to include only actively used functions.
"""

import logging
from typing import Any, Dict, Optional


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
