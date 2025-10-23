"""
Medics API Lambda Function.
Handles CRUD operations for medical professionals management.

Endpoints:
- GET /medics - List medics with pagination
- POST /medics - Create new medic
- GET /medics/{id} - Get medic by ID
- PUT /medics/{id} - Update medic
- DELETE /medics/{id} - Delete medic
"""

import logging
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
    Main Lambda handler for medics API.
    Routes requests to appropriate handlers based on HTTP method and path.
    """
    http_method = event.get('httpMethod', '')
    path = event.get('path', '')
    path_params = extract_path_parameters(event)
    
    # Log the event for debugging
    logger.info(f"Received request: method={http_method}, path={path}")
    
    # Normalize path by removing stage prefix if present
    normalized_path = path
    if path.startswith('/v1/'):
        normalized_path = path[3:]  # Remove '/v1' prefix
    
    # Route to appropriate handler
    if normalized_path == '/medics':
        if http_method == 'GET':
            return list_medics(event)
        elif http_method == 'POST':
            return create_medic(event)
    elif normalized_path.startswith('/medics/') and 'id' in path_params:
        medic_id = path_params['id']
        if http_method == 'GET':
            return get_medic(medic_id)
        elif http_method == 'PUT':
            return update_medic(medic_id, event)
        elif http_method == 'DELETE':
            return delete_medic(medic_id)
    
    return create_error_response(404, "Endpoint not found")


def list_medics(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle GET /medics - List medics with pagination.
    
    Query parameters:
    - limit: Number of medics to return (default: 50, max: 1000)
    - offset: Number of medics to skip (default: 0)
    - specialty: Filter by specialty (optional)
    
    Returns:
        List of medics with pagination info
    """
    try:
        query_params = extract_query_parameters(event)
        pagination = validate_pagination_params(query_params)
        specialty_filter = query_params.get('specialty')
        
        # Build query with optional specialty filter
        where_clause = ""
        parameters = [
            db_manager.create_parameter('limit', pagination['limit'], 'long'),
            db_manager.create_parameter('offset', pagination['offset'], 'long')
        ]
        
        if specialty_filter:
            where_clause = "WHERE LOWER(specialty) LIKE LOWER(:specialty)"
            parameters.append(db_manager.create_parameter('specialty', f'%{specialty_filter}%', 'string'))
        
        sql = f"""
        SELECT medic_id, full_name, specialty, license_number, created_at, updated_at
        FROM medics
        {where_clause}
        ORDER BY full_name
        LIMIT :limit OFFSET :offset
        """
        
        response = db_manager.execute_sql(sql, parameters)
        medics = db_manager.parse_records(
            response.get('records', []),
            response.get('columnMetadata', [])
        )
        
        # Get total count for pagination
        count_sql = f"SELECT COUNT(*) as total FROM medics {where_clause}"
        count_params = [p for p in parameters if p['name'] == 'specialty'] if specialty_filter else []
        count_response = db_manager.execute_sql(count_sql, count_params)
        total_count = 0
        if count_response.get('records'):
            total_count = count_response['records'][0][0].get('longValue', 0)
        
        return create_response(200, {
            'medics': medics,
            'pagination': {
                'limit': pagination['limit'],
                'offset': pagination['offset'],
                'total': total_count,
                'count': len(medics)
            },
            'filters': {
                'specialty': specialty_filter
            } if specialty_filter else {}
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in list_medics: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in list_medics: {str(e)}")
        return create_error_response(500, "Internal server error")


def create_medic(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle POST /medics - Create new medic.
    
    Required fields:
    - full_name: Medic's full name
    - specialty: Medical specialty
    - license_number: Medical license number
    
    Returns:
        Created medic data
    """
    try:
        body = parse_event_body(event)
        
        # Validate required fields
        validation_error = validate_required_fields(body, ['full_name', 'specialty', 'license_number'])
        if validation_error:
            return create_error_response(400, validation_error, "VALIDATION_ERROR")
        
        # Validate license number uniqueness
        license_check_sql = """
        SELECT COUNT(*) as count FROM medics WHERE license_number = :license_number
        """
        license_params = [db_manager.create_parameter('license_number', body['license_number'], 'string')]
        license_response = db_manager.execute_sql(license_check_sql, license_params)
        
        if license_response.get('records') and license_response['records'][0][0].get('longValue', 0) > 0:
            return create_error_response(400, "License number already exists", "DUPLICATE_LICENSE")
        
        # Generate medic ID
        medic_id = generate_uuid()
        
        sql = """
        INSERT INTO medics (medic_id, full_name, specialty, license_number, created_at, updated_at)
        VALUES (:medic_id, :full_name, :specialty, :license_number, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        RETURNING medic_id, full_name, specialty, license_number, created_at, updated_at
        """
        
        parameters = [
            db_manager.create_parameter('medic_id', medic_id, 'string'),
            db_manager.create_parameter('full_name', body['full_name'], 'string'),
            db_manager.create_parameter('specialty', body['specialty'], 'string'),
            db_manager.create_parameter('license_number', body['license_number'], 'string')
        ]
        
        response = db_manager.execute_sql(sql, parameters)
        
        if not response.get('records'):
            return create_error_response(500, "Failed to create medic")
        
        medic = db_manager.parse_records(
            response['records'],
            response.get('columnMetadata', [])
        )[0]
        
        logger.info(f"Created medic: {medic_id}")
        
        return create_response(201, {
            'message': 'Medic created successfully',
            'medic': medic
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in create_medic: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in create_medic: {str(e)}")
        return create_error_response(500, "Internal server error")


def get_medic(medic_id: str) -> Dict[str, Any]:
    """
    Handle GET /medics/{id} - Get medic by ID.
    
    Args:
        medic_id: Medic ID
        
    Returns:
        Medic data or 404 if not found
    """
    try:
        sql = """
        SELECT medic_id, full_name, specialty, license_number, created_at, updated_at
        FROM medics
        WHERE medic_id = :medic_id
        """
        
        parameters = [
            db_manager.create_parameter('medic_id', medic_id, 'string')
        ]
        
        response = db_manager.execute_sql(sql, parameters)
        records = response.get('records', [])
        
        if not records:
            return create_error_response(404, "Medic not found", "MEDIC_NOT_FOUND")
        
        medic = db_manager.parse_records(
            records,
            response.get('columnMetadata', [])
        )[0]
        
        return create_response(200, {'medic': medic})
        
    except DatabaseError as e:
        logger.error(f"Database error in get_medic: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in get_medic: {str(e)}")
        return create_error_response(500, "Internal server error")


def update_medic(medic_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle PUT /medics/{id} - Update medic.
    
    Args:
        medic_id: Medic ID
        event: Lambda event containing update data
        
    Returns:
        Updated medic data or 404 if not found
    """
    try:
        body = parse_event_body(event)
        
        # Build dynamic update query
        update_fields = []
        parameters = [db_manager.create_parameter('medic_id', medic_id, 'string')]
        
        if 'full_name' in body and body['full_name']:
            update_fields.append('full_name = :full_name')
            parameters.append(db_manager.create_parameter('full_name', body['full_name'], 'string'))
        
        if 'specialty' in body and body['specialty']:
            update_fields.append('specialty = :specialty')
            parameters.append(db_manager.create_parameter('specialty', body['specialty'], 'string'))
        
        if 'license_number' in body and body['license_number']:
            # Check for license number uniqueness (excluding current medic)
            license_check_sql = """
            SELECT COUNT(*) as count FROM medics 
            WHERE license_number = :license_number AND medic_id != :medic_id
            """
            license_params = [
                db_manager.create_parameter('license_number', body['license_number'], 'string'),
                db_manager.create_parameter('medic_id', medic_id, 'string')
            ]
            license_response = db_manager.execute_sql(license_check_sql, license_params)
            
            if license_response.get('records') and license_response['records'][0][0].get('longValue', 0) > 0:
                return create_error_response(400, "License number already exists", "DUPLICATE_LICENSE")
            
            update_fields.append('license_number = :license_number')
            parameters.append(db_manager.create_parameter('license_number', body['license_number'], 'string'))
        
        if not update_fields:
            return create_error_response(400, "No fields to update", "NO_UPDATE_FIELDS")
        
        # Add updated timestamp
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        
        sql = f"""
        UPDATE medics
        SET {', '.join(update_fields)}
        WHERE medic_id = :medic_id
        RETURNING medic_id, full_name, specialty, license_number, created_at, updated_at
        """
        
        response = db_manager.execute_sql(sql, parameters)
        records = response.get('records', [])
        
        if not records:
            return create_error_response(404, "Medic not found", "MEDIC_NOT_FOUND")
        
        medic = db_manager.parse_records(
            records,
            response.get('columnMetadata', [])
        )[0]
        
        logger.info(f"Updated medic: {medic_id}")
        
        return create_response(200, {
            'message': 'Medic updated successfully',
            'medic': medic
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in update_medic: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in update_medic: {str(e)}")
        return create_error_response(500, "Internal server error")


def delete_medic(medic_id: str) -> Dict[str, Any]:
    """
    Handle DELETE /medics/{id} - Delete medic.
    
    Args:
        medic_id: Medic ID
        
    Returns:
        Success message or 404 if not found
    """
    try:
        # Check if medic has active reservations
        reservations_check_sql = """
        SELECT COUNT(*) as count FROM reservations 
        WHERE medic_id = :medic_id AND status IN ('scheduled', 'confirmed')
        """
        reservations_params = [db_manager.create_parameter('medic_id', medic_id, 'string')]
        reservations_response = db_manager.execute_sql(reservations_check_sql, reservations_params)
        
        if reservations_response.get('records') and reservations_response['records'][0][0].get('longValue', 0) > 0:
            return create_error_response(400, "Cannot delete medic with active reservations", "ACTIVE_RESERVATIONS")
        
        sql = """
        DELETE FROM medics
        WHERE medic_id = :medic_id
        RETURNING medic_id
        """
        
        parameters = [
            db_manager.create_parameter('medic_id', medic_id, 'string')
        ]
        
        response = db_manager.execute_sql(sql, parameters)
        records = response.get('records', [])
        
        if not records:
            return create_error_response(404, "Medic not found", "MEDIC_NOT_FOUND")
        
        logger.info(f"Deleted medic: {medic_id}")
        
        return create_response(200, {
            'message': 'Medic deleted successfully',
            'medic_id': medic_id
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in delete_medic: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in delete_medic: {str(e)}")
        return create_error_response(500, "Internal server error")
