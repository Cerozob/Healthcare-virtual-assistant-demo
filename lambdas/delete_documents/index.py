"""
Lambda function to delete workflow outputs when original files are deleted.
Uses patient identifiers in paths and S3 metadata for data management.
"""

import json
import boto3
import logging
from typing import Dict, Any, List
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")
ssm_client = boto3.client("ssm")


def get_ssm_parameter(parameter_name: str) -> str:
    """Get parameter value from SSM Parameter Store."""
    try:
        response = ssm_client.get_parameter(Name=parameter_name)
        return response["Parameter"]["Value"]
    except ClientError as e:
        logger.error(f"Failed to get SSM parameter {parameter_name}: {e}")
        raise


def extract_patient_id_from_path(s3_key: str) -> str:
    """Extract patient ID from S3 object path."""
    # Assuming path structure: patient_id/folder/file.ext
    path_parts = s3_key.split("/")
    if len(path_parts) >= 1:
        return path_parts[0]
    return None


def find_related_outputs(
    processed_bucket: str, patient_id: str, original_key: str
) -> List[str]:
    """Find all processed outputs related to the original file."""
    try:
        # List objects with patient ID prefix
        response = s3_client.list_objects_v2(
            Bucket=processed_bucket, Prefix=f"{patient_id}/"
        )

        related_objects = []
        if "Contents" in response:
            for obj in response["Contents"]:
                # Check metadata to see if this output is related to the original file
                try:
                    metadata_response = s3_client.head_object(
                        Bucket=processed_bucket, Key=obj["Key"]
                    )

                    # Check if metadata contains reference to original file
                    metadata = metadata_response.get("Metadata", {})
                    if (
                        metadata.get("source-file") == original_key
                        or metadata.get("original-key") == original_key
                    ):
                        related_objects.append(obj["Key"])

                except ClientError as e:
                    logger.warning(f"Could not get metadata for {obj['Key']}: {e}")
                    continue

        return related_objects

    except ClientError as e:
        logger.error(f"Failed to list objects in {processed_bucket}: {e}")
        return []


def delete_s3_objects(bucket: str, keys: List[str]) -> None:
    """Delete multiple S3 objects."""
    if not keys:
        return

    try:
        # Batch delete objects
        delete_objects = [{"Key": key} for key in keys]

        # S3 delete_objects has a limit of 1000 objects per request
        for i in range(0, len(delete_objects), 1000):
            batch = delete_objects[i : i + 1000]

            response = s3_client.delete_objects(
                Bucket=bucket, Delete={"Objects": batch}
            )

            # Log successful deletions
            if "Deleted" in response:
                for deleted in response["Deleted"]:
                    logger.info(f"Deleted: {deleted['Key']}")

            # Log any errors
            if "Errors" in response:
                for error in response["Errors"]:
                    logger.error(f"Failed to delete {error['Key']}: {error['Message']}")

    except ClientError as e:
        logger.error(f"Failed to delete objects: {e}")
        raise


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle S3 delete events and clean up related processed outputs.
    """
    try:
        # Get processed bucket name from SSM
        processed_bucket = get_ssm_parameter(
            "/healthcare/document-workflow/processed-bucket"
        )

        logger.info(f"Processing delete event: {json.dumps(event)}")

        # Parse the S3 event
        if "detail" not in event:
            logger.error("No detail found in event")
            return {"statusCode": 400, "body": "Invalid event format"}

        detail = event["detail"]
        bucket_name = detail["bucket"]["name"]
        object_key = detail["object"]["key"]

        logger.info(f"File deleted: s3://{bucket_name}/{object_key}")

        # Extract patient ID from the deleted file path
        patient_id = extract_patient_id_from_path(object_key)
        if not patient_id:
            logger.warning(f"Could not extract patient ID from path: {object_key}")
            return {"statusCode": 200, "body": "No patient ID found in path"}

        logger.info(f"Patient ID extracted: {patient_id}")

        # Find all related processed outputs
        related_outputs = find_related_outputs(processed_bucket, patient_id, object_key)

        if not related_outputs:
            logger.info(f"No related outputs found for {object_key}")
            return {"statusCode": 200, "body": "No related outputs to delete"}

        logger.info(f"Found {len(related_outputs)} related outputs to delete")

        # Delete the related outputs
        delete_s3_objects(processed_bucket, related_outputs)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Successfully processed deletion",
                    "deleted_files": related_outputs,
                    "patient_id": patient_id,
                }
            ),
        }

    except Exception as e:
        logger.error(f"Error processing deletion event: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
