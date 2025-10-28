"""
Shared utilities for Lambda functions.
Common functions for request/response handling, validation, and error management.
"""

import json
import logging
import uuid
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from functools import wraps

logger = logging.getLogger(__name__)


class StructuredLogger:
    """
    Structured logging utility for Lambda functions.
    Provides consistent JSON-formatted logging with context.
    """
    
    def __init__(self, logger_name: str = __name__):
        self.logger = logging.getLogger(logger_name)
        
    def log(self, level: str, message: str, **context):
        """Log a message with structured context."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': level.upper(),
            'message': message,
            **{k: v for k, v in context.items() if v is not None}
        }
        
        # Use the appropriate logging level
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(json.dumps(log_entry))
    
    def info(self, message: str, **context):
        """Log an info message."""
        self.log('INFO', message, **context)
    
    def debug(self, message: str, **context):
        """Log a debug message."""
        self.log('DEBUG', message, **context)
    
    def warning(self, message: str, **context):
        """Log a warning message."""
        self.log('WARNING', message, **context)
    
    def error(self, message: str, **context):
        """Log an error message."""
        self.log('ERROR', message, **context)
    
    def exception(self, message: str, exc: Exception = None, **context):
        """Log an exception with traceback."""
        context['error_type'] = type(exc).__name__ if exc else 'Unknown'
        context['traceback'] = traceback.format_exc()
        self.log('ERROR', message, **context)


def create_request_logger(request_id: str = None) -> StructuredLogger:
    """
    Create a structured logger with request context.
    
    Args:
        request_id: Optional request ID to include in all log messages
        
    Returns:
        StructuredLogger instance with request context
    """
    class RequestLogger(StructuredLogger):
        def __init__(self, req_id: str = None):
            super().__init__()
            self.request_id = req_id or str(uuid.uuid4())
        
        def log(self, level: str, message: str, **context):
            context['request_id'] = self.request_id
            super().log(level, message, **context)
    
    return RequestLogger(request_id)


def create_response(
    status_code: int, 
    body: Dict[str, Any], 
    headers: Dict[str, str] = None
) -> Dict[str, Any]:
    """
    Create a standardized API Gateway response.
    
    Args:
        status_code: HTTP status code
        body: Response body dictionary
        headers: Optional additional headers
        
    Returns:
        API Gateway response dictionary
    """
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Amz-Date, X-Api-Key, X-Amz-Security-Token'
    }
    
    if headers:
        default_headers.update(headers)
    
    return {
        'statusCode': status_code,
        'headers': default_headers,
        'body': json.dumps(body, default=str)  # default=str handles datetime serialization
    }


def create_error_response(
    status_code: int, 
    message: str, 
    error_code: str = None,
    details: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        status_code: HTTP status code
        message: Error message
        error_code: Optional error code for client handling
        details: Optional additional error details
        
    Returns:
        API Gateway error response dictionary
    """
    error_body = {
        'error': {
            'message': message,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    }
    
    if error_code:
        error_body['error']['code'] = error_code
        
    if details:
        error_body['error']['details'] = details
    
    return create_response(status_code, error_body)


def parse_event_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse the request body from API Gateway event.
    
    Args:
        event: API Gateway event dictionary
        
    Returns:
        Parsed body dictionary
        
    Raises:
        ValueError: If body parsing fails
    """
    body = event.get('body')
    
    if not body:
        return {}
    
    try:
        if isinstance(body, str):
            return json.loads(body)
        return body
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse request body: {e}")
        raise ValueError("Invalid JSON in request body")


def extract_path_parameters(event: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract path parameters from API Gateway event.
    
    Args:
        event: API Gateway event dictionary
        
    Returns:
        Dictionary of path parameters
    """
    return event.get('pathParameters') or {}


def extract_query_parameters(event: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract query string parameters from API Gateway event.
    
    Args:
        event: API Gateway event dictionary
        
    Returns:
        Dictionary of query parameters
    """
    return event.get('queryStringParameters') or {}


def validate_required_fields(
    data: Dict[str, Any], 
    required_fields: List[str]
) -> Optional[str]:
    """
    Validate that required fields are present in the data.
    
    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
        
    Returns:
        Error message if validation fails, None if successful
    """
    missing_fields = []
    
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            missing_fields.append(field)
    
    if missing_fields:
        return f"Missing required fields: {', '.join(missing_fields)}"
    
    return None


def validate_pagination_params(
    query_params: Dict[str, str],
    default_limit: int = 50,
    max_limit: int = 1000
) -> Dict[str, int]:
    """
    Validate and normalize pagination parameters.
    
    Args:
        query_params: Query parameters dictionary
        default_limit: Default limit if not provided
        max_limit: Maximum allowed limit
        
    Returns:
        Dictionary with validated limit and offset
        
    Raises:
        ValueError: If pagination parameters are invalid
    """
    try:
        # Parse limit
        limit = int(query_params.get('limit', default_limit))
        if limit <= 0:
            limit = default_limit
        elif limit > max_limit:
            limit = max_limit
        
        # Parse offset
        offset = int(query_params.get('offset', 0))
        if offset < 0:
            offset = 0
        
        return {
            'limit': limit,
            'offset': offset
        }
        
    except ValueError as e:
        logger.error(f"Invalid pagination parameters: {e}")
        raise ValueError("Invalid pagination parameters. Limit and offset must be integers.")


def generate_uuid() -> str:
    """
    Generate a UUID string.
    
    Returns:
        UUID string
    """
    return str(uuid.uuid4())


def get_current_timestamp() -> datetime:
    """
    Get current UTC timestamp.
    
    Returns:
        Current datetime in UTC
    """
    return datetime.now(timezone.utc)


def handle_exceptions(func):
    """
    Enhanced decorator to handle exceptions in Lambda functions.
    Catches unhandled exceptions and returns appropriate error responses with structured logging.
    
    Args:
        func: Lambda handler function to wrap
        
    Returns:
        Wrapped function
    """
    @wraps(func)
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        start_time = datetime.now(timezone.utc)
        request_id = context.aws_request_id if context else str(uuid.uuid4())
        structured_logger = create_request_logger(request_id)
        
        # Log function entry
        structured_logger.info(
            f"Lambda function {func.__name__} started",
            function_name=func.__name__,
            lambda_version=context.function_version if context else 'unknown',
            memory_limit=context.memory_limit_in_mb if context else 'unknown',
            remaining_time_ms=context.get_remaining_time_in_millis() if context else 'unknown'
        )
        
        try:
            result = func(event, context)
            
            # Log successful completion
            duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            status_code = result.get('statusCode', 'unknown') if isinstance(result, dict) else 'unknown'
            
            structured_logger.info(
                f"Lambda function {func.__name__} completed successfully",
                function_name=func.__name__,
                duration_ms=round(duration_ms, 2),
                status_code=status_code
            )
            
            return result
            
        except ValueError as e:
            duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            structured_logger.error(
                f"Validation error in {func.__name__}: {str(e)}",
                function_name=func.__name__,
                error_type="ValidationError",
                duration_ms=round(duration_ms, 2)
            )
            return create_error_response(400, str(e), "VALIDATION_ERROR")
            
        except Exception as e:
            duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            structured_logger.exception(
                f"Unhandled exception in {func.__name__}: {str(e)}",
                exc=e,
                function_name=func.__name__,
                duration_ms=round(duration_ms, 2)
            )
            return create_error_response(500, "Internal server error", "INTERNAL_ERROR")
    
    return wrapper


def log_performance_metrics(func_name: str, duration_ms: float, **metrics):
    """
    Log performance metrics for a function.
    
    Args:
        func_name: Name of the function
        duration_ms: Duration in milliseconds
        **metrics: Additional metrics to log
    """
    structured_logger = StructuredLogger()
    structured_logger.info(
        f"Performance metrics for {func_name}",
        function_name=func_name,
        duration_ms=round(duration_ms, 2),
        **metrics
    )


def log_aws_api_call(service: str, operation: str, duration_ms: float, success: bool, **context):
    """
    Log AWS API call metrics.
    
    Args:
        service: AWS service name (e.g., 'bedrock-agentcore', 'ssm')
        operation: API operation name
        duration_ms: Duration in milliseconds
        success: Whether the call was successful
        **context: Additional context
    """
    structured_logger = StructuredLogger()
    level = 'info' if success else 'error'
    
    structured_logger.log(
        level,
        f"AWS API call: {service}.{operation}",
        aws_service=service,
        aws_operation=operation,
        duration_ms=round(duration_ms, 2),
        success=success,
        **context
    )
