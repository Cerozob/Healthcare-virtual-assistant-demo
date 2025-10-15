# Document Upload API Reference

## Overview

API endpoint for uploading medical documents during chat conversations. Documents are processed asynchronously through Bedrock Data Automation with PII anonymization.

## Endpoint

```
POST /api/v1/documents/upload
```

## Authentication

No authentication required (per POC scope - authentication removed).

## Request

### Headers

```
Content-Type: application/json
```

### Body Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `fileName` | string | Yes | Original filename with extension |
| `fileSize` | integer | Yes | File size in bytes (max 100MB) |
| `contentType` | string | Yes | MIME type of the file |
| `patientId` | string | No | Associated patient identifier |
| `chatSessionId` | string | No | Current chat session identifier |
| `fileContent` | string | Yes | Base64-encoded file content |

### Supported Content Types

| Content Type | Extensions | Description |
|--------------|------------|-------------|
| `application/pdf` | .pdf | PDF documents |
| `image/jpeg` | .jpg, .jpeg | JPEG images |
| `image/png` | .png | PNG images |
| `image/tiff` | .tif, .tiff | TIFF images |
| `audio/mpeg` | .mp3 | MP3 audio files |
| `audio/wav` | .wav | WAV audio files |
| `video/mp4` | .mp4 | MP4 video files |
| `application/msword` | .doc | Word documents (legacy) |
| `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | .docx | Word documents |

### Example Request

```json
{
  "fileName": "patient_medical_record.pdf",
  "fileSize": 2048576,
  "contentType": "application/pdf",
  "patientId": "patient-12345",
  "chatSessionId": "session-67890",
  "fileContent": "JVBERi0xLjQKJeLjz9MKMyAwIG9iago8PC9UeXBlL1BhZ2UvUGFyZW50IDIgMCBSL1Jlc291cmNlczw8L0ZvbnQ8PC9GMSA1IDAgUj4+L1Byb2NTZXRbL1BERi9UZXh0L0ltYWdlQi9JbWFnZUMvSW1hZ2VJXT4+L01lZGlhQm94WzAgMCA1OTUuMzIgODQxLjkyXS9Db250ZW50cyA0IDAgUi9Hcm91cDw8L1R5cGUvR3JvdXAvUy9UcmFuc3BhcmVuY3kvQ1MvRGV2aWNlUkdCPj4vVGFicz..."
}
```

## Response

### Success Response (200 OK)

```json
{
  "documentId": "550e8400-e29b-41d4-a716-446655440000",
  "s3Key": "patients/patient-12345/2025/01/14/550e8400-e29b-41d4-a716-446655440000/patient_medical_record.pdf",
  "bucket": "healthcare-raw-documents",
  "status": "uploaded",
  "message": "Document uploaded successfully and queued for processing"
}
```

### Error Responses

#### 400 Bad Request - Missing Required Fields

```json
{
  "error": "Missing required fields: fileName, contentType, fileContent"
}
```

#### 400 Bad Request - Unsupported File Type

```json
{
  "error": "Unsupported file type: application/zip"
}
```

#### 400 Bad Request - File Too Large

```json
{
  "error": "File size exceeds maximum allowed size of 104857600 bytes"
}
```

#### 500 Internal Server Error

```json
{
  "error": "AWS service error: Access Denied"
}
```

## Processing Flow

1. **Upload**: Document is uploaded to S3 raw bucket
2. **Event**: EventBridge event triggers processing Lambda
3. **Processing**: Document is submitted to Bedrock Data Automation
4. **Extraction**: BDA extracts structured data with PII anonymization
5. **Storage**: Extracted data is stored in database and Knowledge Base
6. **Notification**: Chat session receives completion notification

## Processing Status

After upload, you can track processing status using the document ID:

```
GET /api/v1/documents/status/{documentId}
```

### Status Values

- `uploaded`: Document uploaded to S3, awaiting processing
- `processing`: Document being processed by BDA
- `completed`: Processing complete, data available
- `failed`: Processing failed, check error message

## S3 Storage Structure

Documents are stored with an organized folder structure:

```
healthcare-raw-documents/
├── patients/
│   └── {patient_id}/
│       └── {YYYY}/
│           └── {MM}/
│               └── {DD}/
│                   └── {document_id}/
│                       └── {filename}
└── general/
    └── {YYYY}/
        └── {MM}/
            └── {DD}/
                └── {document_id}/
                    └── {filename}
