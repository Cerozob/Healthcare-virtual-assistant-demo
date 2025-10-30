"""
Simplified Lambda function for processing BDA results and organizing extracted data.
Focuses only on essential file organization and cleanup tasks.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
bedrock_agent_client = boto3.client('bedrock-agent')
ssm_client = boto3.client('ssm')

# Environment variables
PROCESSED_BUCKET = os.environ.get('PROCESSED_BUCKET_NAME', '')
SOURCE_BUCKET = os.environ.get('SOURCE_BUCKET_NAME', '')
CLASSIFICATION_CONFIDENCE_THRESHOLD = float(
    os.environ.get('CLASSIFICATION_CONFIDENCE_THRESHOLD', '80'))


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle BDA completion events and organize extracted data.

    Args:
        event: EventBridge event from BDA completion
        context: Lambda context

    Returns:
        Processing result
    """
    logger.info(
        f"Processing BDA completion event: {json.dumps(event, default=str)}")

    try:
        # Extract event details
        detail = event.get('detail', {})
        job_id = detail.get('job_id')
        status = detail.get('job_status')

        if status != 'SUCCESS':
            logger.error(f"BDA job failed: {job_id} with status: {status}")
            return {'statusCode': 500, 'body': json.dumps({'error': f'BDA job failed: {job_id}'})}

        # Get input and output S3 locations
        input_s3_object = detail.get('input_s3_object', {})
        output_s3_location = detail.get('output_s3_location', {})

        input_bucket = input_s3_object.get('s3_bucket', '')
        input_key = input_s3_object.get('name', '')
        output_bucket = output_s3_location.get('s3_bucket', '')
        output_key = output_s3_location.get('name', '')

        if not all([input_bucket, input_key, output_bucket, output_key]):
            logger.error("Missing required S3 location information")
            return {'statusCode': 400, 'body': json.dumps({'error': 'Missing S3 location information'})}

        # Extract patient ID and document ID from input key
        patient_id, document_id = extract_ids_from_input_key(input_key)
        if not patient_id:
            # Try to get patient ID from original file metadata
            patient_id = get_patient_id_from_metadata(input_bucket, input_key)

        if not patient_id:
            logger.error(
                f"Could not extract patient ID from input key: {input_key}")
            return {'statusCode': 400, 'body': json.dumps({'error': 'Could not extract patient ID'})}

        logger.info(
            f"Processing document {document_id} for patient {patient_id}")

        # Download and process BDA output
        bda_output_uri = f"s3://{output_bucket}/{output_key}"
        extracted_data = download_and_process_bda_output(bda_output_uri)

        # Extract classification from BDA results
        classification = extract_classification(extracted_data)

        # Organize processed data in correct structure
        organized_uri = organize_processed_data(
            patient_id, document_id, extracted_data, classification)

        # Update original file metadata with classification
        update_original_file_metadata(input_bucket, input_key, classification)

        # Clean up BDA output completely
        cleanup_bda_output(bda_output_uri)

        # Start Knowledge Base ingestion to sync the new processed data
        ingestion_job_id = start_knowledge_base_ingestion()

        logger.info(
            f"Successfully processed document {document_id} for patient {patient_id}")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'documentId': document_id,
                'patientId': patient_id,
                'organizedUri': organized_uri,
                'classification': classification,
                'ingestionJobId': ingestion_job_id,
                'status': 'completed'
            })
        }

    except Exception as e:
        logger.error(
            f"Error processing BDA completion: {str(e)}", exc_info=True)
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}


def extract_ids_from_input_key(input_key: str) -> tuple[Optional[str], str]:
    """Extract patient ID and document ID from input S3 key."""
    try:
        # Input structure: {patient_id}/{filename}
        key_parts = input_key.split('/')
        if len(key_parts) >= 2:
            patient_id = key_parts[0]
            filename = key_parts[-1]
            # Remove extension for document ID
            document_id = filename.rsplit(
                '.', 1)[0] if '.' in filename else filename
            return patient_id, document_id
        elif len(key_parts) == 1:
            # Single filename without patient prefix
            filename = key_parts[0]
            document_id = filename.rsplit(
                '.', 1)[0] if '.' in filename else filename
            return None, document_id
    except Exception as e:
        logger.warning(f"Error extracting IDs from input key {input_key}: {e}")

    return None, input_key.replace('/', '_')


