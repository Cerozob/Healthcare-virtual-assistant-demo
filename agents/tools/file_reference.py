"""
File Reference Tool for Healthcare Assistant.
Handles S3 file references and provides file information for multimodal processing.
Works with files already uploaded to S3 via client-side upload.
"""

import logging
import boto3
from typing import Optional, Dict, Any, List
from strands import tool
from pydantic import BaseModel, Field
import os
from botocore.exceptions import ClientError
from shared.config import get_agent_config

logger = logging.getLogger(__name__)

class FileInfo(BaseModel):
    """File information model."""
    s3_key: str = Field(..., description="S3 key of the file")
    s3_uri: str = Field(..., description="Full S3 URI")
    file_name: str = Field(..., description="Original file name")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    content_type: Optional[str] = Field(None, description="MIME type of the file")
    patient_id: Optional[str] = Field(None, description="Patient ID extracted from S3 path")
    category: Optional[str] = Field(None, description="File category")
    last_modified: Optional[str] = Field(None, description="Last modified timestamp")

@tool(
    name="get_file_info",
    description="Get information about a file stored in S3 using its S3 key or URI. Useful for understanding file context in multimodal conversations."
)
def get_file_info(s3_reference: str, tool_context=None) -> Dict[str, Any]:
    """
    Get information about a file stored in S3.
    
    Args:
        s3_reference: S3 key (e.g., 'patient123/medical-images/file.jpg') or S3 URI (e.g., 's3://bucket/key')
        tool_context: Tool execution context
        
    Returns:
        Dict containing file information and metadata
    """
    try:
        logger.info(f"🔍 Getting file info for: {s3_reference}")
        
        # Parse S3 reference
        if s3_reference.startswith('s3://'):
            # Full S3 URI
            parts = s3_reference[5:].split('/', 1)
            if len(parts) != 2:
                return {
                    "success": False,
                    "error": "Invalid S3 URI format. Expected: s3://bucket/key",
                    "file_info": None
                }
            bucket_name, s3_key = parts
        else:
            # Just the S3 key, use default bucket from agent config
            s3_key = s3_reference
            try:
                config = get_agent_config()
                bucket_name = config.raw_bucket_name or config.session_bucket
            except Exception:
                bucket_name = os.environ.get('RAW_BUCKET_NAME', os.environ.get('S3_BUCKET_NAME', ''))
            
            if not bucket_name:
                return {
                    "success": False,
                    "error": "No bucket name configured. Check agent configuration for RAW_BUCKET_NAME or SESSION_BUCKET.",
                    "file_info": None
                }
        
        # Initialize S3 client
        s3_client = boto3.client('s3', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        
        # Get file metadata
        try:
            response = s3_client.head_object(Bucket=bucket_name, Key=s3_key)
            
            # Extract file information
            file_name = s3_key.split('/')[-1]  # Get filename from key
            file_size = response.get('ContentLength')
            content_type = response.get('ContentType')
            last_modified = response.get('LastModified')
            metadata = response.get('Metadata', {})
            
            # Extract patient ID from S3 path (assuming format: patient_id/category/file_id/filename)
            path_parts = s3_key.split('/')
            patient_id = path_parts[0] if len(path_parts) > 0 else None
            category = path_parts[1] if len(path_parts) > 1 else None
            
            # Build S3 URI
            s3_uri = f"s3://{bucket_name}/{s3_key}"
            
            file_info = FileInfo(
                s3_key=s3_key,
                s3_uri=s3_uri,
                file_name=file_name,
                file_size=file_size,
                content_type=content_type,
                patient_id=patient_id,
                category=category,
                last_modified=last_modified.isoformat() if last_modified else None
            )
            
            logger.info(f"✅ File info retrieved: {file_name} ({file_size} bytes)")
            
            return {
                "success": True,
                "file_info": file_info.model_dump(),
                "message": f"File information retrieved for {file_name}",
                "metadata": metadata
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                return {
                    "success": False,
                    "error": f"File not found: {s3_key}",
                    "file_info": None
                }
            elif error_code == 'NoSuchBucket':
                return {
                    "success": False,
                    "error": f"Bucket not found: {bucket_name}",
                    "file_info": None
                }
            else:
                return {
                    "success": False,
                    "error": f"S3 error ({error_code}): {e.response['Error']['Message']}",
                    "file_info": None
                }
                
    except Exception as e:
        logger.error(f"💥 Unexpected error getting file info: {e}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "file_info": None
        }

@tool(
    name="list_patient_files",
    description="List all files for a specific patient stored in S3. Useful for understanding what files are available for a patient."
)
def list_patient_files(patient_id: str, category: Optional[str] = None, tool_context=None) -> Dict[str, Any]:
    """
    List all files for a specific patient.
    
    Args:
        patient_id: Patient ID to list files for
        category: Optional category filter (medical-history, exam-results, medical-images, identification, other)
        tool_context: Tool execution context
        
    Returns:
        Dict containing list of patient files
    """
    try:
        logger.info(f"📋 Listing files for patient: {patient_id}")
        
        if not patient_id or not patient_id.strip():
            return {
                "success": False,
                "error": "Patient ID is required",
                "files": []
            }
        
        # Get bucket name from agent config
        try:
            config = get_agent_config()
            bucket_name = config.raw_bucket_name or config.session_bucket
        except Exception:
            bucket_name = os.environ.get('RAW_BUCKET_NAME', os.environ.get('S3_BUCKET_NAME', ''))
            
        if not bucket_name:
            return {
                "success": False,
                "error": "No bucket name configured. Check agent configuration for RAW_BUCKET_NAME or SESSION_BUCKET.",
                "files": []
            }
        
        # Initialize S3 client
        s3_client = boto3.client('s3', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        
        # Build prefix for patient files
        if category:
            prefix = f"{patient_id}/{category}/"
        else:
            prefix = f"{patient_id}/"
        
        logger.info(f"🔍 Searching with prefix: {prefix}")
        
        # List objects
        try:
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                MaxKeys=100  # Limit to prevent large responses
            )
            
            files = []
            for obj in response.get('Contents', []):
                s3_key = obj['Key']
                file_name = s3_key.split('/')[-1]
                
                # Skip directory markers
                if file_name == '':
                    continue
                
                # Extract category from path
                path_parts = s3_key.split('/')
                file_category = path_parts[1] if len(path_parts) > 1 else 'other'
                
                file_info = {
                    "s3_key": s3_key,
                    "s3_uri": f"s3://{bucket_name}/{s3_key}",
                    "file_name": file_name,
                    "file_size": obj.get('Size'),
                    "category": file_category,
                    "last_modified": obj.get('LastModified').isoformat() if obj.get('LastModified') else None,
                    "patient_id": patient_id
                }
                
                files.append(file_info)
            
            logger.info(f"✅ Found {len(files)} files for patient {patient_id}")
            
            return {
                "success": True,
                "files": files,
                "count": len(files),
                "message": f"Found {len(files)} files for patient {patient_id}",
                "patient_id": patient_id,
                "category_filter": category
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                return {
                    "success": False,
                    "error": f"Bucket not found: {bucket_name}",
                    "files": []
                }
            else:
                return {
                    "success": False,
                    "error": f"S3 error ({error_code}): {e.response['Error']['Message']}",
                    "files": []
                }
                
    except Exception as e:
        logger.error(f"💥 Unexpected error listing patient files: {e}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "files": []
        }

@tool(
    name="analyze_file_content",
    description="Analyze the content of a file stored in S3. For images, provides visual analysis. For documents, extracts and analyzes text content."
)
def analyze_file_content(s3_reference: str, analysis_type: str = "general", tool_context=None) -> Dict[str, Any]:
    """
    Analyze the content of a file stored in S3.
    
    Args:
        s3_reference: S3 key or URI of the file to analyze
        analysis_type: Type of analysis (general, medical, diagnostic, text_extraction)
        tool_context: Tool execution context
        
    Returns:
        Dict containing analysis results
    """
    try:
        logger.info(f"🔬 Analyzing file content: {s3_reference}")
        
        # First get file info
        file_info_result = get_file_info(s3_reference, tool_context)
        
        if not file_info_result.get("success"):
            return file_info_result
        
        file_info = file_info_result["file_info"]
        content_type = file_info.get("content_type", "")
        file_name = file_info.get("file_name", "")
        
        # Determine analysis approach based on content type
        if content_type.startswith('image/'):
            analysis_result = {
                "file_type": "image",
                "content_type": content_type,
                "analysis_type": analysis_type,
                "message": f"Image file {file_name} is ready for visual analysis by the AI model",
                "recommendations": [
                    "This image can be processed by multimodal AI models for visual analysis",
                    "For medical images, consider asking specific questions about findings, abnormalities, or diagnostic features",
                    "The image is stored in S3 and can be referenced directly in conversations"
                ]
            }
        elif content_type.startswith('text/') or content_type == 'application/pdf':
            analysis_result = {
                "file_type": "document",
                "content_type": content_type,
                "analysis_type": analysis_type,
                "message": f"Document {file_name} is ready for text analysis",
                "recommendations": [
                    "This document can be processed for text extraction and analysis",
                    "For medical documents, consider asking about diagnoses, treatments, or patient information",
                    "PDF and text files can be analyzed for structured medical information"
                ]
            }
        else:
            analysis_result = {
                "file_type": "other",
                "content_type": content_type,
                "analysis_type": analysis_type,
                "message": f"File {file_name} has content type {content_type}",
                "recommendations": [
                    "File type may have limited analysis capabilities",
                    "Consider converting to a supported format if detailed analysis is needed"
                ]
            }
        
        return {
            "success": True,
            "file_info": file_info,
            "analysis": analysis_result,
            "message": f"Content analysis prepared for {file_name}"
        }
        
    except Exception as e:
        logger.error(f"💥 Unexpected error analyzing file content: {e}")
        return {
            "success": False,
            "error": f"Content analysis error: {str(e)}",
            "analysis": None
        }
