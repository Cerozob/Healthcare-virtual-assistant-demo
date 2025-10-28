"""
Patients API Lambda Function.
Handles CRUD operations for patient management.

Endpoints:
- GET /patients - List patients with pagination
- POST /patients - Create new patient
- GET /patients/{id} - Get patient by ID
- PUT /patients/{id} - Update patient
- DELETE /patients/{id} - Delete patient
"""

import logging
import json
from typing import Dict, Any
from shared.database import DatabaseManager, DatabaseError
from shared.utils import (
    create_response, create_error_response, parse_event_body,
    extract_path_parameters, extract_query_parameters, validate_required_fields,
    validate_pagination_params, handle_exceptions, generate_uuid, get_current_timestamp
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize database manager
db_manager = DatabaseManager()


@handle_exceptions
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for patients API.
    Supports both API Gateway and MCP Gateway invocations.
    """
    # Check if this is an MCP Gateway invocation
    if _is_mcp_gateway_event(event):
        return handle_mcp_gateway_request(event)
    
    # Handle API Gateway requests (existing logic)
    http_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method', '')
    path = event.get('path') or event.get('requestContext', {}).get('http', {}).get('path', '')
    path_params = event.get('pathParameters') or {}
    
    # Log the event for debugging
    logger.info(f"Received API Gateway request: method={http_method}, path={path}")
    
    # Normalize path by removing stage prefix if present
    normalized_path = path
    if path.startswith('/v1/'):
        normalized_path = path[3:]  # Remove '/v1' prefix
    
    # Route to appropriate handler
    if normalized_path == '/patients':
        if http_method == 'GET':
            return list_patients(event)
        elif http_method == 'POST':
            return create_patient(event)
    elif normalized_path.startswith('/patients/') and path_params and 'id' in path_params:
        patient_id = path_params['id']
        if http_method == 'GET':
            return get_patient(patient_id)
        elif http_method == 'PUT':
            return update_patient(patient_id, event)
        elif http_method == 'DELETE':
            return delete_patient(patient_id)
    
    return create_error_response(404, "Endpoint not found")


def _is_mcp_gateway_event(event: Dict[str, Any]) -> bool:
    """
    Check if the event is from MCP Gateway.
    MCP Gateway events have a different structure than API Gateway events.
    """
    # MCP Gateway events typically have 'action' parameter and no HTTP method/path
    return (
        'action' in event and 
        'httpMethod' not in event and 
        'requestContext' not in event
    )


def handle_mcp_gateway_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle MCP Gateway requests with action-based routing.
    
    Expected event structure:
    {
        "action": "list|get|create|update|delete",
        "patient_id": "optional-patient-id",
        "patient_data": {...},
        "pagination": {...}
    }
    """
    try:
        action = event.get('action')
        logger.info(f"Received MCP Gateway request: action={action}")
        
        if action == 'list':
            # Convert MCP parameters to API Gateway format
            query_params = {}
            if 'pagination' in event:
                pagination = event['pagination']
                query_params['limit'] = str(pagination.get('limit', 50))
                query_params['offset'] = str(pagination.get('offset', 0))
            
            # Create mock API Gateway event
            mock_event = {
                'queryStringParameters': query_params
            }
            return list_patients(mock_event)
            
        elif action == 'get':
            patient_id = event.get('patient_id')
            if not patient_id:
                return create_error_response(400, "patient_id required for get action")
            return get_patient(patient_id)
            
        elif action == 'create':
            patient_data = event.get('patient_data')
            if not patient_data:
                return create_error_response(400, "patient_data required for create action")
            
            # Create mock API Gateway event
            mock_event = {
                'body': json.dumps(patient_data)
            }
            return create_patient(mock_event)
            
        elif action == 'update':
            patient_id = event.get('patient_id')
            patient_data = event.get('patient_data')
            if not patient_id:
                return create_error_response(400, "patient_id required for update action")
            if not patient_data:
                return create_error_response(400, "patient_data required for update action")
            
            # Create mock API Gateway event
            mock_event = {
                'body': json.dumps(patient_data)
            }
            return update_patient(patient_id, mock_event)
            
        elif action == 'delete':
            patient_id = event.get('patient_id')
            if not patient_id:
                return create_error_response(400, "patient_id required for delete action")
            return delete_patient(patient_id)
            
        else:
            return create_error_response(400, f"Unknown action: {action}")
            
    except Exception as e:
        logger.error(f"Error handling MCP Gateway request: {str(e)}")
        return create_error_response(500, f"Internal server error: {str(e)}")


def list_patients(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle GET /patients - List patients with pagination.
    
    Query parameters:
    - limit: Number of patients to return (default: 50, max: 1000)
    - offset: Number of patients to skip (default: 0)
    
    Returns:
        List of patients with pagination info
    """
    try:
        query_params = extract_query_parameters(event)
        pagination = validate_pagination_params(query_params)
        
        sql = """
        SELECT patient_id, full_name, email, cedula, date_of_birth, phone, created_at, updated_at
        FROM patients
        ORDER BY full_name
        LIMIT :limit OFFSET :offset
        """
        
        parameters = [
            db_manager.create_parameter('limit', pagination['limit'], 'long'),
            db_manager.create_parameter('offset', pagination['offset'], 'long')
        ]
        
        response = db_manager.execute_sql(sql, parameters)
        patients = db_manager.parse_records(
            response.get('records', []),
            response.get('columnMetadata', [])
        )
        
        # Get total count for pagination
        count_sql = "SELECT COUNT(*) as total FROM patients"
        count_response = db_manager.execute_sql(count_sql)
        total_count = 0
        if count_response.get('records'):
            total_count = count_response['records'][0][0].get('longValue', 0)
        
        return create_response(200, {
            'patients': patients,
            'pagination': {
                'limit': pagination['limit'],
                'offset': pagination['offset'],
                'total': total_count,
                'count': len(patients)
            }
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in list_patients: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in list_patients: {str(e)}")
        return create_error_response(500, "Internal server error")


def create_patient(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle POST /patients - Create new patient.
    
    Required fields:
    - full_name: Patient's full name
    - date_of_birth: Patient's date of birth (YYYY-MM-DD format)
    
    Returns:
        Created patient data
    """
    try:
        # Ensure patients table exists
        ensure_patients_table_exists()
        
        body = parse_event_body(event)
        
        # Validate required fields
        validation_error = validate_required_fields(body, ['full_name', 'date_of_birth'])
        if validation_error:
            return create_error_response(400, validation_error, "VALIDATION_ERROR")
        
        # Generate patient ID
        patient_id = generate_uuid()
        
        # Generate a demo email for the patient
        demo_email = f"patient.{patient_id.lower()}@demo.hospital.com"
        
        sql = """
        INSERT INTO patients (patient_id, full_name, email, cedula, date_of_birth, phone, created_at, updated_at)
        VALUES (:patient_id, :full_name, :email, :cedula, :date_of_birth, :phone, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        RETURNING patient_id, full_name, email, cedula, date_of_birth, phone, created_at, updated_at
        """
        
        parameters = [
            db_manager.create_parameter('patient_id', patient_id, 'string'),
            db_manager.create_parameter('full_name', body['full_name'], 'string'),
            db_manager.create_parameter('email', demo_email, 'string'),
            db_manager.create_parameter('cedula', body.get('cedula'), 'string'),
            db_manager.create_parameter('date_of_birth', body['date_of_birth'], 'string'),
            db_manager.create_parameter('phone', body.get('phone'), 'string')
        ]
        
        response = db_manager.execute_sql(sql, parameters)
        
        if not response.get('records'):
            return create_error_response(500, "Failed to create patient")
        
        patient = db_manager.parse_records(
            response['records'],
            response.get('columnMetadata', [])
        )[0]
        
        logger.info(f"Created patient: {patient_id}")
        
        return create_response(201, {
            'message': 'Patient created successfully',
            'patient': patient
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in create_patient: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in create_patient: {str(e)}")
        return create_error_response(500, "Internal server error")


def get_patient(patient_id: str) -> Dict[str, Any]:
    """
    Handle GET /patients/{id} - Get patient by ID.
    
    Args:
        patient_id: Patient ID
        
    Returns:
        Patient data or 404 if not found
    """
    try:
        sql = """
        SELECT patient_id, full_name, email, cedula, date_of_birth, phone, created_at, updated_at
        FROM patients
        WHERE patient_id = :patient_id
        """
        
        parameters = [
            db_manager.create_parameter('patient_id', patient_id, 'string')
        ]
        
        response = db_manager.execute_sql(sql, parameters)
        records = response.get('records', [])
        
        if not records:
            return create_error_response(404, "Patient not found", "PATIENT_NOT_FOUND")
        
        patient = db_manager.parse_records(
            records,
            response.get('columnMetadata', [])
        )[0]
        
        return create_response(200, {'patient': patient})
        
    except DatabaseError as e:
        logger.error(f"Database error in get_patient: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in get_patient: {str(e)}")
        return create_error_response(500, "Internal server error")


def update_patient(patient_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle PUT /patients/{id} - Update patient.
    
    Args:
        patient_id: Patient ID
        event: Lambda event containing update data
        
    Returns:
        Updated patient data or 404 if not found
    """
    try:
        body = parse_event_body(event)
        
        # Build dynamic update query
        update_fields = []
        parameters = [db_manager.create_parameter('patient_id', patient_id, 'string')]
        
        if 'full_name' in body and body['full_name']:
            update_fields.append('full_name = :full_name')
            parameters.append(db_manager.create_parameter('full_name', body['full_name'], 'string'))
        
        if 'cedula' in body:
            update_fields.append('cedula = :cedula')
            parameters.append(db_manager.create_parameter('cedula', body['cedula'], 'string'))
        
        if 'phone' in body:
            update_fields.append('phone = :phone')
            parameters.append(db_manager.create_parameter('phone', body['phone'], 'string'))
        
        if 'date_of_birth' in body and body['date_of_birth']:
            update_fields.append('date_of_birth = :date_of_birth')
            parameters.append(db_manager.create_parameter('date_of_birth', body['date_of_birth'], 'string'))
        
        if not update_fields:
            return create_error_response(400, "No fields to update", "NO_UPDATE_FIELDS")
        
        # Add updated timestamp
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        
        sql = f"""
        UPDATE patients
        SET {', '.join(update_fields)}
        WHERE patient_id = :patient_id
        RETURNING patient_id, full_name, email, cedula, date_of_birth, phone, created_at, updated_at
        """
        
        response = db_manager.execute_sql(sql, parameters)
        records = response.get('records', [])
        
        if not records:
            return create_error_response(404, "Patient not found", "PATIENT_NOT_FOUND")
        
        patient = db_manager.parse_records(
            records,
            response.get('columnMetadata', [])
        )[0]
        
        logger.info(f"Updated patient: {patient_id}")
        
        return create_response(200, {
            'message': 'Patient updated successfully',
            'patient': patient
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in update_patient: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in update_patient: {str(e)}")
        return create_error_response(500, "Internal server error")


def ensure_patients_table_exists() -> None:
    """Ensure patients table exists by creating it if necessary."""
    try:
        sql = """
        CREATE TABLE IF NOT EXISTS patients (
            patient_id VARCHAR(255) PRIMARY KEY,
            full_name VARCHAR(200) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            date_of_birth DATE,
            phone VARCHAR(20),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """
        db_manager.execute_sql(sql, [])
        logger.info("Ensured patients table exists")
    except Exception as e:
        logger.warning(f"Could not ensure patients table exists: {e}")


def delete_patient(patient_id: str) -> Dict[str, Any]:
    """
    Handle DELETE /patients/{id} - Delete patient.
    
    Args:
        patient_id: Patient ID
        
    Returns:
        Success message or 404 if not found
    """
    try:
        sql = """
        DELETE FROM patients
        WHERE patient_id = :patient_id
        RETURNING patient_id
        """
        
        parameters = [
            db_manager.create_parameter('patient_id', patient_id, 'string')
        ]
        
        response = db_manager.execute_sql(sql, parameters)
        records = response.get('records', [])
        
        if not records:
            return create_error_response(404, "Patient not found", "PATIENT_NOT_FOUND")
        
        logger.info(f"Deleted patient: {patient_id}")
        
        return create_response(200, {
            'message': 'Patient deleted successfully',
            'patient_id': patient_id
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in delete_patient: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in delete_patient: {str(e)}")
        return create_error_response(500, "Internal server error")
