"""
Patient Lookup Lambda Function
Handles patient search requests from the healthcare assistant agent.
Uses RDS Data API to query the Aurora PostgreSQL database.
Supports multi-criteria search across name, email, phone, and cedula.
Enhanced with comprehensive error handling, input validation, and structured logging.
"""

import json
import logging
import os
import time
import re
from typing import Dict, Any, List, Optional
from shared.database import DatabaseManager, DatabaseError
from shared.utils import create_response, create_error_response, StructuredLogger

# Configure structured logging
logger = StructuredLogger(__name__)
base_logger = logging.getLogger()
base_logger.setLevel(logging.INFO)

# Environment variables
PATIENT_TABLE = os.getenv("PATIENT_TABLE", "patients")

# Initialize database manager
db_manager = DatabaseManager()

# Constants
DEFAULT_SEARCH_LIMIT = 3
MAX_SEARCH_LIMIT = 10

# Input validation patterns
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PHONE_PATTERN = re.compile(r'^[\d\s\-\+\(\)\.]{7,20}$')
CEDULA_PATTERN = re.compile(r'^[\d\-\.]{5,20}$')

# Maximum input lengths for security
MAX_NAME_LENGTH = 100
MAX_EMAIL_LENGTH = 100
MAX_PHONE_LENGTH = 20
MAX_CEDULA_LENGTH = 20


