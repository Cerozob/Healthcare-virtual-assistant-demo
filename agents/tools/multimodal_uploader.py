"""
Multimodal Content Uploader Tool
Handles uploading images, documents, and other files to S3 with patient-specific organization.
"""

import boto3
import logging
import hashlib
import mimetypes
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class MultimodalUploader:
    """Handles uploading multimodal content to S3 with patient context organization."""
    
    def __init__(self, raw_bucket_name: str, aws_region: str):
        """
        Initialize the multimodal uploader.
        
        Args:
            raw_bucket_name: S3 bucket name for raw data storage
            aws_region: AWS region for S3 client
        """
        self.raw_bucket_name = raw_bucket_name
        self.aws_region = aws_region
        self.s3_client = boto3.client('s3', region_name=aws_region)
        
    def _generate_file_key(self, patient_id: str, file_name: str, content_hash: str) -> str:
        """
        Generate S3 key for file storage with patient organization (flat structure).
        
        Args:
            patient_id: Patient identifier (cedula or medical record number)
            file_name: Original file name
            content_hash: Hash of file content for uniqueness
            
        Returns:
            S3 key path: patient_id/timestamp_hash_filename
        """
        # Clean patient ID for use in path
        clean_patient_id = patient_id.replace('/', '_').replace('\\', '_')
        
        # Generate timestamp for organization
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        # Generate unique filename with hash prefix to avoid collisions
        unique_filename = f"{timestamp}_{content_hash[:8]}_{file_name}"
        
        # Construct S3 key: patient_id/unique_filename (flat structure for better workflow processing)
        s3_key = f"{clean_patient_id}/{unique_filename}"
        
        return s3_key
    
    def _calculate_content_hash(self, content_bytes: bytes) -> str:
        """Calculate SHA-256 hash of content for uniqueness and deduplication."""
        return hashlib.sha256(content_bytes).hexdigest()
    
    def _determine_content_type(self, file_name: str, format_hint: str = None) -> str:
        """
        Determine MIME type for S3 upload.
        
        Args:
            file_name: Original file name
            format_hint: Format hint from content block (e.g., 'jpeg', 'pdf')
            
        Returns:
            MIME type string
        """
        # Try to get MIME type from file extension
        mime_type, _ = mimetypes.guess_type(file_name)
        
        if mime_type:
            return mime_type
            
        # Fallback to format hint mapping
        format_to_mime = {
            'jpeg': 'image/jpeg',
            'jpg': 'image/jpeg', 
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'pdf': 'application/pdf',
            'txt': 'text/plain',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'md': 'text/markdown'
        }
        
        if format_hint and format_hint.lower() in format_to_mime:
            return format_to_mime[format_hint.lower()]
            
        # Default fallback
        return 'application/octet-stream'
    
    def upload_image(self, patient_id: str, image_block: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upload image content to S3.
        
        Args:
            patient_id: Patient identifier
            image_block: Strands image content block
            
        Returns:
            Upload result with S3 location and metadata
        """
        try:
            image_data = image_block["image"]
            content_bytes = image_data["source"]["bytes"]
            image_format = image_data.get("format", "jpeg")
            
            # Generate file name and metadata
            file_name = f"image.{image_format}"
            content_hash = self._calculate_content_hash(content_bytes)
            content_type = self._determine_content_type(file_name, image_format)
            
            # Generate S3 key (flat structure)
            s3_key = self._generate_file_key(patient_id, file_name, content_hash)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.raw_bucket_name,
                Key=s3_key,
                Body=content_bytes,
                ContentType=content_type,
                Metadata={
                    'patient_id': patient_id,
                    'content_type': 'image',
                    'format': image_format,
                    'content_hash': content_hash,
                    'upload_timestamp': datetime.utcnow().isoformat(),
                    'original_filename': file_name
                }
            )
            
            s3_url = f"s3://{self.raw_bucket_name}/{s3_key}"
            
            logger.info(f"✅ Uploaded image for patient {patient_id} to {s3_url}")
            
            return {
                'success': True,
                'content_type': 'image',
                's3_url': s3_url,
                's3_key': s3_key,
                'bucket': self.raw_bucket_name,
                'patient_id': patient_id,
                'file_size': len(content_bytes),
                'content_hash': content_hash,
                'format': image_format
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to upload image for patient {patient_id}: {e}")
            return {
                'success': False,
                'content_type': 'image',
                'error': str(e),
                'patient_id': patient_id
            }
    
    def upload_document(self, patient_id: str, document_block: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upload document content to S3.
        
        Args:
            patient_id: Patient identifier
            document_block: Strands document content block
            
        Returns:
            Upload result with S3 location and metadata
        """
        try:
            document_data = document_block["document"]
            content_bytes = document_data["source"]["bytes"]
            document_format = document_data.get("format", "txt")
            file_name = document_data.get("name", f"document.{document_format}")
            
            # Generate metadata
            content_hash = self._calculate_content_hash(content_bytes)
            content_type = self._determine_content_type(file_name, document_format)
            
            # Generate S3 key (flat structure)
            s3_key = self._generate_file_key(patient_id, file_name, content_hash)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.raw_bucket_name,
                Key=s3_key,
                Body=content_bytes,
                ContentType=content_type,
                Metadata={
                    'patient_id': patient_id,
                    'content_type': 'document',
                    'format': document_format,
                    'content_hash': content_hash,
                    'upload_timestamp': datetime.utcnow().isoformat(),
                    'original_filename': file_name
                }
            )
            
            s3_url = f"s3://{self.raw_bucket_name}/{s3_key}"
            
            logger.info(f"✅ Uploaded document '{file_name}' for patient {patient_id} to {s3_url}")
            
            return {
                'success': True,
                'content_type': 'document',
                's3_url': s3_url,
                's3_key': s3_key,
                'bucket': self.raw_bucket_name,
                'patient_id': patient_id,
                'file_name': file_name,
                'file_size': len(content_bytes),
                'content_hash': content_hash,
                'format': document_format
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to upload document for patient {patient_id}: {e}")
            return {
                'success': False,
                'content_type': 'document',
                'error': str(e),
                'patient_id': patient_id,
                'file_name': document_block.get("document", {}).get("name", "unknown")
            }
    
    def upload_multimodal_content(self, patient_id: str, content_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Upload all multimodal content from content blocks to S3.
        
        Args:
            patient_id: Patient identifier for organizing uploads
            content_blocks: List of Strands content blocks
            
        Returns:
            List of upload results for each multimodal content block
        """
        upload_results = []
        
        for i, block in enumerate(content_blocks):
            if "image" in block:
                result = self.upload_image(patient_id, block)
                result['block_index'] = i
                upload_results.append(result)
                
            elif "document" in block:
                result = self.upload_document(patient_id, block)
                result['block_index'] = i
                upload_results.append(result)
        
        # Log summary
        successful_uploads = [r for r in upload_results if r.get('success')]
        failed_uploads = [r for r in upload_results if not r.get('success')]
        
        logger.info(f"📊 Upload summary for patient {patient_id}: {len(successful_uploads)} successful, {len(failed_uploads)} failed")
        
        return upload_results
    
    def check_bucket_access(self) -> bool:
        """
        Check if the S3 bucket is accessible.
        
        Returns:
            True if bucket is accessible, False otherwise
        """
        try:
            self.s3_client.head_bucket(Bucket=self.raw_bucket_name)
            return True
        except ClientError as e:
            logger.error(f"❌ Cannot access S3 bucket {self.raw_bucket_name}: {e}")
            return False


def create_multimodal_uploader(raw_bucket_name: str, aws_region: str) -> Optional[MultimodalUploader]:
    """
    Factory function to create a multimodal uploader with validation.
    
    Args:
        raw_bucket_name: S3 bucket name for raw data storage
        aws_region: AWS region
        
    Returns:
        MultimodalUploader instance or None if configuration is invalid
    """
    if not raw_bucket_name:
        logger.warning("⚠️ No raw bucket name configured - multimodal uploads disabled")
        return None
        
    try:
        uploader = MultimodalUploader(raw_bucket_name, aws_region)
        
        # Test bucket access
        if not uploader.check_bucket_access():
            logger.error(f"❌ Cannot access S3 bucket {raw_bucket_name} - multimodal uploads disabled")
            return None
            
        logger.info(f"✅ Multimodal uploader initialized for bucket: {raw_bucket_name}")
        return uploader
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize multimodal uploader: {e}")
        return None
