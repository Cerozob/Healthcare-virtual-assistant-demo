"""
Simplified BDA Trigger Lambda.
Directly invokes Bedrock Data Automation when documents are uploaded to S3.
Includes deduplication logic to prevent duplicate processing.
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

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    BDA trigger with deduplication logic to prevent duplicate processing
    """
    try:
        # Extract S3 details from event
        bucket, key = extract_s3_details(event)
        
        logger.info(f"Processing S3 event for {bucket}/{key}")
        
        # Filter out files that shouldn't trigger BDA processing
        if should_skip_file(key):
            logger.info(f"Skipping file {key} - not suitable for BDA processing")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'status': 'skipped',
                    'reason': 'file_filtered'
                })
            }
        
        # Check if file has already been processed or is currently being processed
        # This also handles metadata-only updates since they would have processing metadata
        processing_status = check_processing_status(bucket, key)
        
        if processing_status == 'already_processed':
            logger.info(f"File {key} already processed successfully, skipping")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'status': 'skipped',
                    'reason': 'already_processed'
                })
            }
        elif processing_status == 'currently_processing':
            logger.info(f"File {key} is currently being processed, skipping duplicate")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'status': 'skipped',
                    'reason': 'currently_processing'
                })
            }
        
        # Mark file as being processed (with race condition protection)
        if not mark_file_processing(bucket, key):
            logger.info(f"File {key} is being processed by another instance, skipping")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'status': 'skipped',
                    'reason': 'race_condition_detected'
                })
            }
        
        # Call BDA API directly
        invocation_arn = invoke_bda_processing(bucket, key)
        
        logger.info(f"Successfully submitted BDA job for {key}: {invocation_arn}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'invocationArn': invocation_arn,
                'status': 'submitted'
            })
        }
    except Exception as e:
        logger.error(f"BDA trigger failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def should_skip_file(key: str) -> bool:
    """
    Determine if a file should be skipped for BDA processing
    """
    # Skip system files and temporary files
    if any(skip_pattern in key for skip_pattern in [
        '.DS_Store', 
        'Thumbs.db', 
        '.tmp', 
        '.temp',
        '/.aws/',
        '/.s3/',
        '$folder$'  # S3 folder markers
    ]):
        return True
    
    # Skip files without extensions (likely folders or system files)
    if '.' not in key.split('/')[-1]:
        return True
    
    # Get file extension
    file_extension = '.' + key.split('.')[-1].lower() if '.' in key else ''
    
    # Only process files that BDA can handle
    supported_extensions = {
        # Documents
        '.pdf', '.doc', '.docx', '.txt', '.rtf',
        # Images  
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif',
        # Audio
        '.mp3', '.wav', '.flac', '.aac', '.ogg',
        # Video
        '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'
    }
    
    if file_extension not in supported_extensions:
        return True
    
    return False


def extract_s3_details(event: Dict[str, Any]) -> tuple[str, str]:
    """
    Extract bucket and key from S3 event (supports both direct S3 and EventBridge)
    """
    # Handle EventBridge S3 events
    if event.get('source') == 'aws.s3':
        detail = event['detail']
        bucket = detail['bucket']['name']
        key = detail['object']['key']
        return bucket, key
    
    # Handle direct S3 notifications
    record = event['Records'][0]
    bucket = record['s3']['bucket']['name']
    key = record['s3']['object']['key']
    return bucket, key

def check_processing_status(bucket: str, key: str) -> str:
    """
    Check if file has already been processed or is currently being processed
    Returns: 'not_processed', 'currently_processing', or 'already_processed'
    """
    try:
        # Check file metadata for processing status
        response = s3_client.head_object(Bucket=bucket, Key=key)
        metadata = response.get('Metadata', {})
        
        workflow_stage = metadata.get('workflow-stage', '')
        
        # Check if already successfully processed
        if workflow_stage in ['processed', 'classified']:
            logger.info(f"File {key} already processed (stage: {workflow_stage})")
            return 'already_processed'
        
        # Check if currently being processed
        if workflow_stage == 'processing':
            # Check if processing started recently (within last 10 minutes for faster recovery)
            processing_timestamp = metadata.get('processing-timestamp', '')
            if processing_timestamp:
                from datetime import datetime, timezone
                try:
                    processing_time = datetime.fromisoformat(processing_timestamp.replace('Z', '+00:00'))
                    current_time = datetime.now(timezone.utc)
                    time_diff = (current_time - processing_time).total_seconds()
                    
                    # Reduced timeout to 10 minutes for faster recovery from stuck states
                    if time_diff > 600:  # 10 minutes
                        logger.warning(f"File {key} has been processing for {time_diff/60:.1f} minutes, allowing reprocessing")
                        return 'not_processed'
                    else:
                        logger.info(f"File {key} is currently being processed (started {time_diff:.0f}s ago)")
                        return 'currently_processing'
                except Exception as e:
                    logger.warning(f"Error parsing processing timestamp for {key}: {e}")
                    return 'not_processed'
            else:
                logger.info(f"File {key} marked as processing but no timestamp, allowing reprocessing")
                return 'not_processed'
        
        logger.info(f"File {key} not processed yet (stage: {workflow_stage or 'none'})")
        return 'not_processed'
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.warning(f"File {key} not found in bucket {bucket}")
            return 'not_processed'
        else:
            logger.error(f"Error checking processing status for {key}: {e}")
            return 'not_processed'
    except Exception as e:
        logger.error(f"Unexpected error checking processing status for {key}: {e}")
        return 'not_processed'


def mark_file_processing(bucket: str, key: str) -> bool:
    """
    Mark file as currently being processed by updating its metadata
    Returns True if successfully marked, False if already being processed by another instance
    """
    try:
        from datetime import datetime
        import uuid
        
        # Generate unique processing ID for this instance
        processing_id = str(uuid.uuid4())[:8]
        current_timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Get current metadata
        try:
            response = s3_client.head_object(Bucket=bucket, Key=key)
            current_metadata = response.get('Metadata', {})
            content_type = response.get('ContentType', 'application/octet-stream')
            
            # Check if another instance is already processing (race condition check)
            existing_stage = current_metadata.get('workflow-stage', '')
            if existing_stage == 'processing':
                existing_timestamp = current_metadata.get('processing-timestamp', '')
                if existing_timestamp:
                    try:
                        processing_time = datetime.fromisoformat(existing_timestamp.replace('Z', '+00:00'))
                        current_time = datetime.now(datetime.timezone.utc)
                        time_diff = (current_time - processing_time).total_seconds()
                        
                        # If processing started less than 2 minutes ago, don't override
                        if time_diff < 120:  # 2 minutes
                            logger.warning(f"File {key} is being processed by another instance (started {time_diff:.0f}s ago)")
                            return False
                    except Exception:
                        pass  # If we can't parse timestamp, proceed with marking
                        
        except ClientError:
            current_metadata = {}
            content_type = 'application/octet-stream'
        
        # Update metadata with processing status and unique ID
        updated_metadata = {
            **current_metadata,
            'workflow-stage': 'processing',
            'processing-timestamp': current_timestamp,
            'processing-id': processing_id,
            'lambda-request-id': os.environ.get('AWS_REQUEST_ID', 'unknown')
        }
        
        # Copy object with updated metadata
        s3_client.copy_object(
            CopySource={'Bucket': bucket, 'Key': key},
            Bucket=bucket,
            Key=key,
            Metadata=updated_metadata,
            MetadataDirective='REPLACE',
            ContentType=content_type
        )
        
        logger.info(f"Marked file {key} as processing (ID: {processing_id})")
        return True
        
    except Exception as e:
        logger.error(f"Error marking file {key} as processing: {e}")
        # Don't fail the entire process if metadata update fails
        return True  # Proceed anyway to avoid blocking


def invoke_bda_processing(bucket: str, key: str) -> str:
    """
    Directly invoke BDA with multiple blueprints
    """
    client = boto3.client('bedrock-data-automation-runtime')
    
    response = client.invoke_data_automation_async(
        inputConfiguration={
            's3Uri': f's3://{bucket}/{key}'
        },
        outputConfiguration={
            's3Uri': f's3://{os.environ["PROCESSED_BUCKET_NAME"]}/processed/{key}'
        },
        dataAutomationConfiguration={
            'dataAutomationProjectArn': os.environ['BDA_PROJECT_ARN'],
            'stage': 'LIVE'
        },
        dataAutomationProfileArn=os.environ['BDA_PROFILE_ARN'],
        notificationConfiguration={
            'eventBridgeConfiguration': {
                'eventBridgeEnabled': True
            }
        }
    )
    
    return response['invocationArn']


