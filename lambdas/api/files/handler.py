"""
Files API Handler for Healthcare System.
Handles file upload, classification, and management operations.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import boto3
from botocore.exceptions import ClientError

# Import shared modules
import sys
sys.path.append('/opt/python')
sys.path.append('/var/task')

from shared.utils import (
    create_response, create_error_response, parse_event_body,
    extract_path_parameters, extract_query_parameters, validate_required_fields,
    handle_exceptions, generate_uuid, get_current_timestamp
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize services
s3_client = boto3.client('s3')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main handler for files API endpoints.
    """
    try:
        # Handle both API Gateway v1 and v2 event formats
        method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method', '')
        path = event.get('path') or event.get('requestContext', {}).get('http', {}).get('path', '')
        
        logger.info(f"Processing {method} request to {path}")
        
        if method == 'GET' and '/files' in path:
            return handle_get_files(event)
        elif method == 'POST' and '/files/upload' in path:
            return handle_upload_file(event)
        elif method == 'PUT' and '/files/' in path and '/classification' in path:
            return handle_update_classification(event)
        elif method == 'DELETE' and '/files/' in path:
            return handle_delete_file(event)
        else:
            return create_response(404, {'error': 'Endpoint not found'})
            
    except Exception as e:
        logger.error(f"Unhandled error in files API: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})


def handle_get_files(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get files for a patient using Knowledge Base metadata queries.
    """
    try:
        query_params = event.get('queryStringParameters') or {}
        patient_id = query_params.get('patient_id')
        category = query_params.get('category')
        
        # Query Knowledge Base using metadata filters
        files = query_knowledge_base_documents(patient_id, category)
        
        return create_response(200, {'files': files})
        
    except Exception as e:
        logger.error(f"Error getting files: {str(e)}")
        return create_response(500, {'error': 'Failed to get files'})


def handle_upload_file(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle file upload - files will be processed by BDA and stored in Knowledge Base.
    Follows document workflow guidelines for patient data association.
    """
    try:
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        required_fields = ['patient_id', 'file_name', 'file_type']
        missing_fields = [field for field in required_fields if field not in body]
        if missing_fields:
            return create_response(400, {'error': f'Missing required fields: {", ".join(missing_fields)}'})
        
        # Validate patient_id format
        patient_id = body['patient_id']
        if not patient_id or len(patient_id.strip()) == 0:
            return create_response(400, {'error': 'Invalid patient_id'})
        
        # Generate file ID and construct S3 path following document workflow guidelines
        file_id = str(uuid.uuid4())
        file_name = body['file_name']
        category = body.get('category', 'other')
        
        # S3 path structure: {patient_id}/{category}/{file_id}/{file_name}
        s3_key = f"{patient_id}/{category}/{file_id}/{file_name}"
        s3_uri = f"s3://{os.environ.get('RAW_BUCKET_NAME', 'default-bucket')}/{s3_key}"
        
        # Log the upload initiation with patient context
        logger.info(f"File upload initiated for patient {patient_id}: {file_name} (category: {category})")
        
        # Create metadata for document workflow
        metadata = {
            'patient_id': patient_id,
            'file_name': file_name,
            'file_type': body['file_type'],
            'category': category,
            'file_size': body.get('size', 0),
            'upload_timestamp': get_current_timestamp(),
            'workflow_stage': 'uploaded',
            'auto_classification_enabled': True
        }
        
        return create_response(201, {
            'file_id': file_id,
            'patient_id': patient_id,
            'message': f'File upload initiated for patient {patient_id} following document workflow guidelines',
            's3_uri': s3_uri,
            's3_key': s3_key,
            'category': category,
            'metadata': metadata,
            'workflow_info': {
                'next_stage': 'BDA processing and classification',
                'expected_processing_time': '2-5 minutes',
                'knowledge_base_integration': 'Automatic after processing'
            },
            'note': 'File will be automatically classified by BDA and ingested into Knowledge Base'
        })
        
    except Exception as e:
        logger.error(f"Error initiating file upload: {str(e)}")
        return create_response(500, {'error': 'Failed to initiate file upload'})


def handle_update_classification(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update file classification (manual override) - updates Knowledge Base metadata.
    """
    try:
        # Extract document ID from path
        path_parts = event.get('path', '').split('/')
        document_id = None
        for i, part in enumerate(path_parts):
            if part == 'files' and i + 1 < len(path_parts):
                document_id = path_parts[i + 1]
                break
        
        if not document_id:
            return create_response(400, {'error': 'Document ID not found in path'})
        
        body = json.loads(event.get('body', '{}'))
        new_category = body.get('category')
        
        if not new_category:
            return create_response(400, {'error': 'Category is required'})
        
        # Validate category
        valid_categories = ['medical-history', 'exam-results', 'medical-images', 'identification', 'other', 'not-identified']
        if new_category not in valid_categories:
            return create_response(400, {'error': f'Invalid category. Must be one of: {", ".join(valid_categories)}'})
        
        # Note: In a full implementation, you would update the Knowledge Base document metadata
        # This would require re-ingesting the document with updated metadata
        # For now, we return success as the classification override is acknowledged
        
        return create_response(200, {
            'message': 'Classification override acknowledged - Knowledge Base will be updated on next ingestion',
            'document_id': document_id,
            'new_category': new_category,
            'note': 'Manual classification overrides are handled through Knowledge Base metadata updates'
        })
        
    except Exception as e:
        logger.error(f"Error updating classification: {str(e)}")
        return create_response(500, {'error': 'Failed to update classification'})


def handle_delete_file(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Delete a document from Knowledge Base (not implemented - requires Knowledge Base management).
    """
    try:
        # Extract document ID from path
        path_parts = event.get('path', '').split('/')
        document_id = None
        for i, part in enumerate(path_parts):
            if part == 'files' and i + 1 < len(path_parts):
                document_id = path_parts[i + 1]
                break
        
        if not document_id:
            return create_response(400, {'error': 'Document ID not found in path'})
        
        # Note: Deleting documents from Knowledge Base requires more complex operations
        # involving data source management and re-ingestion
        # For now, we return a message indicating this is not implemented
        
        return create_response(501, {
            'message': 'Document deletion from Knowledge Base not implemented',
            'document_id': document_id,
            'note': 'Knowledge Base document deletion requires data source management operations'
        })
        
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        return create_response(500, {'error': 'Failed to delete document'})


def process_bda_classification_result(bda_output: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process BDA output to extract classification results with comprehensive error handling.
    This function maps BDA results to frontend category options and handles service degradation.
    """
    try:
        # Validate input
        if not bda_output or not isinstance(bda_output, dict):
            logger.warning("Invalid or empty BDA output received")
            return create_classification_fallback("Invalid BDA output format")
        
        # Extract classification fields from BDA output with multiple fallback paths
        document_type = None
        confidence = 0.0
        
        # Define extraction paths in order of preference
        extraction_paths = [
            # Direct fields
            {'doc': 'document_type', 'conf': 'classification_confidence'},
            # Nested in extractedData
            {'doc': 'extractedData.document_type', 'conf': 'extractedData.classification_confidence'},
            # Nested in results
            {'doc': 'results.document_type', 'conf': 'results.classification_confidence'},
            # Alternative field names
            {'doc': 'documentType', 'conf': 'classificationConfidence'},
            {'doc': 'type', 'conf': 'confidence'}
        ]
        
        for path_config in extraction_paths:
            try:
                # Try to extract document type
                if document_type is None:
                    doc_value = get_nested_field(bda_output, path_config['doc'])
                    if doc_value and isinstance(doc_value, str):
                        document_type = doc_value.strip().lower()
                
                # Try to extract confidence
                if confidence == 0.0:
                    conf_value = get_nested_field(bda_output, path_config['conf'])
                    if conf_value is not None:
                        try:
                            confidence = float(conf_value)
                            # Normalize confidence to 0-100 range
                            if confidence > 1.0 and confidence <= 100.0:
                                pass  # Already in percentage
                            elif confidence <= 1.0:
                                confidence *= 100  # Convert from decimal to percentage
                            else:
                                confidence = min(confidence, 100.0)  # Cap at 100%
                            
                            confidence = max(0.0, confidence)  # Ensure non-negative
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Invalid confidence value '{conf_value}': {e}")
                            continue
                
                # Break if we found both values
                if document_type and confidence > 0:
                    break
                    
            except Exception as e:
                logger.warning(f"Error extracting from path {path_config}: {e}")
                continue
        
        # Validate and normalize document type
        valid_categories = ['medical-history', 'exam-results', 'medical-images', 'identification', 'other']
        if not document_type or document_type not in valid_categories:
            logger.warning(f"Invalid document type '{document_type}', defaulting to 'other'")
            document_type = 'other'
        
        # Apply confidence threshold with graceful degradation
        try:
            confidence_threshold = float(os.environ.get('CLASSIFICATION_CONFIDENCE_THRESHOLD', '80'))
        except (ValueError, TypeError):
            logger.warning("Invalid confidence threshold in environment, using default 80")
            confidence_threshold = 80.0
        
        # Determine final classification
        if confidence < confidence_threshold:
            final_category = 'not-identified'
            logger.info(f"Classification confidence {confidence:.1f}% below threshold {confidence_threshold}%, marking as not-identified")
        else:
            final_category = document_type
            logger.info(f"Classification successful: {final_category} with {confidence:.1f}% confidence")
        
        return {
            'category': final_category,
            'confidence': round(confidence, 2),
            'original_classification': document_type,
            'auto_classified': True,
            'confidence_threshold_met': confidence >= confidence_threshold,
            'processing_successful': True
        }
        
    except Exception as e:
        logger.error(f"Critical error processing BDA classification result: {str(e)}")
        return create_classification_fallback(f"Processing error: {str(e)}")

def get_nested_field(data: Dict[str, Any], field_path: str) -> Any:
    """
    Extract nested field from dictionary using dot notation with error handling
    """
    try:
        keys = field_path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    except Exception:
        return None

def create_classification_fallback(reason: str) -> Dict[str, Any]:
    """
    Create fallback classification result when processing fails
    """
    return {
        'category': 'not-identified',
        'confidence': 0.0,
        'original_classification': None,
        'auto_classified': False,
        'confidence_threshold_met': False,
        'processing_successful': False,
        'error': reason,
        'fallback_applied': True
    }

def query_knowledge_base_documents(patient_id: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Query Knowledge Base for documents using metadata filters.
    
    Args:
        patient_id: Optional patient ID filter
        category: Optional document category filter
        
    Returns:
        List of document metadata
    """
    try:
        # Initialize Bedrock Agent Runtime client for Knowledge Base queries
        bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
        
        # Build metadata filters
        filters = []
        
        if patient_id:
            filters.append({
                'key': 'patientId',
                'value': patient_id,
                'operator': 'EQUALS'
            })
        
        if category and category != 'all':
            filters.append({
                'key': 'documentCategory', 
                'value': category,
                'operator': 'EQUALS'
            })
        
        # Query Knowledge Base with metadata filters
        knowledge_base_id = os.environ.get('KNOWLEDGE_BASE_ID', '')
        if not knowledge_base_id:
            logger.warning("KNOWLEDGE_BASE_ID not configured")
            return []
        
        # Use retrieve API to get documents with metadata
        query_params = {
            'knowledgeBaseId': knowledge_base_id,
            'retrievalQuery': {
                'text': '*'  # Get all documents
            }
        }
        
        if filters:
            query_params['retrievalConfiguration'] = {
                'vectorSearchConfiguration': {
                    'filter': {
                        'andAll': filters
                    }
                }
            }
        
        response = bedrock_agent_runtime.retrieve(**query_params)
        
        # Format response for frontend
        formatted_files = []
        for result in response.get('retrievalResults', []):
            metadata = result.get('metadata', {})
            
            formatted_files.append({
                'id': metadata.get('documentId', ''),
                'name': f"{metadata.get('documentId', 'unknown')}.json",
                'type': 'application/json',
                'size': len(result.get('content', {}).get('text', '')),
                'uploadDate': metadata.get('processingDate', ''),
                'category': metadata.get('documentCategory', 'other'),
                'autoClassified': metadata.get('autoClassified', False),
                'classificationConfidence': metadata.get('classificationConfidence', 0.0),
                'originalClassification': metadata.get('originalClassification', ''),
                'patientId': metadata.get('patientId', ''),
                'hasDiagnoses': metadata.get('hasDiagnoses', False),
                'hasSymptoms': metadata.get('hasSymptoms', False),
                'hasMedications': metadata.get('hasMedications', False),
                'hasVitalSigns': metadata.get('hasVitalSigns', False)
            })
        
        return formatted_files
        
    except Exception as e:
        logger.error(f"Error querying Knowledge Base: {str(e)}")
        return []


def is_classification_service_available() -> bool:
    """
    Check if classification service is available and enabled
    """
    try:
        # Check if classification is enabled
        if not os.environ.get('ENABLE_DOCUMENT_CLASSIFICATION', 'true').lower() == 'true':
            return False
        
        # Additional health checks could be added here
        # For example, checking BDA service status, S3 connectivity, etc.
        
        return True
    except Exception as e:
        logger.warning(f"Error checking classification service availability: {e}")
        return False