def create_enhanced_error_response(
    status_code: int, 
    message: str, 
    error_code: str,
    request_id: str,
    start_time: float,
    additional_metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Create an enhanced error response with comprehensive metadata and logging.
    
    Args:
        status_code: HTTP status code
        message: Error message
        error_code: Error code for client handling
        request_id: Request identifier for tracing
        start_time: Request start time for duration calculation
        additional_metadata: Optional additional metadata
        
    Returns:
        Enhanced error response with metadata
    """
    execution_time_ms = int((time.time() - start_time) * 1000)
    
    # Create comprehensive error metadata
    error_metadata = {
        "criteria_used": [],
        "total_results": 0,
        "search_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "execution_time_ms": execution_time_ms,
        "error_type": "validation_error" if status_code < 500 else "system_error",
        "request_id": request_id
    }
    
    if additional_metadata:
        error_metadata.update(additional_metadata)
    
    # Log the error with structured logging
    logger.error(
        "Error response generated",
        request_id=request_id,
        status_code=status_code,
        error_code=error_code,
        error_message=message,
        execution_time_ms=execution_time_ms
    )
    
    # Create response body with consistent structure
    response_body = {
        "success": False,
        "error": message,
        "error_code": error_code,
        "patients": [],
        "search_metadata": error_metadata,
        "message": message
    }
    
    return create_response(status_code, response_body)


def validate_search_input(
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    cedula: Optional[str] = None,
    limit: Optional[int] = None,
    request_id: str = "unknown"
) -> Dict[str, Any]:
    """
    Comprehensive input validation for search criteria with detailed error reporting.
    
    Args:
        name: Patient name to validate
        email: Email address to validate
        phone: Phone number to validate
        cedula: Cedula/ID to validate
        limit: Search limit to validate
        request_id: Request ID for logging
        
    Returns:
        Dict with validation results: {"valid": bool, "errors": List[str], "sanitized": Dict}
    """
    validation_result = {
        "valid": True,
        "errors": [],
        "sanitized": {}
    }
    
    # Validate and sanitize name
    if name is not None:
        if not isinstance(name, str):
            validation_result["errors"].append("Name must be a string")
            validation_result["valid"] = False
        else:
            name = name.strip()
            if len(name) == 0:
                validation_result["errors"].append("Name cannot be empty")
                validation_result["valid"] = False
            elif len(name) > MAX_NAME_LENGTH:
                validation_result["errors"].append(f"Name exceeds maximum length of {MAX_NAME_LENGTH} characters")
                validation_result["valid"] = False
            else:
                # Sanitize name (remove potentially harmful characters)
                sanitized_name = re.sub(r'[<>"\';]', '', name)
                validation_result["sanitized"]["name"] = sanitized_name
                
                if sanitized_name != name:
                    logger.warning(
                        "Name input sanitized",
                        request_id=request_id,
                        original_length=len(name),
                        sanitized_length=len(sanitized_name)
                    )
    
    # Validate and sanitize email
    if email is not None:
        if not isinstance(email, str):
            validation_result["errors"].append("Email must be a string")
            validation_result["valid"] = False
        else:
            email = email.strip().lower()
            if len(email) == 0:
                validation_result["errors"].append("Email cannot be empty")
                validation_result["valid"] = False
            elif len(email) > MAX_EMAIL_LENGTH:
                validation_result["errors"].append(f"Email exceeds maximum length of {MAX_EMAIL_LENGTH} characters")
                validation_result["valid"] = False
            elif not EMAIL_PATTERN.match(email):
                validation_result["errors"].append("Invalid email format")
                validation_result["valid"] = False
            else:
                validation_result["sanitized"]["email"] = email
    
    # Validate and sanitize phone
    if phone is not None:
        if not isinstance(phone, str):
            validation_result["errors"].append("Phone must be a string")
            validation_result["valid"] = False
        else:
            phone = phone.strip()
            if len(phone) == 0:
                validation_result["errors"].append("Phone cannot be empty")
                validation_result["valid"] = False
            elif len(phone) > MAX_PHONE_LENGTH:
                validation_result["errors"].append(f"Phone exceeds maximum length of {MAX_PHONE_LENGTH} characters")
                validation_result["valid"] = False
            elif not PHONE_PATTERN.match(phone):
                validation_result["errors"].append("Invalid phone format")
                validation_result["valid"] = False
            else:
                validation_result["sanitized"]["phone"] = phone
    
    # Validate and sanitize cedula
    if cedula is not None:
        if not isinstance(cedula, str):
            validation_result["errors"].append("Cedula must be a string")
            validation_result["valid"] = False
        else:
            cedula = cedula.strip()
            if len(cedula) == 0:
                validation_result["errors"].append("Cedula cannot be empty")
                validation_result["valid"] = False
            elif len(cedula) > MAX_CEDULA_LENGTH:
                validation_result["errors"].append(f"Cedula exceeds maximum length of {MAX_CEDULA_LENGTH} characters")
                validation_result["valid"] = False
            elif not CEDULA_PATTERN.match(cedula):
                validation_result["errors"].append("Invalid cedula format")
                validation_result["valid"] = False
            else:
                validation_result["sanitized"]["cedula"] = cedula
    
    # Validate limit
    if limit is not None:
        try:
            limit = int(limit)
            if limit <= 0:
                validation_result["errors"].append("Limit must be greater than 0")
                validation_result["valid"] = False
            elif limit > MAX_SEARCH_LIMIT:
                validation_result["errors"].append(f"Limit cannot exceed {MAX_SEARCH_LIMIT}")
                validation_result["valid"] = False
            else:
                validation_result["sanitized"]["limit"] = limit
        except (ValueError, TypeError):
            validation_result["errors"].append("Limit must be a valid integer")
            validation_result["valid"] = False
    
    # Log validation results
    if not validation_result["valid"]:
        logger.warning(
            "Input validation failed",
            request_id=request_id,
            validation_errors=validation_result["errors"],
            provided_fields=[k for k, v in {"name": name, "email": email, "phone": phone, "cedula": cedula}.items() if v is not None]
        )
    else:
        logger.debug(
            "Input validation successful",
            request_id=request_id,
            sanitized_fields=list(validation_result["sanitized"].keys())
        )
    
    return validation_result


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for patient lookup requests with comprehensive error handling.

    Args:
        event: Lambda event containing the request
        context: Lambda context

    Returns:
        Dict containing the response with consistent error handling
    """
    request_id = context.aws_request_id if context else "unknown"
    start_time = time.time()
    
    try:
        # Log request initiation with structured logging
        logger.info(
            "Patient lookup request initiated",
            request_id=request_id,
            function_name=context.function_name if context else "patient_lookup",
            memory_limit=context.memory_limit_in_mb if context else "unknown",
            remaining_time_ms=context.get_remaining_time_in_millis() if context else "unknown"
        )
        
        # Validate event structure
        if not isinstance(event, dict):
            logger.error(
                "Invalid event format received",
                request_id=request_id,
                event_type=type(event).__name__
            )
            return create_enhanced_error_response(
                400, 
                "Invalid event format", 
                "INVALID_EVENT_FORMAT",
                request_id,
                start_time
            )

        # Parse and validate the action
        action = event.get("action")
        if not action:
            logger.error(
                "Missing action in request",
                request_id=request_id,
                event_keys=list(event.keys())
            )
            return create_enhanced_error_response(
                400, 
                "Missing required 'action' parameter", 
                "MISSING_ACTION",
                request_id,
                start_time
            )

        # Log action being processed
        logger.info(
            "Processing patient lookup action",
            request_id=request_id,
            action=action
        )

        # Route to appropriate handler with enhanced error handling
        if action == "search_patient":
            search_criteria = event.get("search_criteria", {})
            logger.debug(
                "Routing to search_patient handler",
                request_id=request_id,
                criteria_keys=list(search_criteria.keys()) if isinstance(search_criteria, dict) else "invalid"
            )
            return handle_search_patient(search_criteria, request_id)
            
        elif action == "list_recent_patients":
            limit = event.get("limit", 5)
            logger.debug(
                "Routing to list_recent_patients handler",
                request_id=request_id,
                limit=limit
            )
            return handle_list_recent_patients(limit, request_id)
            
        elif action == "get_patient_by_id":
            patient_id = event.get("patient_id")
            logger.debug(
                "Routing to get_patient_by_id handler",
                request_id=request_id,
                patient_id_provided=bool(patient_id)
            )
            return handle_get_patient_by_id(patient_id, request_id)
        else:
            logger.error(
                "Invalid action requested",
                request_id=request_id,
                action=action,
                valid_actions=["search_patient", "list_recent_patients", "get_patient_by_id"]
            )
            return create_enhanced_error_response(
                400, 
                f"Invalid action: {action}. Valid actions are: search_patient, list_recent_patients, get_patient_by_id", 
                "INVALID_ACTION",
                request_id,
                start_time
            )

    except DatabaseError as e:
        logger.error(
            "Database error in lambda handler",
            request_id=request_id,
            error_message=str(e),
            error_code=e.error_code,
            original_error=str(e.original_error) if e.original_error else None
        )
        return create_enhanced_error_response(
            503, 
            f"Database service error: {str(e)}", 
            e.error_code or "DATABASE_ERROR",
            request_id,
            start_time
        )
    except Exception as e:
        logger.error(
            "Unexpected error in lambda handler",
            request_id=request_id,
            error_message=str(e),
            error_type=type(e).__name__
        )
        return create_enhanced_error_response(
            500, 
            f"Internal server error: {str(e)}", 
            "INTERNAL_ERROR",
            request_id,
            start_time
        )


def handle_search_patient(search_criteria: Dict[str, Any], request_id: str = "unknown") -> Dict[str, Any]:
    """
    Handle patient search based on various criteria with comprehensive error handling.

    Args:
        search_criteria: Dictionary containing search parameters
                        - name: Full name for fuzzy matching
                        - email: Email address for exact matching
                        - phone: Phone number for exact matching
                        - cedula: National ID for exact matching
                        - limit: Maximum results (default: 3, max: 10)

    Returns:
        Dict containing the response with patients array and search metadata
    """
    start_time = time.time()
    
    try:
        logger.info(
            "Processing patient search request",
            request_id=request_id,
            criteria_provided=list(search_criteria.keys()) if isinstance(search_criteria, dict) else "invalid"
        )

        # Validate search criteria structure
        if not isinstance(search_criteria, dict):
            logger.error(
                "Invalid search criteria format",
                request_id=request_id,
                criteria_type=type(search_criteria).__name__
            )
            return create_enhanced_error_response(
                400, 
                "Search criteria must be a dictionary", 
                "INVALID_FORMAT",
                request_id,
                start_time
            )

        if not search_criteria:
            logger.error(
                "Empty search criteria provided",
                request_id=request_id
            )
            return create_enhanced_error_response(
                400, 
                "No search criteria provided", 
                "MISSING_CRITERIA",
                request_id,
                start_time
            )

        # Extract search parameters
        name = search_criteria.get("name")
        email = search_criteria.get("email")
        phone = search_criteria.get("phone")
        cedula = search_criteria.get("cedula")
        limit = search_criteria.get("limit", DEFAULT_SEARCH_LIMIT)

        # Comprehensive input validation
        validation_result = validate_search_input(
            name=name,
            email=email,
            phone=phone,
            cedula=cedula,
            limit=limit,
            request_id=request_id
        )

        if not validation_result["valid"]:
            logger.error(
                "Search input validation failed",
                request_id=request_id,
                validation_errors=validation_result["errors"]
            )
            return create_enhanced_error_response(
                400,
                f"Input validation failed: {'; '.join(validation_result['errors'])}",
                "VALIDATION_ERROR",
                request_id,
                start_time
            )

        # Use sanitized inputs
        sanitized = validation_result["sanitized"]
        name = sanitized.get("name")
        email = sanitized.get("email")
        phone = sanitized.get("phone")
        cedula = sanitized.get("cedula")
        limit = sanitized.get("limit", DEFAULT_SEARCH_LIMIT)

        # Check if at least one valid search criterion is provided
        active_criteria = []
        if name: active_criteria.append("name")
        if email: active_criteria.append("email")
        if phone: active_criteria.append("phone")
        if cedula: active_criteria.append("cedula")

        if not active_criteria:
            logger.error(
                "No valid search criteria after validation",
                request_id=request_id,
                original_criteria=list(search_criteria.keys())
            )
            return create_enhanced_error_response(
                400, 
                "At least one valid search criterion must be provided", 
                "NO_VALID_CRITERIA",
                request_id,
                start_time
            )

        # Test database connectivity before executing search
        try:
            logger.debug(
                "Testing database connectivity",
                request_id=request_id
            )
            db_manager._get_database_config()
            logger.debug(
                "Database connectivity test successful",
                request_id=request_id
            )
        except DatabaseError as e:
            logger.error(
                "Database connectivity test failed",
                request_id=request_id,
                error_message=str(e),
                error_code=e.error_code
            )
            return create_enhanced_error_response(
                503, 
                "Database service unavailable", 
                "DATABASE_UNAVAILABLE",
                request_id,
                start_time,
                {"database_error": str(e)}
            )

        # Execute multi-criteria search with comprehensive error handling
        try:
            logger.info(
                "Executing patient search",
                request_id=request_id,
                active_criteria=active_criteria,
                search_limit=limit
            )
            patients = execute_multi_criteria_search(name, email, phone, cedula, limit, request_id)
            
            logger.info(
                "Patient search completed successfully",
                request_id=request_id,
                results_count=len(patients),
                criteria_used=active_criteria
            )
            
        except DatabaseError as e:
            logger.error(
                "Database error during patient search",
                request_id=request_id,
                error_message=str(e),
                error_code=e.error_code,
                original_error=str(e.original_error) if e.original_error else None,
                active_criteria=active_criteria
            )
            
            # Categorize database errors for better user feedback
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                error_code = "DATABASE_CONNECTION_ERROR"
                error_message = "Database connection failed. Please try again."
            elif "permission" in str(e).lower() or "access" in str(e).lower():
                error_code = "DATABASE_ACCESS_ERROR"
                error_message = "Database access denied. Please contact support."
            else:
                error_code = e.error_code or "DATABASE_ERROR"
                error_message = f"Database operation failed: {str(e)}"
            
            return create_enhanced_error_response(
                500, 
                error_message, 
                error_code,
                request_id,
                start_time,
                {"database_error": str(e), "criteria_used": active_criteria}
            )
        
        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)

        # Prepare comprehensive search metadata
        search_metadata = {
            "criteria_used": active_criteria,
            "total_results": len(patients),
            "search_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "execution_time_ms": execution_time_ms,
            "query_type": "multi_criteria" if len(active_criteria) > 1 else "single_criteria",
            "limit_applied": limit,
            "request_id": request_id
        }

        # Log search completion
        logger.info(
            "Patient search operation completed",
            request_id=request_id,
            results_found=len(patients),
            execution_time_ms=execution_time_ms,
            criteria_used=active_criteria
        )

        # Prepare response with detailed messaging
        if patients:
            message = f"Found {len(patients)} patient(s) matching criteria"
            if len(patients) == limit:
                message += f" (limited to {limit} results)"
            
            logger.info(
                "Returning successful search results",
                request_id=request_id,
                patient_count=len(patients),
                message=message
            )
            
            return create_response(200, {
                "success": True,
                "patients": patients,
                "search_metadata": search_metadata,
                "message": message
            })
        else:
            logger.info(
                "No patients found for search criteria",
                request_id=request_id,
                criteria_used=active_criteria
            )
            
            return create_response(200, {
                "success": True,
                "patients": [],
                "search_metadata": search_metadata,
                "message": "No patients found matching the provided criteria"
            })

    except DatabaseError as e:
        logger.error(
            "Database error in handle_search_patient",
            request_id=request_id,
            error_message=str(e),
            error_code=e.error_code,
            original_error=str(e.original_error) if e.original_error else None
        )
        
        return create_enhanced_error_response(
            500, 
            f"Database error: {str(e)}", 
            e.error_code or "DATABASE_ERROR",
            request_id,
            start_time,
            {"error_type": "database_error"}
        )
        
    except Exception as e:
        logger.error(
            "Unexpected error in handle_search_patient",
            request_id=request_id,
            error_message=str(e),
            error_type=type(e).__name__
        )
        
        return create_enhanced_error_response(
            500, 
            f"Search operation failed: {str(e)}", 
            "SEARCH_ERROR",
            request_id,
            start_time,
            {"error_type": "unexpected_error"}
        )


