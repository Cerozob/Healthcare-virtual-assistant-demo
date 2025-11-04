"""
JSON Schema validation utilities for healthcare agent.
Ensures consistency between request/response formats and schemas.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from jsonschema import validate, ValidationError, Draft7Validator
from jsonschema.exceptions import SchemaError

logger = logging.getLogger(__name__)

# Schema file paths
SCHEMA_DIR = Path(__file__).parent.parent / "schemas"
SCHEMAS = {
    "send_message_request": SCHEMA_DIR / "send_message_request.json",
    "structured_output": SCHEMA_DIR / "structured_output.json", 
    "chat_response": SCHEMA_DIR / "chat_response.json",
    "loading_state": SCHEMA_DIR / "loading_state.json"
}

# Cache for loaded schemas
_schema_cache: Dict[str, Dict[str, Any]] = {}


def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load and cache a JSON schema.
    
    Args:
        schema_name: Name of the schema to load
        
    Returns:
        Dict containing the JSON schema
        
    Raises:
        FileNotFoundError: If schema file doesn't exist
        SchemaError: If schema is invalid
    """
    if schema_name in _schema_cache:
        return _schema_cache[schema_name]
    
    if schema_name not in SCHEMAS:
        raise ValueError(f"Unknown schema: {schema_name}. Available: {list(SCHEMAS.keys())}")
    
    schema_path = SCHEMAS[schema_name]
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    try:
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        # Validate the schema itself
        Draft7Validator.check_schema(schema)
        
        _schema_cache[schema_name] = schema
        logger.debug(f"Loaded schema: {schema_name}")
        return schema
        
    except json.JSONDecodeError as e:
        raise SchemaError(f"Invalid JSON in schema {schema_name}: {e}")
    except Exception as e:
        raise SchemaError(f"Error loading schema {schema_name}: {e}")


def validate_request(data: Dict[str, Any]) -> Optional[List[str]]:
    """
    Validate a send message request against the schema.
    
    Args:
        data: Request data to validate
        
    Returns:
        None if valid, list of error messages if invalid
    """
    try:
        schema = load_schema("send_message_request")
        validate(instance=data, schema=schema)
        return None
    except ValidationError as e:
        return [f"Request validation error: {e.message}"]
    except Exception as e:
        return [f"Schema validation error: {str(e)}"]


def validate_response(data: Dict[str, Any]) -> Optional[List[str]]:
    """
    Validate a structured output response against the schema.
    
    Args:
        data: Response data to validate
        
    Returns:
        None if valid, list of error messages if invalid
    """
    try:
        schema = load_schema("structured_output")
        validate(instance=data, schema=schema)
        return None
    except ValidationError as e:
        return [f"Response validation error: {e.message}"]
    except Exception as e:
        return [f"Schema validation error: {str(e)}"]


def validate_chat_response(data: Dict[str, Any]) -> Optional[List[str]]:
    """
    Validate a chat response against the schema.
    
    Args:
        data: Chat response data to validate
        
    Returns:
        None if valid, list of error messages if invalid
    """
    try:
        schema = load_schema("chat_response")
        validate(instance=data, schema=schema)
        return None
    except ValidationError as e:
        return [f"Chat response validation error: {e.message}"]
    except Exception as e:
        return [f"Schema validation error: {str(e)}"]


def create_error_response(
    session_id: str,
    error_code: str, 
    error_message: str,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response that conforms to the schema.
    
    Args:
        session_id: Session identifier
        error_code: Error code identifier
        error_message: Human-readable error message
        details: Optional additional error details
        
    Returns:
        Dict containing standardized error response
    """
    import time
    from datetime import datetime
    
    response = {
        "content": {
            "message": error_message,
            "type": "text"
        },
        "metadata": {
            "sessionId": session_id,
            "agentUsed": "healthcare_agent",
            "toolsExecuted": [],
            "processingTimeMs": 0,
            "timestamp": datetime.utcnow().isoformat(),
            "requestId": f"req_{int(time.time() * 1000)}"
        },
        "success": False,
        "errors": [
            {
                "code": error_code,
                "message": error_message
            }
        ]
    }
    
    if details:
        response["errors"][0]["details"] = details
    
    # Validate the error response we created
    validation_errors = validate_response(response)
    if validation_errors:
        logger.error(f"Created invalid error response: {validation_errors}")
    
    return response


def create_success_response(
    session_id: str,
    content: str,
    processing_time_ms: float,
    tools_executed: List[str],
    patient_context: Optional[Dict[str, Any]] = None,
    file_processing_results: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Create a standardized success response that conforms to the schema.
    
    Args:
        session_id: Session identifier
        content: Response message content
        processing_time_ms: Time taken to process request
        tools_executed: List of tools that were executed
        patient_context: Optional patient context information
        file_processing_results: Optional file processing results
        
    Returns:
        Dict containing standardized success response
    """
    import time
    from datetime import datetime
    
    response = {
        "content": {
            "message": content,
            "type": "text"
        },
        "metadata": {
            "sessionId": session_id,
            "agentUsed": "healthcare_agent",
            "toolsExecuted": tools_executed,
            "processingTimeMs": processing_time_ms,
            "timestamp": datetime.utcnow().isoformat(),
            "requestId": f"req_{int(time.time() * 1000)}"
        },
        "success": True
    }
    
    if patient_context:
        response["patientContext"] = patient_context
    
    if file_processing_results:
        response["fileProcessingResults"] = file_processing_results
    
    # Validate the success response we created
    validation_errors = validate_response(response)
    if validation_errors:
        logger.error(f"Created invalid success response: {validation_errors}")
    
    return response


# Validation decorators for functions
def validate_input(schema_name: str):
    """
    Decorator to validate function input against a schema.
    
    Args:
        schema_name: Name of the schema to validate against
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Assume first argument is the data to validate
            if args:
                data = args[0]
                if schema_name == "send_message_request":
                    errors = validate_request(data)
                elif schema_name == "structured_output":
                    errors = validate_response(data)
                elif schema_name == "chat_response":
                    errors = validate_chat_response(data)
                else:
                    errors = [f"Unknown schema for validation: {schema_name}"]
                
                if errors:
                    raise ValidationError(f"Input validation failed: {errors}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_output(schema_name: str):
    """
    Decorator to validate function output against a schema.
    
    Args:
        schema_name: Name of the schema to validate against
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            if isinstance(result, dict):
                if schema_name == "structured_output":
                    errors = validate_response(result)
                elif schema_name == "chat_response":
                    errors = validate_chat_response(result)
                else:
                    errors = [f"Unknown schema for validation: {schema_name}"]
                
                if errors:
                    logger.error(f"Output validation failed: {errors}")
                    # Don't raise exception for output validation, just log
            
            return result
        return wrapper
    return decorator


if __name__ == "__main__":
    # Test schema loading
    for schema_name in SCHEMAS.keys():
        try:
            schema = load_schema(schema_name)
            print(f"✅ {schema_name}: {schema.get('title', 'No title')}")
        except Exception as e:
            print(f"❌ {schema_name}: {e}")
