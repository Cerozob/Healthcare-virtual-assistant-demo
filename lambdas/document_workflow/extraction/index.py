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
CLASSIFICATION_CONFIDENCE_THRESHOLD = float(os.environ.get('CLASSIFICATION_CONFIDENCE_THRESHOLD', '80'))

# SSM parameter cache
_ssm_cache = {}
_cache_expiry = 0
CACHE_TTL = 300  # 5 minutes


def get_knowledge_base_config() -> Dict[str, str]:
    """Get Knowledge Base configuration from SSM parameters with caching."""
    global _ssm_cache, _cache_expiry
    
    current_time = datetime.now().timestamp()
    
    # Check if cache is still valid
    if current_time < _cache_expiry and 'knowledge_base_id' in _ssm_cache:
        return _ssm_cache
    
    try:
        # Get Knowledge Base parameters from SSM
        response = ssm_client.get_parameters(
            Names=[
                '/healthcare/knowledge-base/id',
                '/healthcare/knowledge-base/data-source-id'
            ]
        )
        
        # Parse parameters
        params = {param['Name'].split('/')[-1]: param['Value'] for param in response['Parameters']}
        
        _ssm_cache = {
            'knowledge_base_id': params.get('id', ''),
            'data_source_id': params.get('data-source-id', '')
        }
        
        # Set cache expiry
        _cache_expiry = current_time + CACHE_TTL
        
        logger.info("Retrieved Knowledge Base configuration from SSM")
        return _ssm_cache
        
    except Exception as e:
        logger.warning(f"Failed to get Knowledge Base configuration from SSM: {e}")
        # Return empty config if SSM fails
        return {'knowledge_base_id': '', 'data_source_id': ''}


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

        # Get BDA job information from the correct event structure
        job_id = detail.get('job_id')
        status = detail.get('job_status')
        output_s3_location = detail.get('output_s3_location', {})
        
        # Construct S3 URI from output location
        output_bucket = output_s3_location.get('s3_bucket', '')
        output_key = output_s3_location.get('name', '')
        output_s3_uri = f"s3://{output_bucket}/{output_key}" if output_bucket and output_key else None

        if status != 'SUCCESS':
            logger.error(f"BDA job failed: {job_id} with status: {status}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': f'BDA job failed: {job_id}',
                    'status': status
                })
            }

        if not output_s3_uri:
            logger.error(f"No valid output S3 URI found for job {job_id}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': f'No valid output S3 URI found for job {job_id}',
                    'status': 'error'
                })
            }

        logger.info(f"Processing BDA results for job {job_id} from: {output_s3_uri}")

        # Download and parse BDA output
        extracted_data = download_bda_output(output_s3_uri)

        # Validate extracted data
        validated_data = validate_extracted_data(extracted_data)

        # Extract document metadata from S3 URI or event
        document_id = extract_document_id_from_event(detail, output_s3_uri, job_id)
        patient_id = extract_patient_id_from_data(validated_data)

        # Extract classification information
        classification = extract_classification_from_data(validated_data)

        # Organize processed data in clean bucket structure
        organized_s3_uri = organize_processed_data(
            document_id=document_id,
            patient_id=patient_id,
            extracted_data=validated_data,
            classification=classification
        )

        # Update original document metadata with classification
        update_original_document_metadata(
            document_id=document_id,
            patient_id=patient_id,
            classification=classification
        )

        # Update Knowledge Base with classification metadata
        kb_document_id = update_knowledge_base(
            document_id=document_id,
            patient_id=patient_id,
            extracted_data=validated_data,
            classification=classification
        )

        logger.info(f"Data extraction completed for document: {document_id}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'documentId': document_id,
                'patientId': patient_id,
                'kbDocumentId': kb_document_id,
                'organizedS3Uri': organized_s3_uri,
                'classification': classification,
                'status': 'completed',
                'message': 'Datos extraídos, clasificados y almacenados en Knowledge Base exitosamente'
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
                    result_files['custom_result'] = download_json_file(
                        bucket, key)
                elif '/standard_output/' in key:
                    result_files['standard_result'] = download_json_file(
                        bucket, key)

            # Also capture other formats for completeness
            elif key.endswith('/result.html'):
                result_files['html_result'] = download_text_file(bucket, key)
            elif key.endswith('/result.md'):
                result_files['markdown_result'] = download_text_file(
                    bucket, key)
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
        primary_result = result_files.get(
            'custom_result') or result_files.get('standard_result')
        if primary_result:
            # Merge primary result data into the main extracted_data
            if isinstance(primary_result, dict):
                extracted_data.update(primary_result)

        logger.info(
            f"Downloaded BDA output with {len(result_files)} result files")
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


def extract_document_id_from_event(detail: Dict[str, Any], s3_uri: str, job_id: str) -> str:
    """
    Extract document ID from event detail or S3 URI using the BDA event structure.

    Args:
        detail: Event detail from BDA completion event
        s3_uri: S3 URI of the BDA output
        job_id: BDA job ID

    Returns:
        Document ID
    """
    # Try to get document ID from event detail
    document_id = detail.get('documentId')
    if document_id:
        return document_id

    # Extract from input S3 object information in the BDA event
    # BDA event structure has input_s3_object with s3_bucket and name
    input_s3_object = detail.get('input_s3_object', {})
    if input_s3_object:
        input_bucket = input_s3_object.get('s3_bucket', '')
        input_key = input_s3_object.get('name', '')
        
        logger.info(f"BDA input S3 object - bucket: {input_bucket}, key: {input_key}")
        
        if input_key:
            # Frontend uploads with structure: {patient_id}/{filename}
            key_parts = input_key.split('/')
            
            if len(key_parts) >= 2:
                patient_id = key_parts[0]
                filename = key_parts[-1]  # Last part is always the filename
                
                # Create document ID from patient_id and filename
                clean_filename = filename.split('.')[0]  # Remove extension
                document_id = f"{patient_id}_{clean_filename}"
                
                logger.info(f"Extracted document ID: {document_id} from BDA input S3 object")
                return document_id
            elif len(key_parts) == 1:
                # Single filename without patient prefix
                filename = key_parts[0]
                clean_filename = filename.split('.')[0]
                logger.info(f"Extracted document ID: {clean_filename} from single filename")
                return clean_filename

    # Fallback: Extract from BDA output S3 URI structure
    try:
        if s3_uri:
            parts = s3_uri.replace('s3://', '').split('/', 1)
            if len(parts) > 1:
                key = parts[1]
                key_parts = key.split('/')

                # BDA output structure varies, try to find patient_id and filename
                if len(key_parts) >= 3:
                    # Look for patterns in the BDA output path
                    for i, part in enumerate(key_parts):
                        # Skip common BDA directories
                        if part in ['processed', 'output', 'results']:
                            continue
                        # Look for patient_id pattern (alphanumeric)
                        if part.replace('_', '').replace('-', '').isalnum() and len(part) > 2:
                            patient_id = part
                            # Next meaningful part might be filename
                            if i + 1 < len(key_parts):
                                filename = key_parts[i + 1]
                                clean_filename = filename.split('.')[0]
                                document_id = f"{patient_id}_{clean_filename}"
                                logger.info(f"Extracted document ID: {document_id} from BDA output path")
                                return document_id

    except Exception as e:
        logger.warning(f"Could not extract document ID from S3 URI: {e}")

    # Use job ID as fallback document ID
    logger.warning(f"Using job ID as document ID fallback: {job_id}")
    return job_id


def extract_patient_id_from_data(extracted_data: Dict[str, Any]) -> Optional[str]:
    """
    Extract patient ID from extracted data, BDA job metadata, or S3 URI structure.

    Args:
        extracted_data: Validated extracted data

    Returns:
        Patient ID if found
    """
    # First, try to extract from BDA job metadata if available
    bda_metadata = extracted_data.get('bda_job_metadata', {})
    if bda_metadata:
        # Check if BDA metadata contains input S3 information
        input_s3_info = bda_metadata.get('input_s3_object', {})
        if input_s3_info:
            input_key = input_s3_info.get('name', '')
            if input_key:
                key_parts = input_key.split('/')
                if len(key_parts) >= 1:
                    patient_id = key_parts[0]
                    logger.info(f"Extracted patient ID from BDA metadata: {patient_id}")
                    return patient_id

    # Try to extract from the S3 URI structure
    source_uri = extracted_data.get('source_s3_uri', '')
    if source_uri:
        try:
            parts = source_uri.replace('s3://', '').split('/', 1)
            if len(parts) > 1:
                key_parts = parts[1].split('/')
                # BDA output structure varies, look for patient_id patterns
                for part in key_parts:
                    # Skip common BDA directories
                    if part in ['processed', 'output', 'results', 'custom_output', 'standard_output']:
                        continue
                    # Look for patient_id pattern (alphanumeric, reasonable length)
                    if part.replace('_', '').replace('-', '').isalnum() and 3 <= len(part) <= 20:
                        logger.info(f"Extracted patient ID from S3 structure: {part}")
                        return part
        except Exception as e:
            logger.warning(f"Could not extract patient ID from S3 URI: {e}")

    # Look for patient identifiers in the extracted data
    patient_fields = ['patient_id', 'medical_record_number',
                      'mrn', 'patient_identifier', 'patientId']

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


def extract_classification_from_data(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract document classification from BDA output.
    
    Args:
        extracted_data: Validated extracted data from BDA
        
    Returns:
        Classification information
    """
    try:
        document_type = None
        confidence = 0.0
        matched_blueprint_confidence = 0.0
        
        logger.info(f"Extracting classification from BDA data: {json.dumps(extracted_data, indent=2)}")
        
        # Look for classification fields in main data
        if 'document_type' in extracted_data:
            document_type = extracted_data['document_type']
        if 'classification_confidence' in extracted_data:
            confidence = float(extracted_data['classification_confidence'])
        
        # Check in result files for BDA custom output structure
        result_files = extracted_data.get('result_files', {})
        
        # Look specifically for custom_result which contains the BDA blueprint output
        custom_result = result_files.get('custom_result')
        if custom_result and isinstance(custom_result, dict):
            logger.info(f"Found custom_result: {json.dumps(custom_result, indent=2)}")
            
            # Extract from matched_blueprint confidence
            matched_blueprint = custom_result.get('matched_blueprint', {})
            if matched_blueprint and 'confidence' in matched_blueprint:
                matched_blueprint_confidence = float(matched_blueprint['confidence'])
                logger.info(f"Matched blueprint confidence: {matched_blueprint_confidence}")
            
            # Extract from inference_result.document_type
            inference_result = custom_result.get('inference_result', {})
            if inference_result and 'document_type' in inference_result:
                document_type = inference_result['document_type']
                logger.info(f"Found document_type in inference_result: {document_type}")
            
            # Also check for classification_confidence in inference_result
            if inference_result and 'classification_confidence' in inference_result:
                confidence_str = inference_result['classification_confidence']
                if confidence_str and confidence_str.strip():
                    try:
                        confidence = float(confidence_str)
                    except (ValueError, TypeError):
                        logger.warning(f"Could not parse classification_confidence: {confidence_str}")
        
        # Check other result files if not found in custom_result
        if not document_type or confidence == 0.0:
            for result_name, result_data in result_files.items():
                if isinstance(result_data, dict):
                    if not document_type and 'document_type' in result_data:
                        document_type = result_data['document_type']
                        logger.info(f"Found document_type in {result_name}: {document_type}")
                    if confidence == 0.0 and 'classification_confidence' in result_data:
                        try:
                            confidence = float(result_data['classification_confidence'])
                            logger.info(f"Found classification_confidence in {result_name}: {confidence}")
                        except (ValueError, TypeError):
                            pass
        
        # Use matched_blueprint confidence if no explicit classification confidence
        if confidence == 0.0 and matched_blueprint_confidence > 0.0:
            # Convert blueprint confidence (0-1) to percentage (0-100)
            confidence = matched_blueprint_confidence * 100
            logger.info(f"Using matched_blueprint confidence as classification confidence: {confidence}%")
        
        logger.info(f"Extracted classification - document_type: {document_type}, confidence: {confidence}")
        
        # Validate and normalize document type
        valid_categories = ['medical-history', 'exam-results', 'medical-images', 'identification', 'other']
        original_document_type = document_type
        
        if not document_type:
            document_type = 'other'
        elif document_type not in valid_categories:
            # Try to map common variations
            document_type_lower = document_type.lower()
            if 'exam' in document_type_lower or 'result' in document_type_lower or 'lab' in document_type_lower:
                document_type = 'exam-results'
            elif 'history' in document_type_lower or 'historia' in document_type_lower or 'record' in document_type_lower:
                document_type = 'medical-history'
            elif 'image' in document_type_lower or 'radio' in document_type_lower or 'scan' in document_type_lower:
                document_type = 'medical-images'
            elif 'id' in document_type_lower or 'cedula' in document_type_lower or 'identification' in document_type_lower:
                document_type = 'identification'
            else:
                document_type = 'other'
            
            logger.info(f"Mapped document type '{original_document_type}' to '{document_type}'")
        
        # Apply confidence threshold
        if confidence < CLASSIFICATION_CONFIDENCE_THRESHOLD:
            final_category = 'not-identified'
            logger.info(f"Classification confidence {confidence}% below threshold {CLASSIFICATION_CONFIDENCE_THRESHOLD}%, setting category to 'not-identified'")
        else:
            final_category = document_type
            logger.info(f"Classification confidence {confidence}% meets threshold, using category '{final_category}'")
        
        classification_result = {
            'category': final_category,
            'confidence': confidence,
            'original_classification': original_document_type,
            'auto_classified': True,
            'confidence_threshold_met': confidence >= CLASSIFICATION_CONFIDENCE_THRESHOLD,
            'matched_blueprint_confidence': matched_blueprint_confidence
        }
        
        logger.info(f"Final classification result: {json.dumps(classification_result, indent=2)}")
        return classification_result
        
    except Exception as e:
        logger.error(f"Error extracting classification: {str(e)}", exc_info=True)
        return {
            'category': 'not-identified',
            'confidence': 0.0,
            'original_classification': None,
            'auto_classified': False,
            'confidence_threshold_met': False
        }



def extract_filename_from_uri(s3_uri: str) -> Optional[str]:
    """
    Extract filename from S3 URI.
    
    Args:
        s3_uri: S3 URI
        
    Returns:
        Filename if found
    """
    try:
        parts = s3_uri.replace('s3://', '').split('/')
        if len(parts) > 1:
            # Look for original filename in the path structure
            for part in reversed(parts):
                if '.' in part and not part.startswith('.'):
                    return part
        return None
    except Exception:
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
            logger.warning(
                "Using cached SSM parameters due to retrieval error")
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
    extracted_data: Dict[str, Any],
    classification: Optional[Dict[str, Any]] = None
) -> str:
    """
    Organize and store processed data in the processed bucket with proper patient/document structure.
    
    Creates structure: processed/{patient_id}/{document_identifier}/
    Following the same pattern as the frontend upload structure.

    Args:
        document_id: Document identifier
        patient_id: Patient identifier
        extracted_data: Validated extracted data
        classification: Classification information to include in metadata

    Returns:
        S3 URI of organized processed data
    """
    if not PROCESSED_BUCKET:
        logger.warning(
            "PROCESSED_BUCKET not configured, skipping data organization")
        return ""

    try:
        # Extract clean filename from document_id (remove patient_id prefix if present)
        clean_filename = document_id
        if patient_id and document_id.startswith(f"{patient_id}_"):
            clean_filename = document_id[len(f"{patient_id}_"):]
        
        # Create proper structure: processed/{patient_id}/{document_identifier}/
        # This matches the frontend pattern: {patient_id}/{filename}
        clean_patient_id = patient_id or 'unknown'
        processed_key_prefix = f"processed/{clean_patient_id}/{clean_filename}"

        logger.info(f"Organizing processed data with proper structure: {processed_key_prefix}")

        # Store the main extracted data as JSON
        main_data_key = f"{processed_key_prefix}/extracted_data.json"

        # Get original file metadata to replicate in processed files
        original_metadata = get_original_file_metadata(document_id, patient_id)
        
        # Prepare clean extracted data (remove BDA metadata for main file)
        clean_data = {k: v for k, v in extracted_data.items()
                      if k not in ['bda_job_metadata', 'source_s3_uri', 'result_files']}

        # Add metadata including classification
        clean_data['processing_metadata'] = {
            'document_id': document_id,
            'patient_id': patient_id,
            'processing_timestamp': get_current_iso8601(),
            'source_bda_uri': extracted_data.get('source_s3_uri'),
            'proper_structure': True
        }
        
        # Add classification metadata if available
        if classification:
            clean_data['classification'] = classification

        # Prepare S3 metadata for processed files (replicate from original + add processing info)
        s3_metadata = {
            **original_metadata,  # Copy original metadata
            'document-id': document_id,
            'processing-timestamp': get_current_iso8601(),
            'workflow-stage': 'processed',
            'extracted-data': 'true'
        }
        
        # Add classification to metadata if available
        if classification:
            s3_metadata.update({
                'document-category': classification.get('category', 'other'),
                'classification-confidence': str(classification.get('confidence', 0.0)),
                'auto-classified': str(classification.get('auto_classified', False))
            })

        # Upload main extracted data with replicated metadata
        s3_client.put_object(
            Bucket=PROCESSED_BUCKET,
            Key=main_data_key,
            Body=json.dumps(clean_data, indent=2, ensure_ascii=False),
            ContentType='application/json',
            Metadata=s3_metadata
        )
        logger.info(f"Stored main extracted data: {main_data_key}")

        # Store individual result files with clean naming
        result_files = extracted_data.get('result_files', {})
        for file_type, content in result_files.items():
            if not content:
                continue
                
            # Map BDA result types to clean filenames
            if file_type == 'custom_result':
                clean_filename_for_type = 'custom_output_result.json'
            elif file_type == 'standard_result':
                clean_filename_for_type = 'standard_output_result.json'
            elif file_type == 'html_result':
                clean_filename_for_type = 'result.html'
            elif file_type == 'markdown_result':
                clean_filename_for_type = 'result.md'
            elif file_type == 'text_result':
                clean_filename_for_type = 'result.txt'
            else:
                # Fallback for any other types
                clean_filename_for_type = f"{file_type}.json" if isinstance(content, dict) else f"{file_type}.txt"

            file_key = f"{processed_key_prefix}/{clean_filename_for_type}"

            if isinstance(content, dict):
                # JSON content with replicated metadata
                s3_client.put_object(
                    Bucket=PROCESSED_BUCKET,
                    Key=file_key,
                    Body=json.dumps(content, indent=2, ensure_ascii=False),
                    ContentType='application/json',
                    Metadata=s3_metadata
                )
            else:
                # Text content with replicated metadata
                content_type = 'text/plain'
                if clean_filename_for_type.endswith('.html'):
                    content_type = 'text/html'
                elif clean_filename_for_type.endswith('.md'):
                    content_type = 'text/markdown'

                s3_client.put_object(
                    Bucket=PROCESSED_BUCKET,
                    Key=file_key,
                    Body=content,
                    ContentType=content_type,
                    Metadata=s3_metadata
                )
            
            logger.info(f"Stored result file: {file_key}")

        # Move any assets from the BDA output (like images) to debloat original
        assets_moved = move_bda_assets(extracted_data.get('source_s3_uri', ''), processed_key_prefix)
        if assets_moved > 0:
            logger.info(f"Moved {assets_moved} asset files to flattened structure")

        # Store BDA metadata separately for debugging/audit purposes
        if extracted_data.get('bda_job_metadata'):
            metadata_key = f"{processed_key_prefix}/bda_metadata.json"
            s3_client.put_object(
                Bucket=PROCESSED_BUCKET,
                Key=metadata_key,
                Body=json.dumps(extracted_data['bda_job_metadata'], indent=2),
                ContentType='application/json',
                Metadata=s3_metadata
            )
            logger.info(f"Stored BDA metadata: {metadata_key}")

        # Clean up original BDA output to debloat (keep only essential files)
        cleanup_bda_output(extracted_data.get('source_s3_uri', ''))

        processed_uri = f"s3://{PROCESSED_BUCKET}/{main_data_key}"
        logger.info(f"Successfully organized processed data with proper structure at: {processed_uri}")
        return processed_uri

    except Exception as e:
        logger.error(f"Error organizing processed data: {str(e)}")
        return ""


def move_bda_assets(source_s3_uri: str, target_prefix: str) -> int:
    """
    Move asset files (like images) from the BDA output to the flattened structure.
    This helps debloat the original BDA output by moving files instead of copying.
    
    Args:
        source_s3_uri: Source S3 URI from BDA output
        target_prefix: Target prefix for flattened structure
        
    Returns:
        Number of assets moved
    """
    if not source_s3_uri or not PROCESSED_BUCKET:
        return 0
        
    try:
        # Parse source S3 URI
        parts = source_s3_uri.replace('s3://', '').split('/', 1)
        source_bucket = parts[0]
        source_prefix = parts[1] if len(parts) > 1 else ''
        
        # List all objects in the BDA output directory
        response = s3_client.list_objects_v2(
            Bucket=source_bucket,
            Prefix=source_prefix
        )
        
        assets_moved = 0
        if 'Contents' in response:
            for obj in response['Contents']:
                key = obj['Key']
                
                # Skip empty files, access check files, and result files we already processed
                if (obj['Size'] == 0 or 
                    '.s3_access_check' in key or 
                    key.endswith('/result.json') or 
                    key.endswith('/result.html') or 
                    key.endswith('/result.md') or 
                    key.endswith('/result.txt') or
                    key.endswith('job_metadata.json')):
                    continue
                
                # Look for asset files (images, etc.)
                if '/assets/' in key or key.endswith(('.png', '.jpg', '.jpeg', '.gif', '.pdf')):
                    # Extract filename from the asset path
                    filename = key.split('/')[-1]
                    
                    # Create target key in flattened structure
                    target_key = f"{target_prefix}/assets/{filename}"
                    
                    # Move the asset file (copy then delete to move)
                    s3_client.copy_object(
                        CopySource={'Bucket': source_bucket, 'Key': key},
                        Bucket=PROCESSED_BUCKET,
                        Key=target_key
                    )
                    
                    # Delete the original file to complete the move
                    s3_client.delete_object(
                        Bucket=source_bucket,
                        Key=key
                    )
                    
                    assets_moved += 1
                    logger.info(f"Moved asset: {key} -> {target_key}")
        
        return assets_moved
        
    except Exception as e:
        logger.error(f"Error moving BDA assets: {str(e)}")
        return 0


def cleanup_bda_output(source_s3_uri: str) -> None:
    """
    Clean up the original BDA output to debloat storage.
    Deletes ALL BDA output files since we've organized them in the processed bucket.
    
    Args:
        source_s3_uri: Source S3 URI from BDA output
    """
    if not source_s3_uri:
        return
        
    try:
        # Parse source S3 URI
        parts = source_s3_uri.replace('s3://', '').split('/', 1)
        source_bucket = parts[0]
        source_prefix = parts[1] if len(parts) > 1 else ''
        
        logger.info(f"Starting cleanup of BDA output at: {source_s3_uri}")
        
        # List all objects in the BDA output directory
        response = s3_client.list_objects_v2(
            Bucket=source_bucket,
            Prefix=source_prefix
        )
        
        files_deleted = 0
        files_to_delete = []
        
        if 'Contents' in response:
            for obj in response['Contents']:
                key = obj['Key']
                
                # Skip empty files and access check files (they're harmless)
                if obj['Size'] == 0 or '.s3_access_check' in key:
                    continue
                
                # Delete ALL BDA output files since we've organized them properly
                files_to_delete.append({'Key': key})
        
        # Batch delete for efficiency
        if files_to_delete:
            # S3 batch delete supports up to 1000 objects at a time
            batch_size = 1000
            for i in range(0, len(files_to_delete), batch_size):
                batch = files_to_delete[i:i + batch_size]
                
                delete_response = s3_client.delete_objects(
                    Bucket=source_bucket,
                    Delete={
                        'Objects': batch,
                        'Quiet': True  # Don't return info about successful deletions
                    }
                )
                
                # Count successful deletions
                deleted_count = len(batch)
                if 'Errors' in delete_response:
                    deleted_count -= len(delete_response['Errors'])
                    for error in delete_response['Errors']:
                        logger.warning(f"Failed to delete {error['Key']}: {error['Message']}")
                
                files_deleted += deleted_count
        
        if files_deleted > 0:
            logger.info(f"Successfully cleaned up {files_deleted} BDA output files to debloat storage")
        else:
            logger.info("No BDA output files found to clean up")
        
    except Exception as e:
        logger.error(f"Error cleaning up BDA output: {str(e)}")
        # Don't fail the process if cleanup fails


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
    metadata_fields = ['bda_job_metadata',
                       'extraction_timestamp', 'source_s3_uri', 'result_files']
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
    patient_id: Optional[str] = None,
    classification: Optional[Dict[str, Any]] = None
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

    # Create comprehensive metadata for knowledge base filtering and classification
    metadata = {
        # Document identification
        'documentId': document_id,
        'patientId': patient_id or 'unknown',
        
        # Classification metadata (primary filtering fields)
        'documentCategory': classification.get('category', 'other') if classification else 'other',
        'classificationConfidence': classification.get('confidence', 0.0) if classification else 0.0,
        'originalClassification': classification.get('original_classification', 'unknown') if classification else 'unknown',
        'autoClassified': classification.get('auto_classified', False) if classification else False,
        'confidenceThresholdMet': classification.get('confidence_threshold_met', False) if classification else False,
        
        # Processing metadata
        'extractionDate': extracted_data.get('extraction_timestamp'),
        'processingDate': get_current_iso8601(),
        'hasAnonymization': True,
        
        # Legacy document type (for backward compatibility)
        'documentType': extracted_data.get('document_type', 'unknown'),
        
        # Medical content metadata for filtering
        'hasDiagnoses': bool(extract_medical_field(extracted_data, ['diagnoses', 'diagnosticos', 'diagnosis'])),
        'hasSymptoms': bool(extract_medical_field(extracted_data, ['symptoms', 'sintomas', 'symptom'])),
        'hasMedications': bool(extract_medical_field(extracted_data, ['medications', 'medicamentos', 'medication'])),
        'hasVitalSigns': bool(extract_medical_field(extracted_data, ['blood_pressure', 'heart_rate', 'temperature', 'weight', 'height'])),
        
        # Source metadata
        'sourceS3Uri': extracted_data.get('source_s3_uri', ''),
        'bdaProcessed': True
    }

    kb_document = {
        'documentId': document_id,
        'patientId': patient_id,
        'content': json.dumps(clean_content, indent=2, ensure_ascii=False),
        'metadata': metadata
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
                        summary_parts.append(
                            f"{field.title()}: {', '.join(value)}")
                    else:
                        summary_parts.append(f"{field.title()}: {value}")

    kb_document['summary'] = ' | '.join(
        summary_parts) if summary_parts else 'Documento médico procesado'

    return kb_document


def extract_medical_field(extracted_data: Dict[str, Any], field_names: list) -> Optional[str]:
    """
    Extract medical field from extracted data or result files.
    
    Args:
        extracted_data: Validated extracted data
        field_names: List of possible field names to search for
        
    Returns:
        Field value if found
    """
    # Check main extracted data
    for field in field_names:
        if field in extracted_data and extracted_data[field]:
            return extracted_data[field]
    
    # Check in result files
    result_files = extracted_data.get('result_files', {})
    for result_data in result_files.values():
        if isinstance(result_data, dict):
            for field in field_names:
                if field in result_data and result_data[field]:
                    return result_data[field]
    
    return None


def get_original_file_metadata(document_id: str, patient_id: Optional[str]) -> Dict[str, str]:
    """
    Get metadata from the original file to replicate in processed files.
    
    Args:
        document_id: Document identifier
        patient_id: Patient identifier
        
    Returns:
        Dictionary of original file metadata
    """
    if not patient_id:
        return {}
    
    try:
        # Get the source bucket from environment
        source_bucket = os.environ.get('SOURCE_BUCKET_NAME', '')
        if not source_bucket:
            logger.warning("SOURCE_BUCKET_NAME not configured, cannot get original metadata")
            return {}
        
        # Extract clean filename from document_id
        clean_filename = document_id
        if document_id.startswith(f"{patient_id}_"):
            clean_filename = document_id[len(f"{patient_id}_"):]
        
        # Try to find the original document in S3
        # Structure: {patient_id}/{filename}
        possible_keys = [
            f"{patient_id}/{clean_filename}",
            f"{patient_id}/{clean_filename}.pdf",
            f"{patient_id}/{clean_filename}.jpg",
            f"{patient_id}/{clean_filename}.png",
            f"{patient_id}/{clean_filename}.tiff",
        ]
        
        for key in possible_keys:
            try:
                response = s3_client.head_object(Bucket=source_bucket, Key=key)
                metadata = response.get('Metadata', {})
                logger.info(f"Retrieved original metadata from: {key}")
                return metadata
            except ClientError:
                continue
        
        logger.warning(f"Could not find original document for {document_id}")
        return {}
        
    except Exception as e:
        logger.error(f"Error getting original file metadata: {str(e)}")
        return {}


def update_original_document_metadata(
    document_id: str,
    patient_id: Optional[str],
    classification: Optional[Dict[str, Any]] = None
) -> None:
    """
    Update the original document's S3 metadata with classification information.
    
    Args:
        document_id: Document identifier
        patient_id: Patient identifier
        classification: Classification information
    """
    if not patient_id or not classification:
        logger.warning("Cannot update document metadata without patient_id and classification")
        return
    
    try:
        # Get the source bucket from environment
        source_bucket = os.environ.get('SOURCE_BUCKET_NAME', '')
        if not source_bucket:
            logger.warning("SOURCE_BUCKET_NAME not configured, skipping metadata update")
            return
        
        # Extract clean filename from document_id
        clean_filename = document_id
        if document_id.startswith(f"{patient_id}_"):
            clean_filename = document_id[len(f"{patient_id}_"):]
        
        # Try to find the original document in S3
        # Structure: {patient_id}/{filename}
        possible_keys = [
            f"{patient_id}/{clean_filename}",
            f"{patient_id}/{clean_filename}.pdf",
            f"{patient_id}/{clean_filename}.jpg",
            f"{patient_id}/{clean_filename}.png",
            f"{patient_id}/{clean_filename}.tiff",
        ]
        
        original_key = None
        original_response = None
        for key in possible_keys:
            try:
                response = s3_client.head_object(Bucket=source_bucket, Key=key)
                original_key = key
                original_response = response
                break
            except ClientError:
                continue
        
        if not original_key or not original_response:
            logger.warning(f"Could not find original document for {document_id}")
            return
        
        # Get current object metadata
        current_metadata = original_response.get('Metadata', {})
        
        # Update metadata with classification (change document-category from 'auto' to actual category)
        updated_metadata = {
            **current_metadata,
            'document-category': classification.get('category', 'other'),
            'classification-confidence': str(classification.get('confidence', 0.0)),
            'original-classification': classification.get('original_classification', 'unknown'),
            'auto-classified': str(classification.get('auto_classified', False)),
            'confidence-threshold-met': str(classification.get('confidence_threshold_met', False)),
            'workflow-stage': 'classified',
            'classification-timestamp': get_current_iso8601()
        }
        
        # Copy object with updated metadata (S3 doesn't allow in-place metadata updates)
        s3_client.copy_object(
            CopySource={'Bucket': source_bucket, 'Key': original_key},
            Bucket=source_bucket,
            Key=original_key,
            Metadata=updated_metadata,
            MetadataDirective='REPLACE',
            ContentType=original_response.get('ContentType', 'application/octet-stream')
        )
        
        logger.info(f"Updated metadata for original document: {original_key}")
        logger.info(f"Classification: {classification.get('category')} ({classification.get('confidence')}% confidence)")
        logger.info(f"Changed document-category from '{current_metadata.get('document-category', 'auto')}' to '{classification.get('category')}'")
        
    except Exception as e:
        logger.error(f"Error updating original document metadata: {str(e)}")
        # Don't fail the entire process if metadata update fails


def update_knowledge_base(
    document_id: str,
    patient_id: Optional[str],
    extracted_data: Dict[str, Any],
    classification: Optional[Dict[str, Any]] = None
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
    # Get Knowledge Base configuration
    kb_config = get_knowledge_base_config()
    knowledge_base_id = kb_config.get('knowledge_base_id', '')
    data_source_id = kb_config.get('data_source_id', 'processed-documents')
    
    if not knowledge_base_id:
        logger.warning(
            "Knowledge Base ID not configured, skipping KB update")
        return document_id

    try:
        # Create knowledge base document with classification metadata
        kb_document = create_knowledge_base_document(
            extracted_data=extracted_data,
            document_id=document_id,
            patient_id=patient_id,
            classification=classification
        )

        # Ingest document into Knowledge Base
        logger.info(f"Starting ingestion job for KB: {knowledge_base_id}, Data Source: {data_source_id}")
        
        response = bedrock_agent_client.start_ingestion_job(
            knowledgeBaseId=knowledge_base_id,
            dataSourceId=data_source_id,
            description=f'Ingesting processed document: {document_id}'
        )

        ingestion_job_id = response.get(
            'ingestionJob', {}).get('ingestionJobId')
        logger.info(f"Started KB ingestion job: {ingestion_job_id}")

        return document_id

    except Exception as e:
        logger.error(f"Error updating Knowledge Base: {str(e)}")
        # Don't fail the entire process if KB update fails
        return document_id