def handle_list_recent_patients(limit: int = 5, request_id: str = "unknown") -> Dict[str, Any]:
    """
    Handle listing recent patients.

    Args:
        limit: Maximum number of patients to return

    Returns:
        Dict containing the response with consistent format
    """
    start_time = time.time()
    
    try:
        logger.info(
            "Listing recent patients",
            request_id=request_id,
            requested_limit=limit
        )

        # Validate and ensure limit is within bounds
        try:
            limit = int(limit)
            limit = min(max(1, limit), MAX_SEARCH_LIMIT)
        except (ValueError, TypeError):
            logger.warning(
                "Invalid limit for recent patients, using default",
                request_id=request_id,
                invalid_limit=limit
            )
            limit = 5

        # Get recent patients from the database (ordered by updated_at)
        patients = get_recent_patients(limit, request_id)
        
        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)

        # Prepare search metadata
        search_metadata = {
            "criteria_used": ["recent"],
            "total_results": len(patients),
            "search_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "execution_time_ms": execution_time_ms,
            "request_id": request_id
        }

        logger.info(
            "Recent patients retrieved successfully",
            request_id=request_id,
            patient_count=len(patients),
            execution_time_ms=execution_time_ms
        )

        return create_response(200, {
            "success": True,
            "patients": patients,
            "search_metadata": search_metadata,
            "message": f"Found {len(patients)} recent patients"
        })

    except DatabaseError as e:
        logger.error(
            "Database error in handle_list_recent_patients",
            request_id=request_id,
            error_message=str(e),
            error_code=e.error_code
        )
        return create_enhanced_error_response(
            500, 
            f"Database error: {str(e)}", 
            e.error_code or "DATABASE_ERROR",
            request_id,
            start_time
        )
    except Exception as e:
        logger.error(
            "Unexpected error in handle_list_recent_patients",
            request_id=request_id,
            error_message=str(e),
            error_type=type(e).__name__
        )
        return create_enhanced_error_response(
            500, 
            f"List error: {str(e)}", 
            "LIST_ERROR",
            request_id,
            start_time
        )


