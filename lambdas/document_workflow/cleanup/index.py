"""
Lambda function for cleaning up lingering files when S3 objects are deleted.
Handles cleanup of related files between raw and processed buckets only.
"""

import json
import logging
import os
from typing import Any, Dict
import boto3
from shared.datetime_utils import get_current_iso8601

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')

# Environment variables
RAW_BUCKET = os.environ.get('RAW_BUCKET_NAME', '')
PROCESSED_BUCKET = os.environ.get('PROCESSED_BUCKET_NAME', '')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle S3 object deletion events and clean up related files between buckets.

    Args:
        event: EventBridge event from S3 object deletion
        context: Lambda context

    Returns:
        Cleanup result
    """
    logger.info(f"Received S3 deletion event: {json.dumps(event)}")

    try:
        # Extract event details
        detail = event.get('detail', {})
        
        # Get S3 object information
        bucket_name = detail.get('bucket', {}).get('name', '')
        object_key = detail.get('object', {}).get('key', '')
        
        if not bucket_name or not object_key:
            logger.error("Missing bucket name or object key in event")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing bucket name or object key in event'
                })
            }

        logger.info(f"Processing deletion of {object_key} from bucket {bucket_name}")

        # Determine cleanup actions based on which bucket the deletion occurred in
        if bucket_name == RAW_BUCKET:
            cleanup_result = handle_raw_bucket_deletion(object_key)
        elif bucket_name == PROCESSED_BUCKET:
            cleanup_result = handle_processed_bucket_deletion(object_key)
        else:
            logger.warning(f"Deletion event from unknown bucket: {bucket_name}")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'No cleanup needed for bucket {bucket_name}',
                    'status': 'ignored'
                })
            }

        logger.info(f"File cleanup completed for {object_key}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'objectKey': object_key,
                'bucketName': bucket_name,
                'cleanupResult': cleanup_result,
                'status': 'completed',
                'timestamp': get_current_iso8601()
            })
        }

    except Exception as e:
        logger.error(f"Error in file cleanup processing: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': get_current_iso8601()
            })
        }


def handle_raw_bucket_deletion(object_key: str) -> Dict[str, Any]:
    """
    Handle cleanup when a file is deleted from the raw bucket.
    Only cleans up related processed files.
    
    Args:
        object_key: S3 object key that was deleted
        
    Returns:
        Cleanup result summary
    """
    cleanup_actions = []
    
    try:
        # Extract document identifier from the object key
        document_id = extract_document_id_from_key(object_key)
        
        # Clean up any processed data in the processed bucket
        processed_objects_deleted = cleanup_processed_data(document_id, object_key)
        if processed_objects_deleted:
            cleanup_actions.append(f"Deleted {processed_objects_deleted} processed files")
        else:
            cleanup_actions.append("No processed files found to delete")
        
        return {
            'document_id': document_id,
            'source_bucket': 'raw',
            'actions_taken': cleanup_actions,
            'total_actions': len(cleanup_actions)
        }
        
    except Exception as e:
        logger.error(f"Error handling raw bucket deletion: {str(e)}")
        return {
            'error': str(e),
            'source_bucket': 'raw',
            'actions_taken': cleanup_actions
        }


def handle_processed_bucket_deletion(object_key: str) -> Dict[str, Any]:
    """
    Handle cleanup when a file is deleted from the processed bucket.
    Only monitors and logs - no cross-bucket cleanup needed.
    
    Args:
        object_key: S3 object key that was deleted
        
    Returns:
        Cleanup result summary
    """
    cleanup_actions = []
    
    try:
        # Extract document identifier from the processed object key
        document_id = extract_document_id_from_processed_key(object_key)
        
        # For processed bucket deletions, we mainly monitor
        # The raw file should remain unless explicitly deleted
        cleanup_actions.append(f"Monitored deletion of processed file: {object_key}")
        
        # Optionally check if this was a complete document folder deletion
        if is_document_folder_deletion(object_key):
            cleanup_actions.append("Complete document folder deleted")
        
        return {
            'document_id': document_id,
            'source_bucket': 'processed',
            'actions_taken': cleanup_actions,
            'total_actions': len(cleanup_actions)
        }
        
    except Exception as e:
        logger.error(f"Error handling processed bucket deletion: {str(e)}")
        return {
            'error': str(e),
            'source_bucket': 'processed',
            'actions_taken': cleanup_actions
        }


def extract_document_id_from_key(object_key: str) -> str:
    """
    Extract document ID from raw bucket object key.
    
    Args:
        object_key: S3 object key
        
    Returns:
        Document ID
    """
    # Raw bucket structure: {patient_id}/{filename}
    # or could be just {filename}
    try:
        parts = object_key.split('/')
        if len(parts) >= 2:
            patient_id = parts[0]
            filename = parts[-1]
            # Remove file extension
            clean_filename = filename.split('.')[0]
            return f"{patient_id}_{clean_filename}"
        else:
            # Just filename
            filename = parts[0]
            clean_filename = filename.split('.')[0]
            return f"unknown_{clean_filename}"
    except Exception as e:
        logger.warning(f"Could not extract document ID from key {object_key}: {e}")
        return f"unknown_{object_key.replace('/', '_').split('.')[0]}"


def extract_document_id_from_processed_key(object_key: str) -> str:
    """
    Extract document ID from processed bucket object key.
    
    Args:
        object_key: S3 object key from processed bucket
        
    Returns:
        Document ID
    """
    # Processed bucket structure: processed/{patient_id}/{document_id}/...
    try:
        parts = object_key.split('/')
        if len(parts) >= 3 and parts[0] == 'processed':
            return parts[2]  # document_id
        else:
            # Fallback extraction
            return extract_document_id_from_key(object_key)
    except Exception as e:
        logger.warning(f"Could not extract document ID from processed key {object_key}: {e}")
        return f"unknown_{object_key.replace('/', '_').split('.')[0]}"


def cleanup_processed_data(document_id: str, original_key: str) -> int:
    """
    Clean up processed data files related to a deleted raw file.
    
    Args:
        document_id: Document identifier
        original_key: Original raw file key
        
    Returns:
        Number of processed objects deleted
    """
    if not PROCESSED_BUCKET:
        return 0
    
    try:
        # List all processed files for this document
        # Structure: processed/{patient_id}/{document_id}/...
        patient_id = original_key.split('/')[0] if '/' in original_key else 'unknown'
        prefix = f"processed/{patient_id}/{document_id}/"
        
        response = s3_client.list_objects_v2(
            Bucket=PROCESSED_BUCKET,
            Prefix=prefix
        )
        
        objects_to_delete = []
        if 'Contents' in response:
            for obj in response['Contents']:
                objects_to_delete.append({'Key': obj['Key']})
        
        if objects_to_delete:
            # Delete in batches of 1000 (S3 limit)
            deleted_count = 0
            for i in range(0, len(objects_to_delete), 1000):
                batch = objects_to_delete[i:i+1000]
                s3_client.delete_objects(
                    Bucket=PROCESSED_BUCKET,
                    Delete={'Objects': batch}
                )
                deleted_count += len(batch)
            
            logger.info(f"Deleted {deleted_count} processed objects for document {document_id}")
            return deleted_count
        
        return 0
        
    except Exception as e:
        logger.error(f"Error cleaning up processed data: {str(e)}")
        return 0


def is_document_folder_deletion(object_key: str) -> bool:
    """
    Check if the deleted object indicates a complete document folder deletion.
    
    Args:
        object_key: S3 object key
        
    Returns:
        True if this appears to be a document folder deletion
    """
    # Check if this is a main extracted data file (indicates folder cleanup)
    return object_key.endswith('/extracted_data.json')



