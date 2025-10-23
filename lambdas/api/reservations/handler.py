"""
Reservations API Lambda Function.
Handles CRUD operations for appointment reservations management.

Endpoints:
- GET /reservations - List reservations with pagination
- POST /reservations - Create new reservation
- GET /reservations/{id} - Get reservation by ID
- PUT /reservations/{id} - Update reservation
- DELETE /reservations/{id} - Cancel reservation
- POST /reservations/availability - Check availability
"""

import logging
from typing import Dict, Any
from datetime import datetime, timedelta
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
    Main Lambda handler for reservations API.
    Routes requests to appropriate handlers based on HTTP method and path.
    """
    # Handle both API Gateway v1 and v2 event formats
    http_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method', '')
    path = event.get('path') or event.get('requestContext', {}).get('http', {}).get('path', '')
    path_params = event.get('pathParameters') or {}
    
    # Log the event for debugging
    logger.info(f"Received request: method={http_method}, path={path}")
    
    # Normalize path by removing stage prefix if present
    normalized_path = path
    if path.startswith('/v1/'):
        normalized_path = path[3:]  # Remove '/v1' prefix
    
    # Route to appropriate handler
    if normalized_path == '/reservations':
        if http_method == 'GET':
            return list_reservations(event)
        elif http_method == 'POST':
            return create_reservation(event)
    elif normalized_path == '/reservations/availability':
        if http_method == 'POST':
            return check_availability(event)
    elif normalized_path.startswith('/reservations/') and path_params and 'id' in path_params:
        reservation_id = path_params['id']
        if http_method == 'GET':
            return get_reservation(reservation_id)
        elif http_method == 'PUT':
            return update_reservation(reservation_id, event)
        elif http_method == 'DELETE':
            return cancel_reservation(reservation_id)
    
    return create_error_response(404, "Endpoint not found")


def list_reservations(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle GET /reservations - List reservations with pagination.
    
    Query parameters:
    - limit: Number of reservations to return (default: 50, max: 1000)
    - offset: Number of reservations to skip (default: 0)
    - status: Filter by status (optional)
    - patient_id: Filter by patient ID (optional)
    - medic_id: Filter by medic ID (optional)
    - date_from: Filter reservations from date (YYYY-MM-DD) (optional)
    - date_to: Filter reservations to date (YYYY-MM-DD) (optional)
    
    Returns:
        List of reservations with pagination info
    """
    try:
        query_params = extract_query_parameters(event)
        pagination = validate_pagination_params(query_params)
        
        # Build filters
        where_conditions = []
        parameters = [
            db_manager.create_parameter('limit', pagination['limit'], 'long'),
            db_manager.create_parameter('offset', pagination['offset'], 'long')
        ]
        
        if query_params.get('status'):
            where_conditions.append("status = :status")
            parameters.append(db_manager.create_parameter('status', query_params['status'], 'string'))
        
        if query_params.get('patient_id'):
            where_conditions.append("patient_id = :patient_id")
            parameters.append(db_manager.create_parameter('patient_id', query_params['patient_id'], 'string'))
        
        if query_params.get('medic_id'):
            where_conditions.append("medic_id = :medic_id")
            parameters.append(db_manager.create_parameter('medic_id', query_params['medic_id'], 'string'))
        
        if query_params.get('date_from'):
            where_conditions.append("DATE(reservation_date) >= :date_from")
            parameters.append(db_manager.create_parameter('date_from', query_params['date_from'], 'string'))
        
        if query_params.get('date_to'):
            where_conditions.append("DATE(reservation_date) <= :date_to")
            parameters.append(db_manager.create_parameter('date_to', query_params['date_to'], 'string'))
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        sql = f"""
        SELECT 
            r.reservation_id, r.patient_id, r.medic_id, r.exam_id,
            (r.reservation_date || ' ' || COALESCE(r.reservation_time::text, '00:00:00')) as appointment_date,
            r.status, r.notes, r.created_at, r.updated_at,
            p.full_name as patient_name,
            m.full_name as medic_name,
            e.exam_name
        FROM reservations r
        LEFT JOIN patients p ON r.patient_id = p.patient_id
        LEFT JOIN medics m ON r.medic_id = m.medic_id
        LEFT JOIN exams e ON r.exam_id = e.exam_id
        {where_clause}
        ORDER BY r.reservation_date DESC, r.reservation_time DESC
        LIMIT :limit OFFSET :offset
        """
        
        response = db_manager.execute_sql(sql, parameters)
        reservations = db_manager.parse_records(
            response.get('records', []),
            response.get('columnMetadata', [])
        )
        
        # Get total count for pagination
        count_sql = f"SELECT COUNT(*) as total FROM reservations r {where_clause}"
        count_params = [p for p in parameters if p['name'] not in ['limit', 'offset']]
        count_response = db_manager.execute_sql(count_sql, count_params)
        total_count = 0
        if count_response.get('records'):
            total_count = count_response['records'][0][0].get('longValue', 0)
        
        return create_response(200, {
            'reservations': reservations,
            'pagination': {
                'limit': pagination['limit'],
                'offset': pagination['offset'],
                'total': total_count,
                'count': len(reservations)
            },
            'filters': {k: v for k, v in query_params.items() 
                       if k in ['status', 'patient_id', 'medic_id', 'date_from', 'date_to'] and v}
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in list_reservations: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in list_reservations: {str(e)}")
        return create_error_response(500, "Internal server error")


def create_reservation(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle POST /reservations - Create new reservation.
    
    Required fields:
    - patient_id: Patient ID
    - medic_id: Medic ID
    - exam_id: Exam ID
    - reservation_date: Reservation date and time (ISO format)
    
    Returns:
        Created reservation data
    """
    try:
        body = parse_event_body(event)
        
        # Validate required fields - frontend sends appointment_date, we need to split it
        validation_error = validate_required_fields(body, ['patient_id', 'medic_id', 'exam_id', 'appointment_date'])
        if validation_error:
            return create_error_response(400, validation_error, "VALIDATION_ERROR")
        
        # Parse appointment_date into date and time components
        try:
            from datetime import datetime
            appointment_datetime = datetime.fromisoformat(body['appointment_date'].replace('Z', '+00:00'))
            reservation_date = appointment_datetime.date()
            reservation_time = appointment_datetime.time()
        except (ValueError, AttributeError) as e:
            return create_error_response(400, f"Invalid appointment_date format: {str(e)}", "INVALID_DATE_FORMAT")
        
        # Validate that referenced entities exist
        validation_result = validate_reservation_entities(body['patient_id'], body['medic_id'], body['exam_id'])
        if validation_result:
            return validation_result
        
        # Check availability using the parsed date
        availability_result = check_medic_availability(body['medic_id'], str(reservation_date))
        if not availability_result['available']:
            return create_error_response(400, "Medic not available at requested time", "MEDIC_NOT_AVAILABLE")
        
        # Generate reservation ID
        reservation_id = generate_uuid()
        
        sql = """
        INSERT INTO reservations (
            reservation_id, patient_id, medic_id, exam_id, 
            reservation_date, reservation_time, status, notes, created_at, updated_at
        )
        VALUES (
            :reservation_id, :patient_id, :medic_id, :exam_id,
            :reservation_date, :reservation_time, 'scheduled', :notes, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
        RETURNING 
            reservation_id, patient_id, medic_id, exam_id,
            (reservation_date || ' ' || COALESCE(reservation_time::text, '00:00:00')) as appointment_date,
            status, notes, created_at, updated_at
        """
        
        parameters = [
            db_manager.create_parameter('reservation_id', reservation_id, 'string'),
            db_manager.create_parameter('patient_id', body['patient_id'], 'string'),
            db_manager.create_parameter('medic_id', body['medic_id'], 'string'),
            db_manager.create_parameter('exam_id', body['exam_id'], 'string'),
            db_manager.create_parameter('reservation_date', str(reservation_date), 'string'),
            db_manager.create_parameter('reservation_time', str(reservation_time), 'string'),
            db_manager.create_parameter('notes', body.get('notes', ''), 'string')
        ]
        
        response = db_manager.execute_sql(sql, parameters)
        
        if not response.get('records'):
            return create_error_response(500, "Failed to create reservation")
        
        reservation = db_manager.parse_records(
            response['records'],
            response.get('columnMetadata', [])
        )[0]
        
        logger.info(f"Created reservation: {reservation_id}")
        
        return create_response(201, {
            'message': 'Reservation created successfully',
            'reservation': reservation
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in create_reservation: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in create_reservation: {str(e)}")
        return create_error_response(500, "Internal server error")


def get_reservation(reservation_id: str) -> Dict[str, Any]:
    """
    Handle GET /reservations/{id} - Get reservation by ID.
    
    Args:
        reservation_id: Reservation ID
        
    Returns:
        Reservation data with related entity details or 404 if not found
    """
    try:
        sql = """
        SELECT 
            r.reservation_id, r.patient_id, r.medic_id, r.exam_id,
            (r.reservation_date || ' ' || COALESCE(r.reservation_time::text, '00:00:00')) as appointment_date,
            r.status, r.notes, r.created_at, r.updated_at,
            p.full_name as patient_name,
            m.full_name as medic_name, m.specialization as medic_specialty,
            e.exam_name, e.exam_type
        FROM reservations r
        LEFT JOIN patients p ON r.patient_id = p.patient_id
        LEFT JOIN medics m ON r.medic_id = m.medic_id
        LEFT JOIN exams e ON r.exam_id = e.exam_id
        WHERE r.reservation_id = :reservation_id
        """
        
        parameters = [
            db_manager.create_parameter('reservation_id', reservation_id, 'string')
        ]
        
        response = db_manager.execute_sql(sql, parameters)
        records = response.get('records', [])
        
        if not records:
            return create_error_response(404, "Reservation not found", "RESERVATION_NOT_FOUND")
        
        reservation = db_manager.parse_records(
            records,
            response.get('columnMetadata', [])
        )[0]
        
        return create_response(200, {'reservation': reservation})
        
    except DatabaseError as e:
        logger.error(f"Database error in get_reservation: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in get_reservation: {str(e)}")
        return create_error_response(500, "Internal server error")


def update_reservation(reservation_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle PUT /reservations/{id} - Update reservation.
    
    Args:
        reservation_id: Reservation ID
        event: Lambda event containing update data
        
    Returns:
        Updated reservation data or 404 if not found
    """
    try:
        body = parse_event_body(event)
        
        # Build dynamic update query
        update_fields = []
        parameters = [db_manager.create_parameter('reservation_id', reservation_id, 'string')]
        
        if 'appointment_date' in body and body['appointment_date']:
            # Parse appointment_date into date and time components
            try:
                from datetime import datetime
                appointment_datetime = datetime.fromisoformat(body['appointment_date'].replace('Z', '+00:00'))
                reservation_date = appointment_datetime.date()
                reservation_time = appointment_datetime.time()
            except (ValueError, AttributeError) as e:
                return create_error_response(400, f"Invalid appointment_date format: {str(e)}", "INVALID_DATE_FORMAT")
            
            # Get current reservation to check medic
            current_sql = "SELECT medic_id FROM reservations WHERE reservation_id = :reservation_id"
            current_response = db_manager.execute_sql(current_sql, parameters)
            
            if not current_response.get('records'):
                return create_error_response(404, "Reservation not found", "RESERVATION_NOT_FOUND")
            
            current_medic_id = current_response['records'][0][0].get('stringValue')
            
            # Check availability for new date
            availability_result = check_medic_availability(current_medic_id, str(reservation_date), reservation_id)
            if not availability_result['available']:
                return create_error_response(400, "Medic not available at requested time", "MEDIC_NOT_AVAILABLE")
            
            update_fields.append('reservation_date = :reservation_date')
            update_fields.append('reservation_time = :reservation_time')
            parameters.append(db_manager.create_parameter('reservation_date', str(reservation_date), 'string'))
            parameters.append(db_manager.create_parameter('reservation_time', str(reservation_time), 'string'))
        
        if 'notes' in body:
            update_fields.append('notes = :notes')
            parameters.append(db_manager.create_parameter('notes', body['notes'], 'string'))
        
        if 'status' in body and body['status']:
            # Validate status
            valid_statuses = ['scheduled', 'confirmed', 'completed', 'cancelled', 'no_show']
            if body['status'] not in valid_statuses:
                return create_error_response(400, f"Invalid status. Must be one of: {', '.join(valid_statuses)}", "INVALID_STATUS")
            
            update_fields.append('status = :status')
            parameters.append(db_manager.create_parameter('status', body['status'], 'string'))
        
        if not update_fields:
            return create_error_response(400, "No fields to update", "NO_UPDATE_FIELDS")
        
        # Add updated timestamp
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        
        sql = f"""
        UPDATE reservations
        SET {', '.join(update_fields)}
        WHERE reservation_id = :reservation_id
        RETURNING 
            reservation_id, patient_id, medic_id, exam_id,
            (reservation_date || ' ' || COALESCE(reservation_time::text, '00:00:00')) as appointment_date,
            status, notes, created_at, updated_at
        """
        
        response = db_manager.execute_sql(sql, parameters)
        records = response.get('records', [])
        
        if not records:
            return create_error_response(404, "Reservation not found", "RESERVATION_NOT_FOUND")
        
        reservation = db_manager.parse_records(
            records,
            response.get('columnMetadata', [])
        )[0]
        
        logger.info(f"Updated reservation: {reservation_id}")
        
        return create_response(200, {
            'message': 'Reservation updated successfully',
            'reservation': reservation
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in update_reservation: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in update_reservation: {str(e)}")
        return create_error_response(500, "Internal server error")


def cancel_reservation(reservation_id: str) -> Dict[str, Any]:
    """
    Handle DELETE /reservations/{id} - Cancel reservation.
    
    Args:
        reservation_id: Reservation ID
        
    Returns:
        Success message or 404 if not found
    """
    try:
        sql = """
        UPDATE reservations
        SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
        WHERE reservation_id = :reservation_id AND status NOT IN ('completed', 'cancelled')
        RETURNING reservation_id, status
        """
        
        parameters = [
            db_manager.create_parameter('reservation_id', reservation_id, 'string')
        ]
        
        response = db_manager.execute_sql(sql, parameters)
        records = response.get('records', [])
        
        if not records:
            return create_error_response(404, "Reservation not found or already completed/cancelled", "RESERVATION_NOT_FOUND")
        
        logger.info(f"Cancelled reservation: {reservation_id}")
        
        return create_response(200, {
            'message': 'Reservation cancelled successfully',
            'reservation_id': reservation_id
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in cancel_reservation: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in cancel_reservation: {str(e)}")
        return create_error_response(500, "Internal server error")


def check_availability(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle POST /reservations/availability - Check medic availability.
    
    Required fields:
    - medic_id: Medic ID
    - date: Date to check (YYYY-MM-DD format)
    
    Optional fields:
    - duration_hours: Duration in hours (default: 1)
    
    Returns:
        Availability information
    """
    try:
        body = parse_event_body(event)
        
        # Validate required fields
        validation_error = validate_required_fields(body, ['medic_id', 'date'])
        if validation_error:
            return create_error_response(400, validation_error, "VALIDATION_ERROR")
        
        medic_id = body['medic_id']
        date = body['date']
        duration_hours = body.get('duration_hours', 1)
        
        availability_result = check_medic_availability(medic_id, date)
        
        return create_response(200, {
            'medic_id': medic_id,
            'date': date,
            'duration_hours': duration_hours,
            'available': availability_result['available'],
            'conflicts': availability_result.get('conflicts', 0),
            'message': availability_result.get('message', '')
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in check_availability: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in check_availability: {str(e)}")
        return create_error_response(500, "Internal server error")


def validate_reservation_entities(patient_id: str, medic_id: str, exam_id: str) -> Dict[str, Any]:
    """
    Validate that patient, medic, and exam exist.
    
    Returns:
        Error response if validation fails, None if successful
    """
    try:
        # Check patient exists
        patient_sql = "SELECT COUNT(*) as count FROM patients WHERE patient_id = :patient_id"
        patient_params = [db_manager.create_parameter('patient_id', patient_id, 'string')]
        patient_response = db_manager.execute_sql(patient_sql, patient_params)
        
        if not patient_response.get('records') or patient_response['records'][0][0].get('longValue', 0) == 0:
            return create_error_response(400, "Patient not found", "PATIENT_NOT_FOUND")
        
        # Check medic exists
        medic_sql = "SELECT COUNT(*) as count FROM medics WHERE medic_id = :medic_id"
        medic_params = [db_manager.create_parameter('medic_id', medic_id, 'string')]
        medic_response = db_manager.execute_sql(medic_sql, medic_params)
        
        if not medic_response.get('records') or medic_response['records'][0][0].get('longValue', 0) == 0:
            return create_error_response(400, "Medic not found", "MEDIC_NOT_FOUND")
        
        # Check exam exists
        exam_sql = "SELECT COUNT(*) as count FROM exams WHERE exam_id = :exam_id"
        exam_params = [db_manager.create_parameter('exam_id', exam_id, 'string')]
        exam_response = db_manager.execute_sql(exam_sql, exam_params)
        
        if not exam_response.get('records') or exam_response['records'][0][0].get('longValue', 0) == 0:
            return create_error_response(400, "Exam not found", "EXAM_NOT_FOUND")
        
        return None  # All validations passed
        
    except DatabaseError as e:
        logger.error(f"Database error in validate_reservation_entities: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)


def check_medic_availability(medic_id: str, date: str, exclude_reservation_id: str = None) -> Dict[str, Any]:
    """
    Check if medic is available at the specified date/time.
    
    Args:
        medic_id: Medic ID
        date: Date/time to check
        exclude_reservation_id: Reservation ID to exclude from conflict check (for updates)
        
    Returns:
        Dictionary with availability information
    """
    try:
        # Check for conflicts on the same date
        sql = """
        SELECT COUNT(*) as conflict_count
        FROM reservations
        WHERE medic_id = :medic_id
          AND DATE(reservation_date) = DATE(:date)
          AND status IN ('scheduled', 'confirmed')
        """
        
        parameters = [
            db_manager.create_parameter('medic_id', medic_id, 'string'),
            db_manager.create_parameter('date', date, 'string')
        ]
        
        if exclude_reservation_id:
            sql += " AND reservation_id != :exclude_reservation_id"
            parameters.append(db_manager.create_parameter('exclude_reservation_id', exclude_reservation_id, 'string'))
        
        response = db_manager.execute_sql(sql, parameters)
        
        conflict_count = 0
        if response.get('records'):
            conflict_count = response['records'][0][0].get('longValue', 0)
        
        available = conflict_count == 0
        
        return {
            'available': available,
            'conflicts': conflict_count,
            'message': 'Available' if available else f'{conflict_count} conflicting reservations found'
        }
        
    except DatabaseError as e:
        logger.error(f"Database error in check_medic_availability: {str(e)}")
        return {
            'available': False,
            'conflicts': 0,
            'message': 'Error checking availability'
        }