```

## PII Anonymization

Documents are processed with PII anonymization:

### Anonymized Fields
- Patient name (first and last)
- Phone numbers
- Email addresses

### Preserved Fields (Medical Utility)
- Medical Record Number (MRN)
- Date of Birth
- Diagnoses and ICD codes
- Medications
- Vital signs
- Symptoms
- Treatment plans

## Rate Limits

No rate limits enforced in POC. Production deployment should implement:
- Per-user rate limiting
- Per-session rate limiting
- File size quotas

## Code Examples

### JavaScript/TypeScript (Frontend)

```typescript
async function uploadDocument(
  file: File,
  patientId: string,
  chatSessionId: string
): Promise<UploadResponse> {
  // Convert file to base64
  const base64Content = await fileToBase64(file);
  
  const response = await fetch('/api/v1/documents/upload', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      fileName: file.name,
      fileSize: file.size,
      contentType: file.type,
      patientId,
      chatSessionId,
      fileContent: base64Content,
    }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error);
  }
  
  return response.json();
}

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      const base64 = reader.result as string;
      // Remove data URL prefix
      const base64Content = base64.split(',')[1];
      resolve(base64Content);
    };
    reader.onerror = reject;
  });
}
```

### Python (Testing)

```python
import base64
import requests

def upload_document(
    file_path: str,
    patient_id: str,
    chat_session_id: str,
    api_url: str
) -> dict:
    """Upload a document to the API."""
    
    # Read and encode file
    with open(file_path, 'rb') as f:
        file_content = base64.b64encode(f.read()).decode('utf-8')
    
    # Determine content type
    import mimetypes
    content_type, _ = mimetypes.guess_type(file_path)
    
    # Prepare request
    payload = {
        'fileName': os.path.basename(file_path),
        'fileSize': os.path.getsize(file_path),
        'contentType': content_type,
        'patientId': patient_id,
        'chatSessionId': chat_session_id,
        'fileContent': file_content
    }
    
    # Send request
    response = requests.post(
        f'{api_url}/api/v1/documents/upload',
        json=payload
    )
    
    response.raise_for_status()
    return response.json()

# Example usage
result = upload_document(
    file_path='patient_record.pdf',
    patient_id='patient-123',
    chat_session_id='session-456',
    api_url='https://api.example.com'
)

print(f"Document uploaded: {result['documentId']}")
```

### cURL

```bash
# Prepare base64 content
FILE_CONTENT=$(base64 -i patient_record.pdf)

# Upload document
curl -X POST https://api.example.com/api/v1/documents/upload \
  -H "Content-Type: application/json" \
  -d "{
    \"fileName\": \"patient_record.pdf\",
    \"fileSize\": 2048576,
    \"contentType\": \"application/pdf\",
    \"patientId\": \"patient-123\",
    \"chatSessionId\": \"session-456\",
    \"fileContent\": \"$FILE_CONTENT\"
  }"
```

## Testing

### Test Files

Sample test files are available in `docs/test-files/`:
- `test_medical_record.pdf`
- `test_xray_image.jpg`
- `test_consultation_audio.mp3`

### Integration Test

```python
import pytest
from tests.helpers import upload_test_document, wait_for_processing

def test_document_upload_and_processing():
    """Test complete document upload and processing workflow."""
    
    # Upload document
    result = upload_test_document(
        file_path='tests/fixtures/test_medical_record.pdf',
        patient_id='test-patient-001',
        chat_session_id='test-session-001'
    )
    
    assert result['status'] == 'uploaded'
    document_id = result['documentId']
    
    # Wait for processing to complete
    status = wait_for_processing(document_id, timeout=300)
    
    assert status['status'] == 'completed'
    assert 'extracted_data' in status
    assert status['extracted_data'] is not None
```

## Troubleshooting

### Common Issues

1. **"Unsupported file type" error**
   - Verify the file extension matches the content type
   - Check that the content type is in the supported list

2. **"File size exceeds maximum" error**
   - Compress large files before upload
   - Split large documents into smaller parts

3. **Base64 encoding issues**
   - Ensure proper base64 encoding without data URL prefix
   - Verify no line breaks or whitespace in encoded content

4. **Processing timeout**
   - Large files may take several minutes to process
   - Check CloudWatch logs for processing status
   - Query DynamoDB status table for detailed information

## Security Notes

- All uploads are encrypted at rest (S3 AES256)
- All data in transit uses TLS/SSL
- PII is automatically anonymized during processing
- No authentication required in POC (add in production)

## Support

For issues or questions:
- Check CloudWatch logs: `/aws/lambda/healthcare-document-upload`
- Review processing status in DynamoDB
- Contact development team with document ID for investigation
