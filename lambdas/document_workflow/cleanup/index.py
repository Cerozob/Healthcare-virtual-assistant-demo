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

        logger.info(
            f"Processing deletion of {object_key} from bucket {bucket_name}")

        # Determine cleanup actions based on which bucket the deletion occurred in
        if bucket_name == RAW_BUCKET:
            cleanup_result = handle_raw_bucket_deletion(
                object_key, bucket_name)
        elif bucket_name == PROCESSED_BUCKET:
            cleanup_result = handle_processed_bucket_deletion(
                object_key, bucket_name)
        else:
            logger.warning(
                f"Deletion event from unknown bucket: {bucket_name}")
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
        logger.error(
            f"Error in file cleanup processing: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': get_current_iso8601()
            })
        }


def handle_raw_bucket_deletion(object_key: str, bucket_name: str) -> Dict[str, Any]:
    """
    Handle cleanup when a file is deleted from the raw bucket.
    Only cleans up related processed files.

    Args:
        object_key: S3 object key that was deleted
        bucket_name: Name of the bucket where deletion occurred

    Returns:
        Cleanup result summary
    """
    cleanup_actions = []

    try:
        # Extract document identifier from the object key
        document_id = extract_document_id_from_key(object_key)

        # Clean up any processed data in the processed bucket
        processed_objects_deleted = cleanup_processed_data(
            document_id, object_key, bucket_name)
        if processed_objects_deleted:
            cleanup_actions.append(
                f"Deleted {processed_objects_deleted} processed files")
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


def handle_processed_bucket_deletion(object_key: str, bucket_name: str) -> Dict[str, Any]:
    """
    Handle cleanup when a file is deleted from the processed bucket.
    Cleans up corresponding raw files when processed files are deleted.

    Args:
        object_key: S3 object key that was deleted
        bucket_name: Name of the bucket where deletion occurred

    Returns:
        Cleanup result summary
    """
    cleanup_actions = []

    try:
        # Log the deletion with detailed information matching the expected format
        logger.info(
            f"Processing deletion of {object_key} from bucket {bucket_name}")

        # Extract document identifier from the processed object key
        document_id = extract_document_id_from_processed_key(object_key)

        # Clean up corresponding raw files when processed files are deleted
        raw_objects_deleted = cleanup_raw_data(document_id, object_key, bucket_name)
        if raw_objects_deleted:
            cleanup_actions.append(
                f"Deleted {raw_objects_deleted} raw files")
        else:
            cleanup_actions.append("No raw files found to delete")

        # Optionally check if this was a complete document folder deletion
        if is_document_folder_deletion(object_key):
            cleanup_actions.append("Complete document folder deleted")

        # Log completion for this specific file
        logger.info(f"File cleanup completed for {object_key}")

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
    # Raw bucket structure examples:
    # {patient_id}/{category}/{timestamp}/{file_id}/{filename}
    # or could be just {filename}
    try:
        parts = object_key.split('/')

        # Handle new structure: {patient_id}/{category}/{timestamp}/{file_id}/{filename}
        if len(parts) >= 2:
            patient_id = parts[0]
            filename = parts[-1]
            clean_filename = filename.split('.')[0]
            document_id = f"{patient_id}_{clean_filename}"
            logger.info(
                f"Extracted from raw key - Patient: {patient_id}, Filename: {filename}, Document ID: {document_id}")
            return document_id

        # Handle structure: {patient_id}/{filename}
        elif len(parts) >= 2:
            patient_id = parts[0]
            filename = parts[-1]
            clean_filename = filename.split('.')[0]
            document_id = f"{patient_id}_{clean_filename}"
            logger.info(
                f"Extracted from raw key - Patient: {patient_id}, Filename: {filename}, Document ID: {document_id}")
            return document_id

        else:
            # Just filename
            filename = parts[0]
            clean_filename = filename.split('.')[0]
            document_id = f"unknown_{clean_filename}"
            logger.info(
                f"Extracted from raw key - Single file: {filename}, Document ID: {document_id}")
            return document_id

    except Exception as e:
        logger.warning(
            f"Could not extract document ID from key {object_key}: {e}")
        return f"unknown_{object_key.replace('/', '_').split('.')[0]}"


def extract_document_id_from_processed_key(object_key: str) -> str:
    """
    Extract document ID from processed bucket object key.

    Args:
        object_key: S3 object key from processed bucket

    Returns:
        Document ID
    """
    # Flattened processed bucket structure: processed/{patient_id}/{clean_filename}/file.json
    # Example: processed/1d621da0-f89e-4691-8f56-5022bb20dcca/historia_clinica_20251022_000124/extracted_data.json
    try:
        parts = object_key.split('/')

        # Handle flattened structure: processed/{patient_id}/{clean_filename}/...
        if len(parts) >= 3 and parts[0] == 'processed':
            patient_id = parts[1]
            clean_filename = parts[2]
            
            # Create document ID from patient and clean filename
            document_id = f"{patient_id}_{clean_filename}"
            
            logger.info(
                f"Extracted from flattened processed key - Patient: {patient_id}, Clean filename: {clean_filename}, Document ID: {document_id}")
            return document_id

        else:
            # Fallback extraction
            logger.warning(f"Unexpected processed key structure: {object_key}")
            return extract_document_id_from_key(object_key)

    except Exception as e:
        logger.warning(
            f"Could not extract document ID from processed key {object_key}: {e}")
        return f"unknown_{object_key.replace('/', '_').split('.')[0]}"