def get_patient_id_from_metadata(bucket: str, key: str) -> Optional[str]:
    """Get patient ID from original file metadata."""
    try:
        response = s3_client.head_object(Bucket=bucket, Key=key)
        metadata = response.get('Metadata', {})
        return metadata.get('patient-id') or metadata.get('patient_id')
    except Exception as e:
        logger.warning(f"Could not get metadata from {bucket}/{key}: {e}")
        return None


def download_and_process_bda_output(bda_output_uri: str) -> Dict[str, Any]:
    """Download and process BDA output files."""
    try:
        # Parse S3 URI
        parts = bda_output_uri.replace('s3://', '').split('/', 1)
        bucket = parts[0]
        prefix = parts[1] if len(parts) > 1 else ''

        # List all objects in the BDA output directory
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)

        if 'Contents' not in response:
            logger.warning(f"No BDA output files found at {bda_output_uri}")
            return {}

        result_data = {}
        job_metadata = None

        for obj in response['Contents']:
            key = obj['Key']
            if obj['Size'] == 0 or '.s3_access_check' in key:
                continue

            try:
                # Get the file content
                file_response = s3_client.get_object(Bucket=bucket, Key=key)
                content = file_response['Body'].read().decode('utf-8')

                # Process different file types
                if key.endswith('job_metadata.json'):
                    job_metadata = json.loads(content)
                elif key.endswith('/result.json'):
                    if '/custom_output/' in key:
                        result_data['custom_result'] = json.loads(content)
                    elif '/standard_output/' in key:
                        result_data['standard_result'] = json.loads(content)
                elif key.endswith('.html'):
                    result_data['html_result'] = content
                elif key.endswith('.md'):
                    result_data['markdown_result'] = content
                elif key.endswith('.txt'):
                    result_data['text_result'] = content

            except Exception as e:
                logger.warning(f"Error processing file {key}: {e}")

        return {
            'job_metadata': job_metadata,
            'result_files': result_data,
            'source_uri': bda_output_uri,
            'processing_timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    except Exception as e:
        logger.error(f"Error downloading BDA output: {e}")
        return {}


def extract_classification(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract classification information from BDA results."""
    try:
        result_files = extracted_data.get('result_files', {})
        custom_result = result_files.get('custom_result', {})

        # Extract classification from custom result
        document_type = None
        confidence = 0.0

        if custom_result:
            # Check inference_result for document_type
            inference_result = custom_result.get('inference_result', {})
            if 'document_type' in inference_result:
                document_type = inference_result['document_type']

            # Check for confidence
            matched_blueprint = custom_result.get('matched_blueprint', {})
            if 'confidence' in matched_blueprint:
                # Convert to percentage
                confidence = float(matched_blueprint['confidence']) * 100

        # Map to valid categories
        valid_categories = ['medical-history', 'exam-results',
                            'medical-images', 'identification', 'other']
        if document_type and document_type not in valid_categories:
            document_type_lower = document_type.lower()
            if 'exam' in document_type_lower or 'result' in document_type_lower:
                document_type = 'exam-results'
            elif 'history' in document_type_lower or 'historia' in document_type_lower:
                document_type = 'medical-history'
            elif 'image' in document_type_lower or 'radio' in document_type_lower:
                document_type = 'medical-images'
            elif 'id' in document_type_lower or 'cedula' in document_type_lower:
                document_type = 'identification'
            else:
                document_type = 'other'

        # Apply confidence threshold
        final_category = document_type if confidence >= CLASSIFICATION_CONFIDENCE_THRESHOLD else 'not-identified'

        return {
            'category': final_category or 'other',
            'confidence': confidence,
            'original_classification': document_type,
            'auto_classified': True,
            'confidence_threshold_met': confidence >= CLASSIFICATION_CONFIDENCE_THRESHOLD
        }

    except Exception as e:
        logger.error(f"Error extracting classification: {e}")
        return {
            'category': 'not-identified',
            'confidence': 0.0,
            'auto_classified': False,
            'confidence_threshold_met': False
        }


def organize_processed_data(patient_id: str, document_id: str, extracted_data: Dict[str, Any], classification: Dict[str, Any]) -> str:
    """Organize processed data in the correct bucket structure."""
    if not PROCESSED_BUCKET:
        logger.warning("PROCESSED_BUCKET not configured")
        return ""

    try:
        # Create structure: {patient_id}/{document_id}/
        key_prefix = f"{patient_id}/{document_id}"

        # Prepare metadata
        metadata = {
            'patient-id': patient_id,
            'document-id': document_id,
            'document-category': classification.get('category', 'other'),
            'classification-confidence': str(classification.get('confidence', 0.0)),
            'auto-classified': str(classification.get('auto_classified', False)),
            'workflow-stage': 'processed',
            'processing-timestamp': extracted_data.get('processing_timestamp', datetime.utcnow().isoformat() + 'Z')
        }

        # Store main extracted data
        main_key = f"{key_prefix}/extracted_data.json"
        clean_data = {k: v for k, v in extracted_data.items()
                      if k != 'source_uri'}
        clean_data['classification'] = classification

        s3_client.put_object(
            Bucket=PROCESSED_BUCKET,
            Key=main_key,
            Body=json.dumps(clean_data, indent=2, ensure_ascii=False),
            ContentType='application/json',
            Metadata=metadata
        )

        # Store individual result files
        result_files = extracted_data.get('result_files', {})
        for file_type, content in result_files.items():
            if not content:
                continue

            file_key = f"{key_prefix}/{file_type}.json" if isinstance(
                content, dict) else f"{key_prefix}/{file_type}.txt"
            content_type = 'application/json' if isinstance(
                content, dict) else 'text/plain'
            body = json.dumps(content, indent=2, ensure_ascii=False) if isinstance(
                content, dict) else content

            s3_client.put_object(
                Bucket=PROCESSED_BUCKET,
                Key=file_key,
                Body=body,
                ContentType=content_type,
                Metadata=metadata
            )

        # Store job metadata if available
        if extracted_data.get('job_metadata'):
            metadata_key = f"{key_prefix}/job_metadata.json"
            s3_client.put_object(
                Bucket=PROCESSED_BUCKET,
                Key=metadata_key,
                Body=json.dumps(extracted_data['job_metadata'], indent=2),
                ContentType='application/json',
                Metadata=metadata
            )

        logger.info(f"Organized processed data at: {key_prefix}")
        return f"s3://{PROCESSED_BUCKET}/{main_key}"

    except Exception as e:
        logger.error(f"Error organizing processed data: {e}")
        return ""


def update_original_file_metadata(bucket: str, key: str, classification: Dict[str, Any]) -> None:
    """Update original file metadata with classification results."""
    try:
        # Get current object metadata
        response = s3_client.head_object(Bucket=bucket, Key=key)
        current_metadata = response.get('Metadata', {})

        # Update metadata with classification
        updated_metadata = {
            **current_metadata,
            'document-category': classification.get('category', 'other'),
            'classification-confidence': str(classification.get('confidence', 0.0)),
            'auto-classified': str(classification.get('auto_classified', False)),
            'workflow-stage': 'classified',
            'classification-timestamp': datetime.utcnow().isoformat() + 'Z'
        }

        # Copy object with updated metadata
        s3_client.copy_object(
            CopySource={'Bucket': bucket, 'Key': key},
            Bucket=bucket,
            Key=key,
            Metadata=updated_metadata,
            MetadataDirective='REPLACE',
            ContentType=response.get('ContentType', 'application/octet-stream')
        )

        logger.info(f"Updated metadata for original file: {key}")

    except Exception as e:
        logger.error(f"Error updating original file metadata: {e}")


def cleanup_bda_output(bda_output_uri: str) -> None:
    """Completely clean up BDA output directory."""
    try:
        # Parse S3 URI
        parts = bda_output_uri.replace('s3://', '').split('/', 1)
        bucket = parts[0]
        prefix = parts[1] if len(parts) > 1 else ''

        # Get the job folder prefix (everything up to the job ID)
        prefix_parts = prefix.split('/')
        if len(prefix_parts) >= 4 and prefix_parts[0] == 'processed':
            # Delete entire job folder: processed/{patient_id}/{document_id}/{job_id}/
            job_folder_prefix = '/'.join(prefix_parts[:4]) + '/'
        else:
            job_folder_prefix = prefix + \
                '/' if not prefix.endswith('/') else prefix

        logger.info(f"Cleaning up BDA output at: {job_folder_prefix}")

        # List and delete all objects
        paginator = s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(
            Bucket=bucket, Prefix=job_folder_prefix)

        objects_to_delete = []
        for page in page_iterator:
            if 'Contents' in page:
                for obj in page['Contents']:
                    if obj['Size'] > 0 and '.s3_access_check' not in obj['Key']:
                        objects_to_delete.append({'Key': obj['Key']})

        # Delete in batches
        if objects_to_delete:
            for i in range(0, len(objects_to_delete), 1000):
                batch = objects_to_delete[i:i + 1000]
                s3_client.delete_objects(
                    Bucket=bucket,
                    Delete={'Objects': batch, 'Quiet': True}
                )

            logger.info(
                f"Cleaned up {len(objects_to_delete)} BDA output files")

    except Exception as e:
        logger.error(f"Error cleaning up BDA output: {e}")


def get_knowledge_base_config() -> Dict[str, Optional[str]]:
    """Get Knowledge Base configuration from SSM parameters."""
    try:
        response = ssm_client.get_parameters(
            Names=[
                '/healthcare/knowledge-base/id',
                '/healthcare/knowledge-base/data-source-id'
            ]
        )

        params = {param['Name'].split('/')[-1]: param['Value']
                  for param in response['Parameters']}

        return {
            'knowledge_base_id': params.get('id'),
            'data_source_id': params.get('data-source-id')
        }

    except Exception as e:
        logger.error(f"Failed to get Knowledge Base configuration: {e}")
        return {'knowledge_base_id': None, 'data_source_id': None}


def check_running_ingestion_jobs(knowledge_base_id: str, data_source_id: str) -> Optional[str]:
    """Check if there are any running ingestion jobs for the data source."""
    try:
        response = bedrock_agent_client.list_ingestion_jobs(
            knowledgeBaseId=knowledge_base_id,
            dataSourceId=data_source_id,
            filters=[
                {
                    'attribute': 'STATUS',
                    'operator': 'EQ',
                    'values': ['STARTING', 'IN_PROGRESS']
                }
            ],
            maxResults=10
        )

        ingestion_jobs = response.get('ingestionJobSummaries', [])

        if ingestion_jobs:
            running_job = ingestion_jobs[0]  # Get the first running job
            job_id = running_job.get('ingestionJobId')
            status = running_job.get('status')
            logger.info(
                f"Found running ingestion job: {job_id} with status: {status}")
            return job_id

        return None

    except Exception as e:
        logger.error(f"Error checking running ingestion jobs: {e}")
        return None


def start_knowledge_base_ingestion() -> Optional[str]:
    """Start Knowledge Base ingestion job if none is currently running."""
    try:
        # Get Knowledge Base configuration
        config = get_knowledge_base_config()
        knowledge_base_id = config.get('knowledge_base_id')
        data_source_id = config.get('data_source_id')

        if not knowledge_base_id or not data_source_id:
            logger.warning(
                "Knowledge Base configuration not available, skipping ingestion")
            return None

        logger.info(
            f"Starting Knowledge Base ingestion for KB: {knowledge_base_id}, Data Source: {data_source_id}")

        # Check if there's already a running ingestion job
        running_job_id = check_running_ingestion_jobs(
            knowledge_base_id, data_source_id)

        if running_job_id:
            logger.info(
                f"Ingestion job already running: {running_job_id}, skipping new job")
            return running_job_id

        # Start new ingestion job
        response = bedrock_agent_client.start_ingestion_job(
            knowledgeBaseId=knowledge_base_id,
            dataSourceId=data_source_id,
            description='Ingesting processed healthcare documents after BDA completion'
        )

        ingestion_job = response.get('ingestionJob', {})
        job_id = ingestion_job.get('ingestionJobId')
        status = ingestion_job.get('status')

        logger.info(
            f"Started Knowledge Base ingestion job: {job_id} with status: {status}")
        return job_id

    except Exception as e:
        logger.error(f"Error starting Knowledge Base ingestion: {e}")
        return None
