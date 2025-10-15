"""
Lambda function for document upload handling.
Handles file uploads from chat interface with validation and S3 storage.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict
import boto3
from botocore.exceptions import ClientError
from shared.datetime_utils import get_current_iso8601, generate_timestamp_id

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
eventbridge_client = boto3.client('events')

# Environment variables
RAW_BUCKET = os.environ.get('RAW_BUCKET', '')  # Updated to match backend_stack.py
EVENT_BUS_NAME = os.environ.get('EVENT_BUS_NAME', 'default')

# Supported file types and their MIME types
SUPPORTED_FILE_TYPES = {
    'application/pdf': ['.pdf'],
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/tiff': ['.tif', '.tiff'],
    'audio/mpeg': ['.mp3'],
    'audio/wav': ['.wav'],
    'video/mp4': ['.mp4'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'application/msword': ['.doc']
}

# Maximum file size: 100MB
MAX_FILE_SIZE = 100 * 1024 * 1024


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle document upload requests from chat interface.
    
    Args:
        event: Lambda event containing upload request
        context: Lambda context
        
    Returns:
        Response with upload status and document metadata
    """
    logger.info(f"Received upload event: {json.dumps(event)}")
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Extract file metadata
        file_name = body.get('fileName')
        file_size = body.get('fileSize', 0)
        content_type = body.get('contentType')
        patient_id = body.get('patientId')
        chat_session_id = body.get('chatSessionId')
        file_content_base64 = body.get('fileContent')
        
        # Validate required fields
        if not all([file_name, content_type, file_content_base64]):
            return error_response(400, "Faltan campos obligatorios: fileName, contentType, fileContent")
        
        # Validate file type
        if not is_valid_file_type(content_type, file_name):
            return error_response(400, f"Tipo de archivo no soportado: {content_type}")
        
        # Validate file size
        if file_size > MAX_FILE_SIZE:
            return error_response(400, f"El tamaño del archivo excede el tamaño máximo permitido de {MAX_FILE_SIZE} bytes")
        
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Create organized S3 key structure
        s3_key = create_s3_key(document_id, patient_id, file_name)
        
        # Decode base64 content and upload to S3
        import base64
        file_content = base64.b64decode(file_content_base64)
        
        # Upload file to S3
        upload_metadata = {
            'document_id': document_id,
            'patient_id': patient_id or 'unknown',
            'chat_session_id': chat_session_id or 'unknown',
            'original_filename': file_name,
            'content_type': content_type,
            'upload_timestamp': get_current_iso8601()
        }
        
        s3_client.put_object(
            Bucket=RAW_BUCKET,
            Key=s3_key,
            Body=file_content,
            ContentType=content_type,
            Metadata=upload_metadata,
            ServerSideEncryption='AES256'
        )
        
        logger.info(f"File uploaded successfully to s3://{RAW_BUCKET}/{s3_key}")
        
        # Publish EventBridge event for immediate processing
        event_detail = {
            'documentId': document_id,
            'bucket': RAW_BUCKET,
            'key': s3_key,
            'patientId': patient_id,
            'chatSessionId': chat_session_id,
            'fileName': file_name,
            'contentType': content_type,
            'fileSize': file_size,
            'uploadTimestamp': upload_metadata['upload_timestamp']
        }
        
        publish_event(event_detail)
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'documentId': document_id,
                's3Key': s3_key,
                'bucket': RAW_BUCKET,
                'status': 'uploaded',
                'message': 'Documento subido exitosamente y en cola para procesamiento'
            })
        }
        
    except ClientError as e:
        logger.error(f"AWS service error: {str(e)}")
        return error_response(500, f"Error del servicio AWS: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return error_response(500, f"Error interno del servidor: {str(e)}")


def is_valid_file_type(content_type: str, file_name: str) -> bool:
    """
    Validate if the file type is supported.
    
    Args:
        content_type: MIME type of the file
        file_name: Name of the file
        
    Returns:
        True if file type is supported, False otherwise
    """
    if content_type not in SUPPORTED_FILE_TYPES:
        return False
    
    # Check file extension matches content type
    file_extension = file_name.lower().split('.')[-1]
    return file_extension in SUPPORTED_FILE_TYPES[content_type]


def create_s3_key(document_id: str, patient_id: str, file_name: str) -> str:
    """
    Create organized S3 key structure.
    
    Args:
        document_id: Unique document identifier
        patient_id: Patient identifier (optional)
        file_name: Original file name
        
    Returns:
        S3 key path
    """
    date_prefix = datetime.now().strftime('%Y/%m/%d')
    
    if patient_id:
        return f"patients/{patient_id}/{date_prefix}/{document_id}/{file_name}"
    else:
        return f"general/{date_prefix}/{document_id}/{file_name}"


def publish_event(event_detail: Dict[str, Any]) -> None:
    """
    Publish EventBridge event for document processing.
    
    Args:
        event_detail: Event details to publish
    """
    try:
        response = eventbridge_client.put_events(
            Entries=[
                {
                    'Source': 'healthcare.documents',
                    'DetailType': 'Document Uploaded',
                    'Detail': json.dumps(event_detail),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
        
        if response['FailedEntryCount'] > 0:
            logger.error(f"Failed to publish event: {response['Entries']}")
        else:
            logger.info(f"Event published successfully: {event_detail['documentId']}")
            
    except Exception as e:
        logger.error(f"Error publishing event: {str(e)}")
        # Don't fail the upload if event publishing fails
        # The S3 event notification will trigger processing as fallback


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """
    Create error response.
    
    Args:
        status_code: HTTP status code
        message: Error message
        
    Returns:
        Error response dictionary
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': message
        })
    }