def cleanup_raw_data(document_id: str, processed_key: str, source_bucket: str) -> int:
    """
    Clean up raw data files related to a deleted processed file.

    Args:
        document_id: Document identifier
        processed_key: Original processed file key
        source_bucket: Name of the source bucket where deletion occurred

    Returns:
        Number of raw objects deleted
    """
    if not RAW_BUCKET:
        return 0

    try:
        # Extract patient_id and clean_filename from processed key
        # Processed structure: processed/{patient_id}/{clean_filename}/file.json
        key_parts = processed_key.split('/')
        
        if len(key_parts) >= 3 and key_parts[0] == 'processed':
            patient_id = key_parts[1]
            clean_filename = key_parts[2]
        else:
            logger.warning(f"Unexpected processed key structure: {processed_key}")
            return 0

        # Look for raw files that could match this processed file
        # Raw structure: {patient_id}/{category}/{timestamp}/{file_id}/{filename}
        possible_prefixes = [
            f"{patient_id}/"
        ]
        
        objects_to_delete = []
        
        for prefix in possible_prefixes:
            logger.info(f"Looking for raw files with prefix: {prefix}")
            
            try:
                response = s3_client.list_objects_v2(
                    Bucket=RAW_BUCKET,
                    Prefix=prefix
                )

                if 'Contents' in response:
                    for obj in response['Contents']:
                        # Check if this raw file corresponds to our processed file
                        raw_filename = obj['Key'].split('/')[-1]
                        raw_clean_filename = raw_filename.split('.')[0]
                        
                        # Remove patient prefix if present
                        if raw_clean_filename.startswith(f"patient_{patient_id}_"):
                            raw_clean_filename = raw_clean_filename[len(f"patient_{patient_id}_"):]
                        
                        # Match if clean filenames are the same
                        if raw_clean_filename == clean_filename:
                            objects_to_delete.append({'Key': obj['Key']})
                            logger.info(f"Found matching raw file: {obj['Key']}")
                            
            except Exception as e:
                logger.warning(f"Error listing objects with prefix {prefix}: {e}")
                continue

        if objects_to_delete:
            # Log each file being deleted
            for obj in objects_to_delete:
                logger.info(
                    f"Processing deletion of {obj['Key']} from bucket {RAW_BUCKET}")

            # Delete in batches of 1000 (S3 limit)
            deleted_count = 0
            for i in range(0, len(objects_to_delete), 1000):
                batch = objects_to_delete[i:i+1000]
                s3_client.delete_objects(
                    Bucket=RAW_BUCKET,
                    Delete={'Objects': batch}
                )
                deleted_count += len(batch)

                # Log completion for each file in the batch
                for obj in batch:
                    logger.info(f"File cleanup completed for {obj['Key']}")

            logger.info(
                f"Deleted {deleted_count} raw objects for patient {patient_id}, clean filename {clean_filename}")
            return deleted_count
        else:
            logger.info(f"No matching raw files found for processed file: {processed_key}")

        return 0

    except Exception as e:
        logger.error(f"Error cleaning up raw data: {str(e)}")
        return 0


def cleanup_processed_data(document_id: str, original_key: str, source_bucket: str) -> int:
    """
    Clean up processed data files related to a deleted raw file.

    Args:
        document_id: Document identifier (not used, we use original_key structure)
        original_key: Original raw file key
        source_bucket: Name of the source bucket where deletion occurred

    Returns:
        Number of processed objects deleted
    """
    if not PROCESSED_BUCKET:
        return 0

    try:
        # Extract patient_id and filename from original raw key
        # Raw structure: {patient_id}/{category}/{timestamp}/{file_id}/{filename}
        key_parts = original_key.split('/')
        
        if len(key_parts) >= 2:
            # New structure: {patient_id}/{category}/{timestamp}/{file_id}/{filename}
            patient_id = key_parts[0]
            filename = key_parts[-1]  # Last part is always the filename
            else:
                # Structure: {patient_id}/{filename}
                patient_id = key_parts[0]
                filename = key_parts[-1]
        else:
            # Single filename - use unknown patient
            patient_id = 'unknown'
            filename = key_parts[0]

        # With flattened structure: processed/{patient_id}/{clean_filename}/
        # Extract clean filename (remove extension and patient prefix)
        clean_filename = filename.split('.')[0]
        if clean_filename.startswith(f"patient_{patient_id}_"):
            clean_filename = clean_filename[len(f"patient_{patient_id}_"):]
        
        prefix = f"processed/{patient_id}/{clean_filename}/"
        
        logger.info(f"Looking for processed files with prefix: {prefix}")

        response = s3_client.list_objects_v2(
            Bucket=PROCESSED_BUCKET,
            Prefix=prefix
        )

        objects_to_delete = []
        if 'Contents' in response:
            for obj in response['Contents']:
                objects_to_delete.append({'Key': obj['Key']})

        if objects_to_delete:
            # Log each file being deleted with detailed information
            for obj in objects_to_delete:
                logger.info(
                    f"Processing deletion of {obj['Key']} from bucket {PROCESSED_BUCKET}")

            # Delete in batches of 1000 (S3 limit)
            deleted_count = 0
            for i in range(0, len(objects_to_delete), 1000):
                batch = objects_to_delete[i:i+1000]
                s3_client.delete_objects(
                    Bucket=PROCESSED_BUCKET,
                    Delete={'Objects': batch}
                )
                deleted_count += len(batch)

                # Log completion for each file in the batch
                for obj in batch:
                    logger.info(f"File cleanup completed for {obj['Key']}")

            logger.info(
                f"Deleted {deleted_count} processed objects for patient {patient_id}, filename {filename}")
            return deleted_count
        else:
            logger.info(f"No processed files found for prefix: {prefix}")

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
    # In flattened structure: processed/{patient_id}/{clean_filename}/extracted_data.json
    return object_key.endswith('/extracted_data.json')