def handle_get_patient_by_id(patient_id: str, request_id: str = "unknown") -> Dict[str, Any]:
    """
    Handle getting patient by exact ID.

    Args:
        patient_id: The patient ID

    Returns:
        Dict containing the response with consistent format
    """
    start_time = time.time()
    
    try:
        logger.info(
            "Getting patient by ID",
            request_id=request_id,
            patient_id_provided=bool(patient_id)
        )

        # Validate patient ID
        if not patient_id:
            logger.error(
                "Patient ID is required but not provided",
                request_id=request_id
            )
            return create_enhanced_error_response(
                400, 
                "Patient ID is required", 
                "MISSING_PATIENT_ID",
                request_id,
                start_time
            )

        if not isinstance(patient_id, str):
            logger.error(
                "Patient ID must be a string",
                request_id=request_id,
                patient_id_type=type(patient_id).__name__
            )
            return create_enhanced_error_response(
                400, 
                "Patient ID must be a string", 
                "INVALID_PATIENT_ID_TYPE",
                request_id,
                start_time
            )

        patient_id = patient_id.strip()
        if not patient_id:
            logger.error(
                "Patient ID cannot be empty",
                request_id=request_id
            )
            return create_enhanced_error_response(
                400, 
                "Patient ID cannot be empty", 
                "EMPTY_PATIENT_ID",
                request_id,
                start_time
            )

        patient = search_by_patient_id(patient_id, request_id)
        
        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)

        # Prepare search metadata
        search_metadata = {
            "criteria_used": ["patient_id"],
            "total_results": 1 if patient else 0,
            "search_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "execution_time_ms": execution_time_ms,
            "request_id": request_id
        }

        if patient:
            logger.info(
                "Patient found by ID",
                request_id=request_id,
                patient_name=patient.get('full_name', 'Unknown'),
                execution_time_ms=execution_time_ms
            )
            
            return create_response(200, {
                "success": True,
                "patients": [patient],
                "search_metadata": search_metadata,
                "message": f"Patient found: {patient['full_name']}"
            })
        else:
            logger.info(
                "No patient found with provided ID",
                request_id=request_id,
                execution_time_ms=execution_time_ms
            )
            
            return create_response(200, {
                "success": True,
                "patients": [],
                "search_metadata": search_metadata,
                "message": f"No patient found with ID: {patient_id}"
            })

    except DatabaseError as e:
        logger.error(
            "Database error in handle_get_patient_by_id",
            request_id=request_id,
            error_message=str(e),
            error_code=e.error_code
        )
        return create_enhanced_error_response(
            500, 
            f"Database error: {str(e)}", 
            e.error_code or "DATABASE_ERROR",
            request_id,
            start_time
        )
    except Exception as e:
        logger.error(
            "Unexpected error in handle_get_patient_by_id",
            request_id=request_id,
            error_message=str(e),
            error_type=type(e).__name__
        )
        return create_enhanced_error_response(
            500, 
            f"Get patient error: {str(e)}", 
            "GET_ERROR",
            request_id,
            start_time
        )


