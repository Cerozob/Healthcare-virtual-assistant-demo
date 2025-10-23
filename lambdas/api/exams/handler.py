"""
Exams API Lambda Function.
Handles CRUD operations for medical exams management.

Endpoints:
- GET /exams - List exams with pagination
- POST /exams - Create new exam
- GET /exams/{id} - Get exam by ID
- PUT /exams/{id} - Update exam
- DELETE /exams/{id} - Delete exam
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
    Main Lambda handler for exams API.
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
    if normalized_path == '/exams':
        if http_method == 'GET':
            return list_exams(event)
        elif http_method == 'POST':
            return create_exam(event)
    elif normalized_path.startswith('/exams/') and 'id' in path_params:
        exam_id = path_params['id']
        if http_method == 'GET':
            return get_exam(exam_id)
        elif http_method == 'PUT':
            return update_exam(exam_id, event)
        elif http_method == 'DELETE':
            return delete_exam(exam_id)
    
    return create_error_response(404, "Endpoint not found")


def list_exams(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle GET /exams - List exams with pagination.
    
    Query parameters:
    - limit: Number of exams to return (default: 50, max: 1000)
    - offset: Number of exams to skip (default: 0)
    - exam_type: Filter by exam type (optional)
    
    Returns:
        List of exams with pagination info
    """
    try:
        query_params = extract_query_parameters(event)
        pagination = validate_pagination_params(query_params)
        exam_type_filter = query_params.get('exam_type')
        
        # Build query with optional exam type filter
        where_clause = ""
        parameters = [
            db_manager.create_parameter('limit', pagination['limit'], 'long'),
            db_manager.create_parameter('offset', pagination['offset'], 'long')
        ]
        
        if exam_type_filter:
            where_clause = "WHERE LOWER(exam_type) LIKE LOWER(:exam_type)"
            parameters.append(db_manager.create_parameter('exam_type', f'%{exam_type_filter}%', 'string'))
        
        sql = f"""
        SELECT exam_id, exam_name, exam_type, description, created_at, updated_at
        FROM exams
        {where_clause}
        ORDER BY exam_name
        LIMIT :limit OFFSET :offset
        """
        
        exams = db_manager.execute_query(sql, parameters)
        
        # Get total count for pagination
        count_sql = f"SELECT COUNT(*) as total FROM exams {where_clause}"
        count_params = [p for p in parameters if p['name'] == 'exam_type'] if exam_type_filter else []
        count_results = db_manager.execute_query(count_sql, count_params)
        total_count = count_results[0]['total'] if count_results else 0
        
        return create_response(200, {
            'exams': exams,
            'pagination': {
                'limit': pagination['limit'],
                'offset': pagination['offset'],
                'total': total_count,
                'count': len(exams)
            },
            'filters': {
                'exam_type': exam_type_filter
            } if exam_type_filter else {}
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in list_exams: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in list_exams: {str(e)}")
        return create_error_response(500, "Internal server error")


def create_exam(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle POST /exams - Create new exam.
    
    Required fields:
    - exam_name: Name of the exam
    - exam_type: Type/category of the exam
    
    Optional fields:
    - description: Exam description
    
    Returns:
        Created exam data
    """
    try:
        body = parse_event_body(event)
        
        # Validate required fields
        validation_error = validate_required_fields(body, ['exam_name', 'exam_type'])
        if validation_error:
            return create_error_response(400, validation_error, "VALIDATION_ERROR")
        
        # Validate exam name uniqueness
        name_check_sql = """
        SELECT COUNT(*) as count FROM exams WHERE LOWER(exam_name) = LOWER(:exam_name)
        """
        name_params = [db_manager.create_parameter('exam_name', body['exam_name'], 'string')]
        name_results = db_manager.execute_query(name_check_sql, name_params)
        
        if name_results and name_results[0]['count'] > 0:
            return create_error_response(400, "Exam name already exists", "DUPLICATE_EXAM_NAME")
        
        # Generate exam ID
        exam_id = generate_uuid()
        
        sql = """
        INSERT INTO exams (exam_id, exam_name, exam_type, description, created_at, updated_at)
        VALUES (:exam_id, :exam_name, :exam_type, :description, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        RETURNING exam_id, exam_name, exam_type, description, created_at, updated_at
        """
        
        parameters = [
            db_manager.create_parameter('exam_id', exam_id, 'string'),
            db_manager.create_parameter('exam_name', body['exam_name'], 'string'),
            db_manager.create_parameter('exam_type', body['exam_type'], 'string'),
            db_manager.create_parameter('description', body.get('description', ''), 'string')
        ]
        
        exam_results = db_manager.execute_query(sql, parameters)
        
        if not exam_results:
            return create_error_response(500, "Failed to create exam")
        
        exam = exam_results[0]
        
        logger.info(f"Created exam: {exam_id}")
        
        return create_response(201, {
            'message': 'Exam created successfully',
            'exam': exam
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in create_exam: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in create_exam: {str(e)}")
        return create_error_response(500, "Internal server error")


def get_exam(exam_id: str) -> Dict[str, Any]:
    """
    Handle GET /exams/{id} - Get exam by ID.
    
    Args:
        exam_id: Exam ID
        
    Returns:
        Exam data or 404 if not found
    """
    try:
        sql = """
        SELECT exam_id, exam_name, exam_type, description, created_at, updated_at
        FROM exams
        WHERE exam_id = :exam_id
        """
        
        parameters = [
            db_manager.create_parameter('exam_id', exam_id, 'string')
        ]
        
        exam_results = db_manager.execute_query(sql, parameters)
        
        if not exam_results:
            return create_error_response(404, "Exam not found", "EXAM_NOT_FOUND")
        
        exam = exam_results[0]
        
        return create_response(200, {'exam': exam})
        
    except DatabaseError as e:
        logger.error(f"Database error in get_exam: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in get_exam: {str(e)}")
        return create_error_response(500, "Internal server error")


def update_exam(exam_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle PUT /exams/{id} - Update exam.
    
    Args:
        exam_id: Exam ID
        event: Lambda event containing update data
        
    Returns:
        Updated exam data or 404 if not found
    """
    try:
        body = parse_event_body(event)
        
        # Build dynamic update query
        update_fields = []
        parameters = [db_manager.create_parameter('exam_id', exam_id, 'string')]
        
        if 'exam_name' in body and body['exam_name']:
            # Check for exam name uniqueness (excluding current exam)
            name_check_sql = """
            SELECT COUNT(*) as count FROM exams 
            WHERE LOWER(exam_name) = LOWER(:exam_name) AND exam_id != :exam_id
            """
            name_params = [
                db_manager.create_parameter('exam_name', body['exam_name'], 'string'),
                db_manager.create_parameter('exam_id', exam_id, 'string')
            ]
            name_results = db_manager.execute_query(name_check_sql, name_params)
            
            if name_results and name_results[0]['count'] > 0:
                return create_error_response(400, "Exam name already exists", "DUPLICATE_EXAM_NAME")
            
            update_fields.append('exam_name = :exam_name')
            parameters.append(db_manager.create_parameter('exam_name', body['exam_name'], 'string'))
        
        if 'exam_type' in body and body['exam_type']:
            update_fields.append('exam_type = :exam_type')
            parameters.append(db_manager.create_parameter('exam_type', body['exam_type'], 'string'))
        
        if 'description' in body:
            update_fields.append('description = :description')
            parameters.append(db_manager.create_parameter('description', body['description'], 'string'))
        
        if not update_fields:
            return create_error_response(400, "No fields to update", "NO_UPDATE_FIELDS")
        
        # Add updated timestamp
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        
        sql = f"""
        UPDATE exams
        SET {', '.join(update_fields)}
        WHERE exam_id = :exam_id
        RETURNING exam_id, exam_name, exam_type, description, created_at, updated_at
        """
        
        exam_results = db_manager.execute_query(sql, parameters)
        
        if not exam_results:
            return create_error_response(404, "Exam not found", "EXAM_NOT_FOUND")
        
        exam = exam_results[0]
        
        logger.info(f"Updated exam: {exam_id}")
        
        return create_response(200, {
            'message': 'Exam updated successfully',
            'exam': exam
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in update_exam: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in update_exam: {str(e)}")
        return create_error_response(500, "Internal server error")


def delete_exam(exam_id: str) -> Dict[str, Any]:
    """
    Handle DELETE /exams/{id} - Delete exam.
    
    Args:
        exam_id: Exam ID
        
    Returns:
        Success message or 404 if not found
    """
    try:
        # Check if exam has active reservations
        reservations_check_sql = """
        SELECT COUNT(*) as count FROM reservations 
        WHERE exam_id = :exam_id AND status IN ('scheduled', 'confirmed')
        """
        reservations_params = [db_manager.create_parameter('exam_id', exam_id, 'string')]
        reservations_results = db_manager.execute_query(reservations_check_sql, reservations_params)
        
        if reservations_results and reservations_results[0]['count'] > 0:
            return create_error_response(400, "Cannot delete exam with active reservations", "ACTIVE_RESERVATIONS")
        
        sql = """
        DELETE FROM exams
        WHERE exam_id = :exam_id
        RETURNING exam_id
        """
        
        parameters = [
            db_manager.create_parameter('exam_id', exam_id, 'string')
        ]
        
        delete_results = db_manager.execute_query(sql, parameters)
        
        if not delete_results:
            return create_error_response(404, "Exam not found", "EXAM_NOT_FOUND")
        
        logger.info(f"Deleted exam: {exam_id}")
        
        return create_response(200, {
            'message': 'Exam deleted successfully',
            'exam_id': exam_id
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in delete_exam: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in delete_exam: {str(e)}")
        return create_error_response(500, "Internal server error")
