"""
Document Upload API Lambda Function.
Handles document upload operations and triggers document processing workflow.

Endpoints:
- POST /documents/upload - Handle document upload metadata and trigger processing
- GET /documents/status/{id} - Get document processing status
"""

import logging
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError
from shared.database import DatabaseManager, DatabaseError
from shared.utils import (
    create_response, create_error_response, parse_event_body,
    extract_path_parameters, extract_query_parameters, validate_required_fields,
    handle_exceptions, generate_uuid, get_current_timestamp
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
db_manager = DatabaseManager()
eventbridge = boto3.client('events')


@handle_exceptions
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for document upload API.
    Routes requests to appropriate handlers based on HTTP method and path.
    """
    http_method = event.get('httpMethod', '')
    path = event.get('path', '')
    path_params = extract_path_parameters(event)
    
    # Route to appropriate handler
    if path == '/documents/upload':
        if http_method == 'POST':
            return handle_document_upload(event)
    elif path.startswith('/documents/status/') and 'id' in path_params:
        document_id = path_params['id']
        if http_method == 'GET':
            return get_document_status(document_id)
    
    return create_error_response(404, "Endpoint not found")


def handle_document_upload(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle POST /documents/upload - Process document upload metadata and trigger workflow.
    
    Required fields:
    - documentId: Unique document identifier
    - s3Key: S3 object key where document is stored
    - fileName: Original file name
    
    Optional fields:
    - contentType: MIME type of the document
    - fileSize: Size of the document in bytes
    - patientId: Associated patient ID
    - chatSessionId: Associated chat session ID
    
    Returns:
        Document upload confirmation with processing status
    """
    try:
        body = parse_event_body(event)
        
        # Validate required fields
        validation_error = validate_required_fields(body, ['documentId', 's3Key', 'fileName'])
        if validation_error:
            return create_error_response(400, validation_error, "VALIDATION_ERROR")
        
        document_id = body['documentId']
        s3_key = body['s3Key']
        file_name = body['fileName']
        content_type = body.get('contentType', 'application/octet-stream')
        file_size = body.get('fileSize', 0)
        patient_id = body.get('patientId')
        chat_session_id = body.get('chatSessionId')
        
        # Validate patient exists if provided
        if patient_id:
            patient_validation = validate_patient_exists(patient_id)
            if patient_validation:
                return patient_validation
        
        # Store document metadata in database
        store_result = store_document_metadata({
            'document_id': document_id,
            's3_key': s3_key,
            'file_name': file_name,
            'content_type': content_type,
            'file_size': file_size,
            'patient_id': patient_id,
            'chat_session_id': chat_session_id,
            'status': 'uploaded',
            'uploaded_at': get_current_timestamp()
        })
        
        if store_result:
            return store_result
        
        # Publish event for document processing
        event_result = publish_document_event({
            'documentId': document_id,
            's3Key': s3_key,
            'fileName': file_name,
            'contentType': content_type,
            'fileSize': file_size,
            'patientId': patient_id,
            'chatSessionId': chat_session_id,
            'eventType': 'DocumentUploaded',
            'timestamp': get_current_timestamp()
        })
        
        if event_result:
            logger.warning(f"Failed to publish event for document {document_id}: {event_result}")
            # Don't fail the upload if event publishing fails
        
        logger.info(f"Document upload processed: {document_id}")
        
        return create_response(200, {
            'documentId': document_id,
            'status': 'uploaded',
            'message': 'Document uploaded successfully and queued for processing',
            'fileName': file_name,
            'timestamp': get_current_timestamp()
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in handle_document_upload: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in handle_document_upload: {str(e)}")
        return create_error_response(500, "Internal server error")


def get_document_status(document_id: str) -> Dict[str, Any]:
    """
    Handle GET /documents/status/{id} - Get document processing status.
    
    Args:
        document_id: Document ID
        
    Returns:
        Document status and processing information
    """
    try:
        sql = """
        SELECT 
            document_id, file_name, content_type, file_size,
            status, uploaded_at, processed_at, error_message,
            patient_id, chat_session_id
        FROM document_uploads
        WHERE document_id = :document_id
        """
        
        parameters = [
            db_manager.create_parameter('document_id', document_id, 'string')
        ]
        
        response = db_manager.execute_sql(sql, parameters)
        records = response.get('records', [])
        
        if not records:
            return create_error_response(404, "Document not found", "DOCUMENT_NOT_FOUND")
        
        document = db_manager.parse_records(
            records,
            response.get('columnMetadata', [])
        )[0]
        
        # Add processing progress information
        processing_info = get_processing_progress(document_id)
        if processing_info:
            document['processing'] = processing_info
        
        return create_response(200, {'document': document})
        
    except DatabaseError as e:
        logger.error(f"Database error in get_document_status: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in get_document_status: {str(e)}")
        return create_error_response(500, "Internal server error")


def store_document_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Store document metadata in the database.
    
    Args:
        metadata: Document metadata dictionary
        
    Returns:
        Error response if storage fails, None if successful
    """
    try:
        sql = """
        INSERT INTO document_uploads (
            document_id, s3_key, file_name, content_type, file_size,
            patient_id, chat_session_id, status, uploaded_at, created_at, updated_at
        ) VALUES (
            :document_id, :s3_key, :file_name, :content_type, :file_size,
            :patient_id, :chat_session_id, :status, :uploaded_at, 
            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
        ON CONFLICT (document_id) DO UPDATE SET
            status = EXCLUDED.status,
            updated_at = CURRENT_TIMESTAMP
        """
        
        parameters = [
            db_manager.create_parameter('document_id', metadata['document_id'], 'string'),
            db_manager.create_parameter('s3_key', metadata['s3_key'], 'string'),
            db_manager.create_parameter('file_name', metadata['file_name'], 'string'),
            db_manager.create_parameter('content_type', metadata['content_type'], 'string'),
            db_manager.create_parameter('file_size', metadata['file_size'], 'long'),
            db_manager.create_parameter('patient_id', metadata.get('patient_id'), 'string'),
            db_manager.create_parameter('chat_session_id', metadata.get('chat_session_id'), 'string'),
            db_manager.create_parameter('status', metadata['status'], 'string'),
            db_manager.create_parameter('uploaded_at', metadata['uploaded_at'], 'string')
        ]
        
        db_manager.execute_sql(sql, parameters)
        logger.info(f"Stored document metadata: {metadata['document_id']}")
        
        return None  # Success
        
    except DatabaseError as e:
        logger.error(f"Failed to store document metadata: {str(e)}")
        return create_error_response(500, "Failed to store document metadata", e.error_code)


def publish_document_event(event_data: Dict[str, Any]) -> str:
    """
    Publish document processing event to EventBridge.
    
    Args:
        event_data: Event data dictionary
        
    Returns:
        Error message if publishing fails, None if successful
    """
    try:
        response = eventbridge.put_events(
            Entries=[
                {
                    'Source': 'healthcare.documents',
                    'DetailType': event_data['eventType'],
                    'Detail': str(event_data),  # Convert to JSON string
                    'Time': get_current_timestamp()
                }
            ]
        )
        
        # Check for failed entries
        failed_entries = response.get('FailedEntryCount', 0)
        if failed_entries > 0:
            logger.error(f"Failed to publish {failed_entries} events")
            return f"Failed to publish {failed_entries} events"
        
        logger.info(f"Published document event: {event_data['documentId']}")
        return None  # Success
        
    except ClientError as e:
        error_message = f"EventBridge error: {str(e)}"
        logger.error(error_message)
        return error_message
    
    except Exception as e:
        error_message = f"Unexpected error publishing event: {str(e)}"
        logger.error(error_message)
        return error_message


def validate_patient_exists(patient_id: str) -> Dict[str, Any]:
    """
    Validate that patient exists.
    
    Args:
        patient_id: Patient ID to validate
        
    Returns:
        Error response if patient doesn't exist, None if exists
    """
    try:
        sql = "SELECT COUNT(*) as count FROM patients WHERE patient_id = :patient_id"
        parameters = [db_manager.create_parameter('patient_id', patient_id, 'string')]
        
        response = db_manager.execute_sql(sql, parameters)
        
        if not response.get('records') or response['records'][0][0].get('longValue', 0) == 0:
            return create_error_response(400, "Patient not found", "PATIENT_NOT_FOUND")
        
        return None  # Patient exists
        
    except DatabaseError as e:
        logger.error(f"Database error validating patient: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)


def get_processing_progress(document_id: str) -> Dict[str, Any]:
    """
    Get document processing progress information.
    
    Args:
        document_id: Document ID
        
    Returns:
        Processing progress information or None if not available
    """
    try:
        # This would typically query a processing status table or external service
        # For now, return basic information
        sql = """
        SELECT status, uploaded_at, processed_at, error_message
        FROM document_uploads
        WHERE document_id = :document_id
        """
        
        parameters = [
            db_manager.create_parameter('document_id', document_id, 'string')
        ]
        
        response = db_manager.execute_sql(sql, parameters)
        
        if not response.get('records'):
            return None
        
        record = db_manager.parse_records(
            response['records'],
            response.get('columnMetadata', [])
        )[0]
        
        status = record.get('status', 'unknown')
        
        # Map status to progress information
        progress_map = {
            'uploaded': {'stage': 'uploaded', 'progress': 10, 'message': 'Document uploaded, queued for processing'},
            'processing': {'stage': 'processing', 'progress': 50, 'message': 'Document being processed'},
            'processed': {'stage': 'completed', 'progress': 100, 'message': 'Document processing completed'},
            'failed': {'stage': 'failed', 'progress': 0, 'message': 'Document processing failed'},
            'error': {'stage': 'error', 'progress': 0, 'message': 'Error during processing'}
        }
        
        progress_info = progress_map.get(status, {
            'stage': 'unknown',
            'progress': 0,
            'message': f'Unknown status: {status}'
        })
        
        if record.get('error_message'):
            progress_info['error'] = record['error_message']
        
        return progress_info
        
    except Exception as e:
        logger.error(f"Error getting processing progress: {str(e)}")
        return None


def update_document_status(document_id: str, status: str, error_message: str = None) -> None:
    """
    Update document processing status.
    
    Args:
        document_id: Document ID
        status: New status
        error_message: Optional error message
    """
    try:
        if status == 'processed':
            sql = """
            UPDATE document_uploads
            SET status = :status, processed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE document_id = :document_id
            """
            parameters = [
                db_manager.create_parameter('document_id', document_id, 'string'),
                db_manager.create_parameter('status', status, 'string')
            ]
        else:
            sql = """
            UPDATE document_uploads
            SET status = :status, error_message = :error_message, updated_at = CURRENT_TIMESTAMP
            WHERE document_id = :document_id
            """
            parameters = [
                db_manager.create_parameter('document_id', document_id, 'string'),
                db_manager.create_parameter('status', status, 'string'),
                db_manager.create_parameter('error_message', error_message, 'string')
            ]
        
        db_manager.execute_sql(sql, parameters)
        logger.info(f"Updated document status: {document_id} -> {status}")
        
    except Exception as e:
        logger.error(f"Error updating document status: {str(e)}")