def execute_multi_criteria_search(
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    cedula: Optional[str] = None,
    limit: int = DEFAULT_SEARCH_LIMIT,
    request_id: str = "unknown"
) -> List[Dict[str, Any]]:
    """
    Execute multi-criteria patient search using AND logic with optimized query performance.
    
    Args:
        name: Full name for fuzzy matching (optional)
        email: Email address for exact matching (optional)
        phone: Phone number for exact matching (optional)
        cedula: National ID for exact matching (optional)
        limit: Maximum number of results to return
        
    Returns:
        List of patient dictionaries matching ALL provided criteria
        
    Raises:
        DatabaseError: If database operation fails
    """
    try:
        # Validate that at least one search criterion is provided
        if not any([name, email, phone, cedula]):
            logger.warning(
                "No search criteria provided to multi-criteria search",
                request_id=request_id
            )
            return []
        
        # Build WHERE clause conditions with optimized ordering
        # Order conditions by selectivity: exact matches first (most selective)
        where_conditions = []
        parameters = []
        
        # 1. Cedula condition (most selective - unique identifier)
        if cedula:
            where_conditions.append("cedula = :cedula")
            parameters.append(db_manager.create_parameter('cedula', cedula.strip(), 'string'))
        
        # 2. Email condition (highly selective - should be unique)
        if email:
            where_conditions.append("LOWER(email) = LOWER(:email)")
            parameters.append(db_manager.create_parameter('email', email.strip(), 'string'))
        
        # 3. Phone condition (moderately selective)
        if phone:
            where_conditions.append("phone = :phone")
            parameters.append(db_manager.create_parameter('phone', phone.strip(), 'string'))
        
        # 4. Name condition (least selective - fuzzy matching)
        if name:
            where_conditions.append("LOWER(full_name) LIKE LOWER(:name_pattern)")
            parameters.append(db_manager.create_parameter('name_pattern', f"%{name.strip()}%", 'string'))
        
        # Build the complete SQL query with optimized ordering
        sql = f"""
        SELECT 
            patient_id, 
            full_name, 
            email, 
            phone, 
            cedula, 
            date_of_birth, 
            created_at, 
            updated_at
        FROM patients
        WHERE {' AND '.join(where_conditions)}
        ORDER BY 
            CASE 
                WHEN cedula = :order_cedula THEN 1
                WHEN LOWER(email) = LOWER(:order_email) THEN 2
                WHEN phone = :order_phone THEN 3
                WHEN LOWER(full_name) = LOWER(:order_exact_name) THEN 4
                WHEN LOWER(full_name) LIKE LOWER(:order_name_starts) THEN 5
                ELSE 6
            END,
            full_name ASC
        LIMIT :limit
        """
        
        # Add ordering parameters (use provided values or empty strings for non-provided criteria)
        parameters.extend([
            db_manager.create_parameter('order_cedula', cedula.strip() if cedula else '', 'string'),
            db_manager.create_parameter('order_email', email.strip() if email else '', 'string'),
            db_manager.create_parameter('order_phone', phone.strip() if phone else '', 'string'),
            db_manager.create_parameter('order_exact_name', name.strip() if name else '', 'string'),
            db_manager.create_parameter('order_name_starts', f"{name.strip()}%" if name else '', 'string'),
            db_manager.create_parameter('limit', limit, 'long')
        ])
        
        logger.debug(
            "Executing optimized multi-criteria search",
            request_id=request_id,
            where_conditions=where_conditions,
            parameter_count=len(parameters)
        )
        
        # Execute query with comprehensive error handling
        try:
            response = db_manager.execute_sql(sql, parameters)
        except DatabaseError as e:
            # Re-raise database errors with additional context
            logger.error(
                "Database query execution failed in multi-criteria search",
                request_id=request_id,
                error_message=str(e),
                error_code=e.error_code
            )
            raise DatabaseError(
                f"Multi-criteria search query failed: {e}",
                e.error_code or "QUERY_EXECUTION_ERROR",
                e.original_error
            )
        
        records = response.get('records', [])
        
        if records:
            try:
                patients = db_manager.parse_records(records, response.get('columnMetadata', []))
                logger.info(
                    "Multi-criteria search found patients",
                    request_id=request_id,
                    patient_count=len(patients)
                )
                
                # Validate parsed results
                for i, patient in enumerate(patients):
                    if not patient.get('patient_id'):
                        logger.warning(
                            "Patient record missing patient_id",
                            request_id=request_id,
                            patient_index=i,
                            patient_name=patient.get('full_name', 'Unknown')
                        )
                
                return patients
            except Exception as e:
                logger.error(
                    "Failed to parse query results",
                    request_id=request_id,
                    error_message=str(e),
                    error_type=type(e).__name__
                )
                raise DatabaseError(
                    f"Failed to parse search results: {str(e)}",
                    "RESULT_PARSING_ERROR",
                    e
                )
        
        logger.info(
            "Multi-criteria search found no patients",
            request_id=request_id
        )
        return []
        
    except DatabaseError:
        # Re-raise database errors as-is
        raise
    except Exception as e:
        logger.error(
            "Unexpected error in multi-criteria search",
            request_id=request_id,
            error_message=str(e),
            error_type=type(e).__name__
        )
        raise DatabaseError(
            f"Multi-criteria search failed: {str(e)}", 
            "SEARCH_ERROR", 
            e
        )


