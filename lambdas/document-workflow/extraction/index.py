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
        
        # Organize processed data in clean bucket structure
        organized_s3_uri = organize_processed_data(
            document_id=document_id,
            patient_id=patient_id,
            extracted_data=validated_data
        )
        
        # Store extracted data in database
        stored_document_id = store_in_database(
            document_id=document_id,
            patient_id=patient_id,
            extracted_data=validated_data,
            s3_uri=organized_s3_uri or output_s3_uri
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
                'patientId': patient_id,
                'storedDocumentId': stored_document_id,
                'kbDocumentId': kb_document_id,
                'organizedS3Uri': organized_s3_uri,
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
    Download and parse BDA output from S3, handling the complex BDA output structure.
    
    Args:
        s3_uri: S3 URI of BDA output directory
        
    Returns:
        Parsed extracted data with metadata
    """
    # Parse S3 URI to get bucket and prefix
    parts = s3_uri.replace('s3://', '').split('/', 1)
    bucket = parts[0]
    prefix = parts[1] if len(parts) > 1 else ''
    
    try:
        # List all objects in the BDA output directory
        response = s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix
        )
        
        if 'Contents' not in response:
            raise ValueError(f"No BDA output files found at {s3_uri}")
        
        # Find the result files in the BDA output structure
        result_files = {}
        job_metadata = None
        
        for obj in response['Contents']:
            key = obj['Key']
            
            # Skip empty files and access check files
            if obj['Size'] == 0 or '.s3_access_check' in key:
                continue
            
            # Extract job metadata
            if key.endswith('job_metadata.json'):
                job_metadata = download_json_file(bucket, key)
                continue
            
            # Find result files (custom_output and standard_output)
            if '/result.json' in key:
                if '/custom_output/' in key:
                    result_files['custom_result'] = download_json_file(bucket, key)
                elif '/standard_output/' in key:
                    result_files['standard_result'] = download_json_file(bucket, key)
            
            # Also capture other formats for completeness
            elif key.endswith('/result.html'):
                result_files['html_result'] = download_text_file(bucket, key)
            elif key.endswith('/result.md'):
                result_files['markdown_result'] = download_text_file(bucket, key)
            elif key.endswith('/result.txt'):
                result_files['text_result'] = download_text_file(bucket, key)
        
        # Combine all extracted data
        extracted_data = {
            'bda_job_metadata': job_metadata,
            'extraction_timestamp': get_current_iso8601(),
            'source_s3_uri': s3_uri,
            'result_files': result_files
        }
        
        # Use custom result if available, otherwise standard result
        primary_result = result_files.get('custom_result') or result_files.get('standard_result')
        if primary_result:
            # Merge primary result data into the main extracted_data
            if isinstance(primary_result, dict):
                extracted_data.update(primary_result)
        
        logger.info(f"Downloaded BDA output with {len(result_files)} result files")
        return extracted_data
        
    except Exception as e:
        logger.error(f"Error downloading BDA output: {str(e)}")
        raise


def download_json_file(bucket: str, key: str) -> Dict[str, Any]:
    """Download and parse JSON file from S3."""
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        return json.loads(content)
    except Exception as e:
        logger.warning(f"Error parsing JSON file {key}: {e}")
        return {}


def download_text_file(bucket: str, key: str) -> str:
    """Download text file from S3."""
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        return response['Body'].read().decode('utf-8')
    except Exception as e:
        logger.warning(f"Error downloading text file {key}: {e}")
        return ""


def extract_document_id_from_event(detail: Dict[str, Any], s3_uri: str) -> str:
    """
    Extract document ID from event detail or S3 URI.
    
    Args:
        detail: Event detail
        s3_uri: S3 URI of the BDA output
        
    Returns:
        Document ID
    """
    # Try to get document ID from event detail
    document_id = detail.get('documentId')
    if document_id:
        return document_id
    
    # Extract from S3 URI - BDA output structure is:
    # processed/{patient_id}/{original_filename}/{job_id}/...
    try:
        parts = s3_uri.replace('s3://', '').split('/', 1)
        if len(parts) > 1:
            key = parts[1]
            key_parts = key.split('/')
            
            # Expected structure: processed/{patient_id}/{filename}/{job_id}/...
            if len(key_parts) >= 3:
                patient_id = key_parts[1]
                filename = key_parts[2]
                
                # Create document ID from patient_id and filename
                # Remove file extension and any timestamp suffixes
                clean_filename = filename.split('.')[0]
                document_id = f"{patient_id}_{clean_filename}"
                
                logger.info(f"Extracted document ID: {document_id} from BDA output path")
                return document_id
                
    except Exception as e:
        logger.warning(f"Could not extract document ID from S3 URI: {e}")
    
    # Generate a unique document ID as fallback
    import uuid
    fallback_id = str(uuid.uuid4())
    logger.warning(f"Using fallback document ID: {fallback_id}")
    return fallback_id


def extract_patient_id_from_data(extracted_data: Dict[str, Any]) -> Optional[str]:
    """
    Extract patient ID from extracted data or S3 URI structure.
    
    Args:
        extracted_data: Validated extracted data
        
    Returns:
        Patient ID if found
    """
    # First, try to extract from the S3 URI structure
    source_uri = extracted_data.get('source_s3_uri', '')
    if source_uri:
        try:
            parts = source_uri.replace('s3://', '').split('/', 1)
            if len(parts) > 1:
                key_parts = parts[1].split('/')
                # Expected structure: processed/{patient_id}/{filename}/{job_id}/...
                if len(key_parts) >= 2:
                    patient_id = key_parts[1]
                    logger.info(f"Extracted patient ID from S3 structure: {patient_id}")
                    return patient_id
        except Exception as e:
            logger.warning(f"Could not extract patient ID from S3 URI: {e}")
    
    # Look for patient identifiers in the extracted data
    patient_fields = ['patient_id', 'medical_record_number', 'mrn', 'patient_identifier', 'patientId']
    
    for field in patient_fields:
        if field in extracted_data and extracted_data[field]:
            return str(extracted_data[field])
    
    # Check in nested result files
    result_files = extracted_data.get('result_files', {})
    for result_data in result_files.values():
        if isinstance(result_data, dict):
            for field in patient_fields:
                if field in result_data and result_data[field]:
                    return str(result_data[field])
    
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


def organize_processed_data(
    document_id: str,
    patient_id: Optional[str],
    extracted_data: Dict[str, Any]
) -> str:
    """
    Organize and store processed data in the processed bucket with clean structure.
    
    Args:
        document_id: Document identifier
        patient_id: Patient identifier
        extracted_data: Validated extracted data
        
    Returns:
        S3 URI of organized processed data
    """
    if not PROCESSED_BUCKET:
        logger.warning("PROCESSED_BUCKET not configured, skipping data organization")
        return ""
    
    try:
        # Create clean organized structure: processed/{patient_id}/{document_id}/
        clean_patient_id = patient_id or 'unknown'
        processed_key_prefix = f"processed/{clean_patient_id}/{document_id}"
        
        # Store the main extracted data as JSON
        main_data_key = f"{processed_key_prefix}/extracted_data.json"
        
        # Prepare clean extracted data (remove BDA metadata for main file)
        clean_data = {k: v for k, v in extracted_data.items() 
                     if k not in ['bda_job_metadata', 'source_s3_uri', 'result_files']}
        
        # Add metadata
        clean_data['processing_metadata'] = {
            'document_id': document_id,
            'patient_id': patient_id,
            'processing_timestamp': get_current_iso8601(),
            'source_bda_uri': extracted_data.get('source_s3_uri')
        }
        
        # Upload main extracted data
        s3_client.put_object(
            Bucket=PROCESSED_BUCKET,
            Key=main_data_key,
            Body=json.dumps(clean_data, indent=2, ensure_ascii=False),
            ContentType='application/json'
        )
        
        # Store individual result files if they exist
        result_files = extracted_data.get('result_files', {})
        for file_type, content in result_files.items():
            if content:
                file_key = f"{processed_key_prefix}/{file_type}"
                
                if isinstance(content, dict):
                    # JSON content
                    s3_client.put_object(
                        Bucket=PROCESSED_BUCKET,
                        Key=f"{file_key}.json",
                        Body=json.dumps(content, indent=2, ensure_ascii=False),
                        ContentType='application/json'
                    )
                else:
                    # Text content (HTML, MD, TXT)
                    extension = 'txt'
                    content_type = 'text/plain'
                    
                    if 'html' in file_type:
                        extension = 'html'
                        content_type = 'text/html'
                    elif 'markdown' in file_type:
                        extension = 'md'
                        content_type = 'text/markdown'
                    
                    s3_client.put_object(
                        Bucket=PROCESSED_BUCKET,
                        Key=f"{file_key}.{extension}",
                        Body=content,
                        ContentType=content_type
                    )
        
        # Store BDA metadata separately
        if extracted_data.get('bda_job_metadata'):
            metadata_key = f"{processed_key_prefix}/bda_metadata.json"
            s3_client.put_object(
                Bucket=PROCESSED_BUCKET,
                Key=metadata_key,
                Body=json.dumps(extracted_data['bda_job_metadata'], indent=2),
                ContentType='application/json'
            )
        
        processed_uri = f"s3://{PROCESSED_BUCKET}/{main_data_key}"
        logger.info(f"Organized processed data at: {processed_uri}")
        return processed_uri
        
    except Exception as e:
        logger.error(f"Error organizing processed data: {str(e)}")
        return ""


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
    
    # Copy metadata fields
    metadata_fields = ['bda_job_metadata', 'extraction_timestamp', 'source_s3_uri', 'result_files']
    for field in metadata_fields:
        if field in extracted_data:
            validated[field] = extracted_data[field]
    
    # Ensure required fields exist
    if 'extraction_timestamp' not in validated:
        validated['extraction_timestamp'] = get_current_iso8601()
    
    # Clean and validate each field
    for key, value in extracted_data.items():
        if key in metadata_fields:
            continue  # Already handled above
            
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
    
    # Try to infer document type from BDA metadata or filename
    if 'document_type' not in validated:
        source_uri = validated.get('source_s3_uri', '')
        if 'historia_clinica' in source_uri.lower():
            validated['document_type'] = 'historia_clinica'
        elif 'laboratorio' in source_uri.lower():
            validated['document_type'] = 'laboratorio'
        elif 'radiologia' in source_uri.lower():
            validated['document_type'] = 'radiologia'
        else:
            validated['document_type'] = 'unknown'
    
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
    # Create clean content without BDA metadata for KB
    clean_content = {k: v for k, v in extracted_data.items() 
                    if k not in ['bda_job_metadata', 'source_s3_uri']}
    
    kb_document = {
        'documentId': document_id,
        'patientId': patient_id,
        'content': json.dumps(clean_content, indent=2, ensure_ascii=False),
        'metadata': {
            'documentType': extracted_data.get('document_type', 'unknown'),
            'extractionDate': extracted_data.get('extraction_timestamp'),
            'hasAnonymization': True
        }
    }
    
    # Add searchable text summary from all result files
    summary_parts = []
    
    # Check main extracted data
    for field in ['diagnoses', 'diagnosticos', 'diagnosis']:
        if field in extracted_data and extracted_data[field]:
            diagnoses = extracted_data[field]
            if isinstance(diagnoses, list):
                summary_parts.append(f"Diagnósticos: {', '.join(diagnoses)}")
            else:
                summary_parts.append(f"Diagnósticos: {diagnoses}")
            break
    
    for field in ['symptoms', 'sintomas', 'symptom']:
        if field in extracted_data and extracted_data[field]:
            symptoms = extracted_data[field]
            if isinstance(symptoms, list):
                summary_parts.append(f"Síntomas: {', '.join(symptoms)}")
            else:
                summary_parts.append(f"Síntomas: {symptoms}")
            break
    
    for field in ['medications', 'medicamentos', 'medication']:
        if field in extracted_data and extracted_data[field]:
            medications = extracted_data[field]
            if isinstance(medications, list):
                summary_parts.append(f"Medicamentos: {', '.join(medications)}")
            else:
                summary_parts.append(f"Medicamentos: {medications}")
            break
    
    # Also check in result files
    result_files = extracted_data.get('result_files', {})
    for result_data in result_files.values():
        if isinstance(result_data, dict):
            for field in ['diagnoses', 'symptoms', 'medications']:
                if field in result_data and result_data[field]:
                    value = result_data[field]
                    if isinstance(value, list):
                        summary_parts.append(f"{field.title()}: {', '.join(value)}")
                    else:
                        summary_parts.append(f"{field.title()}: {value}")
    
    kb_document['summary'] = ' | '.join(summary_parts) if summary_parts else 'Documento médico procesado'
    
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



