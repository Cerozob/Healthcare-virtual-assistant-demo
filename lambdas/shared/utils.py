"""
Shared utilities for Lambda functions.
Common functions for request/response handling, validation, and error management.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from functools import wraps

logger = logging.getLogger(__name__)


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
    Decorator to handle exceptions in Lambda functions.
    Catches unhandled exceptions and returns appropriate error responses.
    
    Args:
        func: Lambda handler function to wrap
        
    Returns:
        Wrapped function
    """
    @wraps(func)
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        try:
            return func(event, context)
        except ValueError as e:
            logger.error(f"Validation error in {func.__name__}: {e}")
            return create_error_response(400, str(e), "VALIDATION_ERROR")
        except Exception as e:
            logger.error(f"Unhandled exception in {func.__name__}: {e}", exc_info=True)
            return create_error_response(500, "Internal server error", "INTERNAL_ERROR")
    
    return wrapper


def validate_email(email: str) -> bool:
    """
    Basic email validation.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email format is valid, False otherwise
    """
    import re
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """
    Basic phone number validation.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if phone format is valid, False otherwise
    """
    import re
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if it's a valid length (10-15 digits)
    return 10 <= len(digits_only) <= 15


def sanitize_string(value: str, max_length: int = None) -> str:
    """
    Sanitize string input by trimming whitespace and limiting length.
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return str(value)
    
    # Trim whitespace
    sanitized = value.strip()
    
    # Limit length if specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def format_datetime_for_api(dt: datetime) -> str:
    """
    Format datetime for API response.
    
    Args:
        dt: Datetime object to format
        
    Returns:
        ISO formatted datetime string
    """
    if dt is None:
        return None
    
    # Ensure timezone info is present
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.isoformat()


def parse_datetime_from_api(dt_string: str) -> datetime:
    """
    Parse datetime from API request.
    
    Args:
        dt_string: ISO formatted datetime string
        
    Returns:
        Datetime object
        
    Raises:
        ValueError: If datetime parsing fails
    """
    try:
        return datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
    except ValueError as e:
        logger.error(f"Failed to parse datetime: {dt_string}")
        raise ValueError(f"Invalid datetime format: {dt_string}")


def build_filter_clause(
    filters: Dict[str, Any],
    allowed_filters: Dict[str, str]
) -> tuple[str, List[Dict[str, Any]]]:
    """
    Build SQL WHERE clause and parameters from filters.
    
    Args:
        filters: Dictionary of filter values
        allowed_filters: Dictionary mapping filter names to column names
        
    Returns:
        Tuple of (WHERE clause string, parameters list)
    """
    where_conditions = []
    parameters = []
    
    for filter_name, filter_value in filters.items():
        if filter_name in allowed_filters and filter_value is not None:
            column_name = allowed_filters[filter_name]
            
            # Handle different filter types
            if isinstance(filter_value, str) and '%' in filter_value:
                # LIKE filter
                where_conditions.append(f"LOWER({column_name}) LIKE LOWER(:{filter_name})")
            else:
                # Exact match filter
                where_conditions.append(f"{column_name} = :{filter_name}")
            
            # Create parameter
            from .database import DatabaseManager
            db_manager = DatabaseManager()
            parameters.append(db_manager.create_parameter(filter_name, filter_value))
    
    where_clause = ""
    if where_conditions:
        where_clause = "WHERE " + " AND ".join(where_conditions)
    
    return where_clause, parameters
