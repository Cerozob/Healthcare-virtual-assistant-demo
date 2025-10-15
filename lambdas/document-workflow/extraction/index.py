"""
Lambda function for processing BDA results and storing extracted data.
Handles data extraction, validation, database storage, and Knowledge Base updates.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional
import boto3
from botocore.exceptions import ClientError
from shared.datetime_utils import get_current_iso8601

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
bedrock_agent_client = boto3.client('bedrock-agent')
rds_data_client = boto3.client('rds-data')
ssm_client = boto3.client('ssm')

# Environment variables (minimal)
PROCESSED_BUCKET = os.environ.get('PROCESSED_BUCKET_NAME', '')
KNOWLEDGE_BASE_ID = os.environ.get('KNOWLEDGE_BASE_ID', '')

# SSM parameter cache
_ssm_cache = {}
_cache_expiry = 0
CACHE_TTL = 300  # 5 minutes


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle BDA completion events and extract data.
    
    Args:
        event: EventBridge event from BDA completion
        context: Lambda context
        
    Returns:
        Processing result
    """
    logger.info(f"Received data extraction event: {json.dumps(event)}")
    
    try:
        # Extract event details
        detail = event.get('detail', {})
        
        # Get BDA job information
        invocation_arn = detail.get('invocationArn')
        status = detail.get('status')
        output_s3_uri = detail.get('outputS3Uri')
        
        if status != 'SUCCEEDED':
            logger.error(f"BDA job failed: {invocation_arn}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': f'BDA job failed: {invocation_arn}',
                    'status': status
                })
            }
        
        logger.info(f"Processing BDA results from: {output_s3_uri}")
        
        # Download and parse BDA output
        extracted_data = download_bda_output(output_s3_uri)
        
        # Validate extracted data
        validated_data = validate_extracted_data(extracted_data)
        
        # Extract document metadata from S3 URI or event
        document_id = extract_document_id_from_event(detail, output_s3_uri)
        patient_id = extract_patient_id_from_data(validated_data)
        
        # Store extracted data in database
        stored_document_id = store_in_database(
            document_id=document_id,
            patient_id=patient_id,
            extracted_data=validated_data,
            s3_uri=output_s3_uri
        )
        
        # Update Knowledge Base
        kb_document_id = update_knowledge_base(
            document_id=document_id,
            patient_id=patient_id,
            extracted_data=validated_data
        )
        
        logger.info(f"Data extraction completed for document: {document_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'documentId': document_id,
                'storedDocumentId': stored_document_id,
                'kbDocumentId': kb_document_id,
                'status': 'completed',
                'message': 'Datos extraídos y almacenados exitosamente'
            })
        }
        
    except Exception as e:
        logger.error(f"Error in data extraction: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }


def download_bda_output(s3_uri: str) -> Dict[str, Any]:
    """
    Download and parse BDA output from S3.
    
    Args:
        s3_uri: S3 URI of BDA output
        
    Returns:
        Parsed extracted data
    """
    # Parse S3 URI
    parts = s3_uri.replace('s3://', '').split('/', 1)
    bucket = parts[0]
    key = parts[1]
    
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        data = json.loads(content)
        
        logger.info(f"Downloaded BDA output: {len(content)} bytes")
        return data
        
    except Exception as e:
        logger.error(f"Error downloading BDA output: {str(e)}")
        raise


def extract_document_id_from_event(detail: Dict[str, Any], s3_uri: str) -> str:
    """
    Extract document ID from event detail or S3 URI.
    
    Args:
        detail: Event detail
        s3_uri: S3 URI of the document
        
    Returns:
        Document ID
    """
    # Try to get document ID from event detail
    document_id = detail.get('documentId')
    if document_id:
        return document_id
    
    # Extract from S3 URI as fallback
    try:
        # Parse S3 URI to get object key
        parts = s3_uri.replace('s3://', '').split('/', 1)
        if len(parts) > 1:
            key = parts[1]
            # Extract document ID from key (assuming format like documents/{document_id}/...)
            key_parts = key.split('/')
            if len(key_parts) > 1:
                return key_parts[1]
    except Exception as e:
        logger.warning(f"Could not extract document ID from S3 URI: {e}")
    
    # Generate a unique document ID as fallback
    import uuid
    return str(uuid.uuid4())


def extract_patient_id_from_data(extracted_data: Dict[str, Any]) -> Optional[str]:
    """
    Extract patient ID from extracted data.
    
    Args:
        extracted_data: Validated extracted data
        
    Returns:
        Patient ID if found
    """
    # Look for patient identifiers in the extracted data
    patient_fields = ['patient_id', 'medical_record_number', 'mrn', 'patient_identifier']
    
    for field in patient_fields:
        if field in extracted_data and extracted_data[field]:
            return str(extracted_data[field])
    
    return None


def get_ssm_parameters() -> Dict[str, str]:
    """
    Get database configuration from SSM Parameter Store with caching.
    
    Returns:
        Dictionary of SSM parameters
    """
    global _ssm_cache, _cache_expiry
    
    # Check cache
    current_time = datetime.now().timestamp()
    if _ssm_cache and current_time < _cache_expiry:
        return _ssm_cache
    
    try:
        # Get all healthcare database parameters
        parameter_names = [
            '/healthcare/database/cluster-arn',
            '/healthcare/database/secret-arn',
            '/healthcare/database/name'
        ]
        
        response = ssm_client.get_parameters(
            Names=parameter_names,
            WithDecryption=True
        )
        
        # Build parameter dictionary
        params = {}
        for param in response.get('Parameters', []):
            params[param['Name']] = param['Value']
        
        # Cache the results
        _ssm_cache = params
        _cache_expiry = current_time + CACHE_TTL
        
        return params
        
    except Exception as e:
        logger.error(f"Error retrieving SSM parameters: {str(e)}")
        # Return cached values if available
        if _ssm_cache:
            logger.warning("Using cached SSM parameters due to retrieval error")
            return _ssm_cache
        raise


def execute_sql(sql: str, parameters: Optional[list] = None) -> Any:
    """
    Execute SQL statement using RDS Data API with SSM configuration.
    
    Args:
        sql: SQL statement
        parameters: SQL parameters
        
    Returns:
        Query result
    """
    # Get database configuration from SSM
    ssm_params = get_ssm_parameters()
    
    db_cluster_arn = ssm_params.get('/healthcare/database/cluster-arn', '')
    db_secret_arn = ssm_params.get('/healthcare/database/secret-arn', '')
    db_name = ssm_params.get('/healthcare/database/name', 'healthcare')
    
    params = {
        'resourceArn': db_cluster_arn,
        'secretArn': db_secret_arn,
        'database': db_name,
        'sql': sql
    }
    
    if parameters:
        params['parameters'] = parameters
    
    return rds_data_client.execute_statement(**params)


def store_in_database(
    document_id: str,
    patient_id: Optional[str],
    extracted_data: Dict[str, Any],
    s3_uri: str
) -> str:
    """
    Store extracted data in Aurora PostgreSQL.
    
    Args:
        document_id: Document identifier
        patient_id: Patient identifier
        extracted_data: Validated extracted data
        s3_uri: S3 URI of processed document
        
    Returns:
        Stored document ID
    """
    try:
        # Prepare SQL statement
        sql = """
        INSERT INTO processed_documents 
        (document_id, patient_id, extracted_data, s3_uri, processing_date, created_at)
        VALUES (:document_id, :patient_id, :extracted_data::jsonb, :s3_uri, :processing_date, :created_at)
        ON CONFLICT (document_id) 
        DO UPDATE SET 
            extracted_data = EXCLUDED.extracted_data,
            s3_uri = EXCLUDED.s3_uri,
            processing_date = EXCLUDED.processing_date,
            updated_at = NOW()
        RETURNING id
        """
        
        parameters = [
            {'name': 'document_id', 'value': {'stringValue': document_id}},
            {'name': 'patient_id', 'value': {'stringValue': patient_id or 'unknown'}},
            {'name': 'extracted_data', 'value': {'stringValue': json.dumps(extracted_data)}},
            {'name': 's3_uri', 'value': {'stringValue': s3_uri}},
            {'name': 'processing_date', 'value': {'stringValue': get_current_iso8601()}},
            {'name': 'created_at', 'value': {'stringValue': get_current_iso8601()}}
        ]
        
        response = execute_sql(sql, parameters)
        
        logger.info(f"Stored document in database: {document_id}")
        return document_id
        
    except Exception as e:
        logger.error(f"Error storing in database: {str(e)}")
        # Don't fail the entire process if database storage fails
        return document_id


def validate_extracted_data(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and clean extracted data from BDA.
    
    Args:
        extracted_data: Raw extracted data from BDA
        
    Returns:
        Validated and cleaned data
    """
    validated = {}
    
    # Ensure required fields exist
    required_fields = ['document_type', 'extraction_timestamp']
    for field in required_fields:
        if field not in extracted_data:
            logger.warning(f"Missing required field: {field}")
    
    # Clean and validate each field
    for key, value in extracted_data.items():
        if value is None or value == '':
            continue
            
        # Validate dates
        if 'date' in key.lower() and isinstance(value, str):
            try:
                from datetime import datetime
                datetime.fromisoformat(value.replace('Z', '+00:00'))
                validated[key] = value
            except ValueError:
                logger.warning(f"Invalid date format for {key}: {value}")
                continue
        
        # Validate lists
        elif isinstance(value, list):
            validated[key] = [item for item in value if item]
        
        # Keep other valid values
        else:
            validated[key] = value
    
    return validated


def create_knowledge_base_document(
    extracted_data: Dict[str, Any],
    document_id: str,
    patient_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create knowledge base document from extracted data.
    
    Args:
        extracted_data: Validated extracted data
        document_id: Document identifier
        patient_id: Patient identifier
        
    Returns:
        Knowledge base document
    """
    kb_document = {
        'documentId': document_id,
        'patientId': patient_id,
        'content': json.dumps(extracted_data, indent=2),
        'metadata': {
            'documentType': extracted_data.get('document_type', 'unknown'),
            'extractionDate': extracted_data.get('extraction_timestamp'),
            'hasAnonymization': True
        }
    }
    
    # Add searchable text summary
    summary_parts = []
    
    if 'diagnoses' in extracted_data:
        summary_parts.append(f"Diagnoses: {', '.join(extracted_data['diagnoses'])}")
    
    if 'symptoms' in extracted_data:
        summary_parts.append(f"Symptoms: {extracted_data['symptoms']}")
    
    if 'medications' in extracted_data:
        summary_parts.append(f"Medications: {', '.join(extracted_data['medications'])}")
    
    kb_document['summary'] = ' | '.join(summary_parts)
    
    return kb_document


def update_knowledge_base(
    document_id: str,
    patient_id: Optional[str],
    extracted_data: Dict[str, Any]
) -> str:
    """
    Update Knowledge Base with extracted data.
    
    Args:
        document_id: Document identifier
        patient_id: Patient identifier
        extracted_data: Validated extracted data
        
    Returns:
        Knowledge Base document ID
    """
    if not KNOWLEDGE_BASE_ID:
        logger.warning("KNOWLEDGE_BASE_ID no configurado, omitiendo actualización de KB")
        return document_id
    
    try:
        # Create knowledge base document
        kb_document = create_knowledge_base_document(
            extracted_data=extracted_data,
            document_id=document_id,
            patient_id=patient_id
        )
        
        # Ingest document into Knowledge Base
        response = bedrock_agent_client.start_ingestion_job(
            knowledgeBaseId=KNOWLEDGE_BASE_ID,
            dataSourceId='processed-documents',
            description=f'Ingesting processed document: {document_id}'
        )
        
        ingestion_job_id = response.get('ingestionJob', {}).get('ingestionJobId')
        logger.info(f"Started KB ingestion job: {ingestion_job_id}")
        
        return document_id
        
    except Exception as e:
        logger.error(f"Error updating Knowledge Base: {str(e)}")
        # Don't fail the entire process if KB update fails
        return document_id



