"""
Workflow entrypoint lambda that routes files based on MIME type.
Routes to: document, audio, or passthrough processing branches.
"""

import json
import boto3
import logging
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")
ssm_client = boto3.client("ssm")

# * Supported file types

# MIME type classifications
DOCUMENT_MIMETYPES = [
    "image/png",
    "image/jpeg",
    "image/tiff",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]

PASSTHROUGH_MIMETYPES = ["application/json", "text/plain"]

AUDIO_MIMETYPES = [
    "audio/aac",
    "audio/mp3",
    "audio/flac",
    "audio/wav",
    "audio/ogg",
    "audio/mpeg",
]


def extract_patient_id_from_path(s3_key: str) -> str:
    """Extract patient ID from S3 object path."""
    # Assuming path structure: patient_id/folder/file.ext
    path_parts = s3_key.split("/")
    if len(path_parts) >= 1:
        return path_parts[0]
    return None


def get_file_mimetype(bucket: str, key: str) -> Optional[str]:
    """Get the MIME type of an S3 object."""
    try:
        response = s3_client.head_object(Bucket=bucket, Key=key)
        return response.get("ContentType")
    except ClientError as e:
        logger.error(f"Failed to get object metadata for s3://{bucket}/{key}: {e}")
        return None


def determine_processing_branch(mimetype: str) -> str:
    """
    Determine which processing branch to use based on MIME type.

    Returns:
        - "document" for document processing (Bedrock Data Automation)
        - "audio" for audio processing (Amazon HealthScribe)
        - "passthrough" for direct processing (Amazon Comprehend Medical)
    """
    if not mimetype:
        logger.warning("No MIME type provided, defaulting to passthrough")
        return "passthrough"

    mimetype_lower = mimetype.lower()

    if mimetype_lower in DOCUMENT_MIMETYPES:
        return "document"
    elif mimetype_lower in AUDIO_MIMETYPES:
        return "audio"
    elif mimetype_lower in PASSTHROUGH_MIMETYPES:
        return "passthrough"
    else:
        logger.warning(f"Unknown MIME type: {mimetype}, defaulting to document")
        return "document"


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle S3 create events and route to appropriate processing branch.

    Returns a response indicating which branch should handle the file.
    """
    try:
        logger.info(f"Processing workflow entrypoint event: {json.dumps(event)}")

        # Parse the S3 event
        if "detail" not in event:
            logger.error("No detail found in event")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid event format"}),
            }

        detail = event["detail"]
        bucket_name = detail["bucket"]["name"]
        object_key = detail["object"]["key"]

        logger.info(f"Processing file: s3://{bucket_name}/{object_key}")

        # Get the file's MIME type
        mimetype = get_file_mimetype(bucket_name, object_key)

        if not mimetype:
            logger.error(f"Could not determine MIME type for {object_key}")
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Could not determine file MIME type"}),
            }

        # Determine processing branch
        processing_branch = determine_processing_branch(mimetype)

        logger.info(
            f"File {object_key} with MIME type {mimetype} routed to: {processing_branch}"
        )

        # Return the routing decision in Step Functions compatible format
        response = {
            "processing_branch": processing_branch,
            "bucket": bucket_name,
            "key": object_key,
            "mimetype": mimetype,
            "patient_id": extract_patient_id_from_path(object_key),
            "timestamp": context.aws_request_id,
            "statusCode": 200,
        }

        return response

    except Exception as e:
        logger.error(f"Error processing entrypoint event: {str(e)}")
        return {
            "processing_branch": "passthrough",  # Default fallback
            "error": str(e),
            "statusCode": 500,
        }