def search_by_phone(phone: str, request_id: str = "unknown") -> Optional[Dict[str, Any]]:
    """
    Search patient by phone number using exact matching with input validation.

    Args:
        phone: Patient phone number

    Returns:
        Patient data or None
        
    Raises:
        DatabaseError: If database operation fails
    """
    try:
        # Input validation
        if not phone or not phone.strip():
            logger.warning(
                "Empty phone number provided to search_by_phone",
                request_id=request_id
            )
            return None
        
        phone = phone.strip()
        
        # Optimized query with index hint (assuming phone has an index)
        sql = """
        SELECT 
            patient_id, 
            full_name, 
            email, 
            phone, 
            cedula, 
            date_of_birth, 
            created_at, 
            updated_at
        FROM patients
        WHERE phone = :phone
        LIMIT 1
        """

        parameters = [
            db_manager.create_parameter('phone', phone, 'string')
        ]

        logger.debug(
            "Searching patient by phone",
            request_id=request_id,
            phone_prefix=phone[:4] + "****"
        )
        
        try:
            response = db_manager.execute_sql(sql, parameters)
        except DatabaseError as e:
            logger.error(
                "Database query failed for phone search",
                request_id=request_id,
                error_message=str(e),
                error_code=e.error_code
            )
            raise DatabaseError(
                f"Phone search query failed: {e}",
                e.error_code or "PHONE_QUERY_ERROR",
                e.original_error
            )
        
        records = response.get('records', [])

        if records:
            try:
                patients = db_manager.parse_records(records, response.get('columnMetadata', []))
                if patients and patients[0]:
                    logger.info(
                        "Found patient by phone",
                        request_id=request_id,
                        patient_name=patients[0].get('full_name', 'Unknown')
                    )
                    return patients[0]
            except Exception as e:
                logger.error(
                    "Failed to parse phone search results",
                    request_id=request_id,
                    error_message=str(e),
                    error_type=type(e).__name__
                )
                raise DatabaseError(
                    f"Failed to parse phone search results: {str(e)}",
                    "PHONE_RESULT_PARSING_ERROR",
                    e
                )

        logger.debug(
            "No patient found with phone",
            request_id=request_id,
            phone_prefix=phone[:4] + "****"
        )
        return None

    except DatabaseError:
        # Re-raise database errors as-is
        raise
    except Exception as e:
        logger.error(
            "Unexpected error in phone search",
            request_id=request_id,
            error_message=str(e),
            error_type=type(e).__name__
        )
        raise DatabaseError(f"Phone search failed: {str(e)}", "PHONE_SEARCH_ERROR", e)


def search_by_cedula(cedula: str, request_id: str = "unknown") -> Optional[Dict[str, Any]]:
    """
    Search patient by cedula (national ID) using exact matching with input validation.

    Args:
        cedula: Patient cedula/national ID

    Returns:
        Patient data or None
        
    Raises:
        DatabaseError: If database operation fails
    """
    try:
        # Input validation
        if not cedula or not cedula.strip():
            logger.warning(
                "Empty cedula provided to search_by_cedula",
                request_id=request_id
            )
            return None
        
        cedula = cedula.strip()
        
        # Basic cedula format validation (assuming numeric format)
        if not cedula.replace('-', '').replace('.', '').isdigit():
            logger.warning(
                "Invalid cedula format provided",
                request_id=request_id,
                cedula_length=len(cedula)
            )
            return None
        
        # Optimized query (cedula should be unique and indexed)
        sql = """
        SELECT 
            patient_id, 
            full_name, 
            email, 
            phone, 
            cedula, 
            date_of_birth, 
            created_at, 
            updated_at
        FROM patients
        WHERE cedula = :cedula
        LIMIT 1
        """

        parameters = [
            db_manager.create_parameter('cedula', cedula, 'string')
        ]

        logger.debug(
            "Searching patient by cedula",
            request_id=request_id,
            cedula_prefix=cedula[:3] + "****"
        )
        
        try:
            response = db_manager.execute_sql(sql, parameters)
        except DatabaseError as e:
            logger.error(f"Database query failed for cedula search: {e}")
            raise DatabaseError(
                f"Cedula search query failed: {e}",
                e.error_code or "CEDULA_QUERY_ERROR",
                e.original_error
            )
        
        records = response.get('records', [])

        if records:
            try:
                patients = db_manager.parse_records(records, response.get('columnMetadata', []))
                if patients and patients[0]:
                    logger.info(f"Found patient by cedula: {patients[0].get('full_name', 'Unknown')}")
                    return patients[0]
            except Exception as e:
                logger.error(f"Failed to parse cedula search results: {e}")
                raise DatabaseError(
                    f"Failed to parse cedula search results: {str(e)}",
                    "CEDULA_RESULT_PARSING_ERROR",
                    e
                )

        logger.debug(f"No patient found with cedula: {cedula[:3]}****")
        return None

    except DatabaseError:
        # Re-raise database errors as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in cedula search: {str(e)}")
        raise DatabaseError(f"Cedula search failed: {str(e)}", "CEDULA_SEARCH_ERROR", e)


