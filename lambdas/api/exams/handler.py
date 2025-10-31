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
    Main Lambda handler for exams API.
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
    if normalized_path == '/exams':
        if http_method == 'GET':
            return list_exams(event)
        elif http_method == 'POST':
            return create_exam(event)
    elif normalized_path.startswith('/exams/') and path_params and 'id' in path_params:
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
        SELECT exam_id, exam_name, exam_type, description, duration_minutes, created_at, updated_at
        FROM exams
        {where_clause}
        ORDER BY exam_name
        LIMIT :limit OFFSET :offset
        """
        
        response = db_manager.execute_sql(sql, parameters)
        exams = db_manager.parse_records(
            response.get('records', []),
            response.get('columnMetadata', [])
        )
        
        # Get total count for pagination
        count_sql = f"SELECT COUNT(*) as total FROM exams {where_clause}"
        count_params = [p for p in parameters if p['name'] == 'exam_type'] if exam_type_filter else []
        count_response = db_manager.execute_sql(count_sql, count_params)
        total_count = 0
        if count_response.get('records'):
            total_count = count_response['records'][0][0].get('longValue', 0)
        
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
    - exam_name: Exam name
    - exam_type: Type of exam
    - duration_minutes: Duration in minutes
    
    Optional fields:
    - description: Exam description
    
    Returns:
        Created exam data
    """
    try:
        body = parse_event_body(event)
        
        # Validate required fields
        validation_error = validate_required_fields(body, ['exam_name', 'exam_type', 'duration_minutes'])
        if validation_error:
            return create_error_response(400, validation_error, "VALIDATION_ERROR")
        
        # Generate exam ID
        exam_id = generate_uuid()
        
        sql = """
        INSERT INTO exams (exam_id, exam_name, exam_type, description, duration_minutes, created_at, updated_at)
        VALUES (:exam_id, :exam_name, :exam_type, :description, :duration_minutes, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        RETURNING exam_id, exam_name, exam_type, description, duration_minutes, created_at, updated_at
        """
        
        parameters = [
            db_manager.create_parameter('exam_id', exam_id, 'string'),
            db_manager.create_parameter('exam_name', body['exam_name'], 'string'),
            db_manager.create_parameter('exam_type', body['exam_type'], 'string'),
            db_manager.create_parameter('description', body.get('description', ''), 'string'),
            db_manager.create_parameter('duration_minutes', body['duration_minutes'], 'long')
        ]
        
        response = db_manager.execute_sql(sql, parameters)
        
        if not response.get('records'):
            return create_error_response(500, "Failed to create exam")
        
        exam = db_manager.parse_records(
            response['records'],
            response.get('columnMetadata', [])
        )[0]
        
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
        SELECT exam_id, exam_name, exam_type, description, duration_minutes, created_at, updated_at
        FROM exams
        WHERE exam_id = :exam_id
        """
        
        parameters = [
            db_manager.create_parameter('exam_id', exam_id, 'string')
        ]
        
        response = db_manager.execute_sql(sql, parameters)
        records = response.get('records', [])
        
        if not records:
            return create_error_response(404, "Exam not found", "EXAM_NOT_FOUND")
        
        exam = db_manager.parse_records(
            records,
            response.get('columnMetadata', [])
        )[0]
        
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
            update_fields.append('exam_name = :exam_name')
            parameters.append(db_manager.create_parameter('exam_name', body['exam_name'], 'string'))
        
        if 'exam_type' in body and body['exam_type']:
            update_fields.append('exam_type = :exam_type')
            parameters.append(db_manager.create_parameter('exam_type', body['exam_type'], 'string'))
        
        if 'description' in body:
            update_fields.append('description = :description')
            parameters.append(db_manager.create_parameter('description', body['description'], 'string'))
        
        if 'duration_minutes' in body and body['duration_minutes']:
            update_fields.append('duration_minutes = :duration_minutes')
            parameters.append(db_manager.create_parameter('duration_minutes', body['duration_minutes'], 'long'))
        
        if not update_fields:
            return create_error_response(400, "No fields to update", "NO_UPDATE_FIELDS")
        
        # Add updated timestamp
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        
        sql = f"""
        UPDATE exams
        SET {', '.join(update_fields)}
        WHERE exam_id = :exam_id
        RETURNING exam_id, exam_name, exam_type, description, duration_minutes, created_at, updated_at
        """
        
        response = db_manager.execute_sql(sql, parameters)
        records = response.get('records', [])
        
        if not records:
            return create_error_response(404, "Exam not found", "EXAM_NOT_FOUND")
        
        exam = db_manager.parse_records(
            records,
            response.get('columnMetadata', [])
        )[0]
        
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
        reservations_response = db_manager.execute_sql(reservations_check_sql, reservations_params)
        
        if reservations_response.get('records') and reservations_response['records'][0][0].get('longValue', 0) > 0:
            return create_error_response(400, "Cannot delete exam with active reservations", "ACTIVE_RESERVATIONS")
        
        sql = """
        DELETE FROM exams
        WHERE exam_id = :exam_id
        RETURNING exam_id
        """
        
        parameters = [
            db_manager.create_parameter('exam_id', exam_id, 'string')
        ]
        
        response = db_manager.execute_sql(sql, parameters)
        records = response.get('records', [])
        
        if not records:
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


def _is_mcp_gateway_event(event: Dict[str, Any]) -> bool:
    """
    Check if the event is from MCP Gateway.
    MCP Gateway events have an 'action' field and no HTTP method.
    """
    return 'action' in event and 'httpMethod' not in event


def handle_mcp_gateway_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle MCP Gateway requests with action-based routing.
    
    Expected event format:
    {
        "action": "list|get|create|update|delete",
        "exam_id": "string (for get, update, delete)",
        "exam_type": "string (for list filtering)",
        "exam_data": {
            "exam_name": "string",
            "exam_type": "string", 
            "description": "string",
            "duration_minutes": int,
            "preparation_instructions": "string"
        },
        "pagination": {
            "limit": int,
            "offset": int
        }
    }
    """
    try:
        action = event.get('action')
        logger.info(f"Received MCP Gateway request: action={action}")
        
        if action == 'list':
            # Convert MCP parameters to API Gateway format
            query_params = {}
            if event.get('exam_type'):
                query_params['exam_type'] = event['exam_type']
            if event.get('pagination'):
                query_params.update(event['pagination'])
            
            mock_event = {
                'queryStringParameters': query_params
            }
            return list_exams(mock_event)
            
        elif action == 'get':
            exam_id = event.get('exam_id')
            if not exam_id:
                return create_error_response(400, "exam_id is required for get action")
            return get_exam(exam_id)
            
        elif action == 'create':
            exam_data = event.get('exam_data')
            if not exam_data:
                return create_error_response(400, "exam_data is required for create action")
            
            mock_event = {
                'body': json.dumps(exam_data)
            }
            return create_exam(mock_event)
            
        elif action == 'update':
            exam_id = event.get('exam_id')
            exam_data = event.get('exam_data')
            if not exam_id:
                return create_error_response(400, "exam_id is required for update action")
            if not exam_data:
                return create_error_response(400, "exam_data is required for update action")
            
            mock_event = {
                'body': json.dumps(exam_data)
            }
            return update_exam(exam_id, mock_event)
            
        elif action == 'delete':
            exam_id = event.get('exam_id')
            if not exam_id:
                return create_error_response(400, "exam_id is required for delete action")
            return delete_exam(exam_id)
            
        else:
            return create_error_response(400, f"Unsupported action: {action}")
            
    except Exception as e:
        logger.error(f"Error in MCP Gateway request: {str(e)}")
        return create_error_response(500, "Internal server error")