def search_by_patient_id(patient_id: str, request_id: str = "unknown") -> Optional[Dict[str, Any]]:
    """
    Search patient by patient ID using exact matching with input validation.

    Args:
        patient_id: Patient ID

    Returns:
        Patient data or None
        
    Raises:
        DatabaseError: If database operation fails
    """
    try:
        # Input validation
        if not patient_id or not patient_id.strip():
            logger.warning("Empty patient_id provided to search_by_patient_id")
            return None
        
        patient_id = patient_id.strip()
        
        # Optimized query (patient_id should be primary key)
        sql = """
        SELECT 
            patient_id, 
            full_name, 
            email, 
            phone, 
            cedula, 
            date_of_birth, 
            created_at, 
            updated_at
        FROM patients
        WHERE patient_id = :patient_id
        LIMIT 1
        """

        parameters = [
            db_manager.create_parameter('patient_id', patient_id, 'string')
        ]

        logger.debug(f"Searching patient by ID: {patient_id}")
        
        try:
            response = db_manager.execute_sql(sql, parameters)
        except DatabaseError as e:
            logger.error(f"Database query failed for patient ID search: {e}")
            raise DatabaseError(
                f"Patient ID search query failed: {e}",
                e.error_code or "PATIENT_ID_QUERY_ERROR",
                e.original_error
            )
        
        records = response.get('records', [])

        if records:
            try:
                patients = db_manager.parse_records(records, response.get('columnMetadata', []))
                if patients and patients[0]:
                    logger.info(f"Found patient by ID: {patients[0].get('full_name', 'Unknown')}")
                    return patients[0]
            except Exception as e:
                logger.error(f"Failed to parse patient ID search results: {e}")
                raise DatabaseError(
                    f"Failed to parse patient ID search results: {str(e)}",
                    "PATIENT_ID_RESULT_PARSING_ERROR",
                    e
                )

        logger.debug(f"No patient found with ID: {patient_id}")
        return None

    except DatabaseError:
        # Re-raise database errors as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in patient ID search: {str(e)}")
        raise DatabaseError(f"Patient ID search failed: {str(e)}", "PATIENT_ID_SEARCH_ERROR", e)


def search_by_email(email: str, request_id: str = "unknown") -> Optional[Dict[str, Any]]:
    """
    Search patient by email using exact matching (case-insensitive) with input validation.

    Args:
        email: Patient email

    Returns:
        Patient data or None
        
    Raises:
        DatabaseError: If database operation fails
    """
    try:
        # Input validation
        if not email or not email.strip():
            logger.warning("Empty email provided to search_by_email")
            return None
        
        email = email.strip().lower()
        
        # Basic email format validation
        if '@' not in email or '.' not in email.split('@')[-1]:
            logger.warning(f"Invalid email format: {email}")
            return None
        
        # Optimized query (email should be unique and indexed)
        sql = """
        SELECT 
            patient_id, 
            full_name, 
            email, 
            phone, 
            cedula, 
            date_of_birth, 
            created_at, 
            updated_at
        FROM patients
        WHERE LOWER(email) = LOWER(:email)
        LIMIT 1
        """

        parameters = [
            db_manager.create_parameter('email', email, 'string')
        ]

        logger.debug(f"Searching patient by email: {email.split('@')[0][:3]}***@{email.split('@')[1]}")
        
        try:
            response = db_manager.execute_sql(sql, parameters)
        except DatabaseError as e:
            logger.error(f"Database query failed for email search: {e}")
            raise DatabaseError(
                f"Email search query failed: {e}",
                e.error_code or "EMAIL_QUERY_ERROR",
                e.original_error
            )
        
        records = response.get('records', [])

        if records:
            try:
                patients = db_manager.parse_records(records, response.get('columnMetadata', []))
                if patients and patients[0]:
                    logger.info(f"Found patient by email: {patients[0].get('full_name', 'Unknown')}")
                    return patients[0]
            except Exception as e:
                logger.error(f"Failed to parse email search results: {e}")
                raise DatabaseError(
                    f"Failed to parse email search results: {str(e)}",
                    "EMAIL_RESULT_PARSING_ERROR",
                    e
                )

        logger.debug(f"No patient found with email: {email.split('@')[0][:3]}***@{email.split('@')[1]}")
        return None

    except DatabaseError:
        # Re-raise database errors as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in email search: {str(e)}")
        raise DatabaseError(f"Email search failed: {str(e)}", "EMAIL_SEARCH_ERROR", e)


def search_by_name(full_name: str, limit: int = DEFAULT_SEARCH_LIMIT, request_id: str = "unknown") -> List[Dict[str, Any]]:
    """
    Search patients by name with optimized fuzzy matching and relevance scoring.
    Returns multiple matches ordered by relevance.

    Args:
        full_name: Full name to search for
        limit: Maximum number of results to return

    Returns:
        List of patient data ordered by match relevance
        
    Raises:
        DatabaseError: If database operation fails
    """
    try:
        # Input validation
        if not full_name or not full_name.strip():
            logger.warning("Empty name provided to search_by_name")
            return []
        
        full_name = full_name.strip()
        
        # Validate limit
        limit = min(max(1, limit), MAX_SEARCH_LIMIT)
        
        # Single optimized query with comprehensive relevance scoring
        sql = """
        SELECT 
            patient_id, 
            full_name, 
            email, 
            phone, 
            cedula, 
            date_of_birth, 
            created_at, 
            updated_at,
            CASE 
                WHEN LOWER(full_name) = LOWER(:exact_name) THEN 1
                WHEN LOWER(full_name) LIKE LOWER(:starts_with) THEN 2
                WHEN LOWER(full_name) LIKE LOWER(:name_pattern) THEN 3
                ELSE 4
            END as match_priority,
            LENGTH(full_name) as name_length
        FROM patients
        WHERE LOWER(full_name) LIKE LOWER(:name_pattern)
        ORDER BY 
            match_priority ASC,
            name_length ASC,
            full_name ASC
        LIMIT :limit
        """

        # Prepare search patterns
        name_pattern = f"%{full_name}%"
        starts_with = f"{full_name}%"

        parameters = [
            db_manager.create_parameter('exact_name', full_name, 'string'),
            db_manager.create_parameter('starts_with', starts_with, 'string'),
            db_manager.create_parameter('name_pattern', name_pattern, 'string'),
            db_manager.create_parameter('limit', limit, 'long')
        ]

        logger.debug(f"Searching patients by name: '{full_name}' (limit: {limit})")
        
        try:
            response = db_manager.execute_sql(sql, parameters)
        except DatabaseError as e:
            logger.error(f"Database query failed for name search: {e}")
            raise DatabaseError(
                f"Name search query failed: {e}",
                e.error_code or "NAME_QUERY_ERROR",
                e.original_error
            )
        
        records = response.get('records', [])

        if records:
            try:
                patients = db_manager.parse_records(records, response.get('columnMetadata', []))
                
                # Remove internal scoring fields from results
                cleaned_patients = []
                for patient in patients:
                    # Remove match_priority and name_length fields if present
                    cleaned_patient = {k: v for k, v in patient.items() 
                                     if k not in ['match_priority', 'name_length']}
                    cleaned_patients.append(cleaned_patient)
                
                if cleaned_patients:
                    match_type = "exact" if patients[0].get('match_priority') == 1 else "fuzzy"
                    logger.info(f"Found {len(cleaned_patients)} {match_type} matches for '{full_name}'")
                    return cleaned_patients
                    
            except Exception as e:
                logger.error(f"Failed to parse name search results: {e}")
                raise DatabaseError(
                    f"Failed to parse name search results: {str(e)}",
                    "NAME_RESULT_PARSING_ERROR",
                    e
                )

        logger.debug(f"No matches found for name: '{full_name}'")
        return []

    except DatabaseError:
        # Re-raise database errors as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in name search: {str(e)}")
        raise DatabaseError(f"Name search failed: {str(e)}", "NAME_SEARCH_ERROR", e)


def get_recent_patients(limit: int = 5, request_id: str = "unknown") -> List[Dict[str, Any]]:
    """
    Get recent patients from the database using optimized query with proper error handling.

    Args:
        limit: Maximum number of patients to return

    Returns:
        List of patient data ordered by most recent activity
        
    Raises:
        DatabaseError: If database operation fails
    """
    try:
        # Validate and constrain limit
        limit = min(max(1, limit), MAX_SEARCH_LIMIT)
        
        # Optimized query with proper indexing hints
        sql = """
        SELECT 
            patient_id, 
            full_name, 
            email, 
            phone, 
            cedula, 
            date_of_birth, 
            created_at, 
            updated_at
        FROM patients
        ORDER BY 
            updated_at DESC NULLS LAST, 
            created_at DESC
        LIMIT :limit
        """

        parameters = [
            db_manager.create_parameter('limit', limit, 'long')
        ]

        logger.debug(f"Getting recent patients (limit: {limit})")
        
        try:
            response = db_manager.execute_sql(sql, parameters)
        except DatabaseError as e:
            logger.error(f"Database query failed for recent patients: {e}")
            raise DatabaseError(
                f"Recent patients query failed: {e}",
                e.error_code or "RECENT_PATIENTS_QUERY_ERROR",
                e.original_error
            )
        
        records = response.get('records', [])

        if records:
            try:
                patients = db_manager.parse_records(records, response.get('columnMetadata', []))
                logger.info(f"Retrieved {len(patients)} recent patients")
                return patients
            except Exception as e:
                logger.error(f"Failed to parse recent patients results: {e}")
                raise DatabaseError(
                    f"Failed to parse recent patients results: {str(e)}",
                    "RECENT_PATIENTS_PARSING_ERROR",
                    e
                )

        logger.info("No recent patients found")
        return []

    except DatabaseError:
        # Re-raise database errors as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting recent patients: {str(e)}")
        raise DatabaseError(f"Recent patients query failed: {str(e)}", "RECENT_PATIENTS_ERROR", e)

