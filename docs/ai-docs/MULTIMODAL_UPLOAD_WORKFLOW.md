# Multimodal Content Upload Workflow

## Overview

The Healthcare Agent now automatically uploads multimodal content (images, documents) to S3 with patient-specific organization. This happens transparently during message processing.

## Workflow Steps

1. **Content Processing**: Agent receives multimodal content blocks (images, documents)
2. **Patient Context Detection**: Agent analyzes the conversation to identify the patient
3. **Content Upload**: Files are uploaded to S3 with patient-specific organization
4. **Response Generation**: Agent processes the content and generates response
5. **Upload Results**: Response includes upload status and S3 locations

## S3 Organization Structure

```
s3://raw-bucket-name/
├── patient_123456/
│   ├── 20241103_143022_a1b2c3d4_xray.jpg
│   ├── 20241103_143030_i9j0k1l2_lab_results.pdf
│   ├── 20241103_143045_e5f6g7h8_ultrasound.png
│   └── 20241103_143055_m3n4o5p6_prescription.txt
└── patient_789012/
    ├── 20241103_144015_e5f6g7h8_scan.jpg
    └── 20241103_144020_m3n4o5p6_report.pdf
```

### File Naming Convention

Files are named with the pattern: `{timestamp}_{hash}_{original_name}`

- **Timestamp**: `YYYYMMDD_HHMMSS` format
- **Hash**: First 8 characters of SHA-256 content hash (for uniqueness)
- **Original Name**: Cleaned original filename

## Patient Context Detection

The agent uses existing patient context detection logic to identify:

- **Patient ID**: Cedula, medical record number, or other identifier
- **Patient Name**: Full name when available
- **Context Source**: How the patient was identified (tool extraction, LLM extraction, etc.)

If no patient context is detected, files are uploaded to `unknown_patient/` folder.

## Upload Features

### Content Types Supported

- **Images**: JPEG, PNG, GIF, WebP
- **Documents**: PDF, TXT, DOC, DOCX, Markdown

### Metadata Storage

Each uploaded file includes S3 metadata:

```json
{
  "patient_id": "123456",
  "content_type": "image",
  "format": "jpeg",
  "content_hash": "a1b2c3d4e5f6g7h8...",
  "upload_timestamp": "2024-11-03T14:30:22Z",
  "original_filename": "xray.jpg"
}
```

### Deduplication

Files with identical content (same SHA-256 hash) are automatically deduplicated by the naming convention.

## Configuration

### Environment Variables

```bash
# S3 Configuration (required for uploads)
RAW_BUCKET_NAME=ab2-cerozob-rawdata-us-east-1
AWS_REGION=us-east-1
```

### Permissions Required

The agent needs S3 permissions for:
- `s3:PutObject` - Upload files
- `s3:PutObjectMetadata` - Set file metadata
- `s3:HeadBucket` - Verify bucket access

## Response Format

The agent response now includes upload results:

```json
{
  "response": "I can see the X-ray image you've uploaded...",
  "sessionId": "healthcare_session_123",
  "patientContext": {
    "patientId": "123456",
    "patientName": "Juan Pérez",
    "contextChanged": true
  },
  "uploadResults": [
    {
      "success": true,
      "content_type": "image",
      "s3_url": "s3://bucket/123456/20241103_143022_a1b2c3d4_xray.jpg",
      "s3_key": "123456/20241103_143022_a1b2c3d4_xray.jpg",
      "bucket": "ab2-cerozob-rawdata-us-east-1",
      "patient_id": "123456",
      "file_size": 245760,
      "content_hash": "a1b2c3d4e5f6g7h8...",
      "format": "jpeg",
      "block_index": 1
    }
  ],
  "timestamp": "2024-11-03T14:30:22Z",
  "status": "success"
}
```

## Error Handling

### Upload Failures

- Individual file upload failures don't stop agent processing
- Failed uploads are logged and included in response
- Agent continues processing with available content

### Missing Configuration

- If no S3 bucket is configured, uploads are skipped with warning
- If bucket access fails, uploads are disabled
- Agent functionality remains intact without uploads

### Patient Context Issues

- If no patient context is detected, files go to `unknown_patient/` folder
- Files can be reorganized later when patient context becomes available

## Logging

Upload operations are logged with structured events:

```
INFO: ✅ Successfully uploaded 2 files for patient 123456
INFO:    📄 image: s3://bucket/123456/20241103_143022_a1b2c3d4_xray.jpg
INFO:    📄 document: s3://bucket/123456/20241103_143030_i9j0k1l2_lab.pdf
```

## Testing the Workflow

### Test Sequence 1: Image Upload with Patient Context

1. **Send message with patient info and image**:
   ```
   "Aquí está la radiografía de tórax del paciente Juan Pérez, cédula 12345678"
   [Include image attachment]
   ```

2. **Expected behavior**:
   - Agent detects patient context (Juan Pérez, 12345678)
   - Image is uploaded to `s3://bucket/12345678/`
   - Response includes upload results
   - Agent analyzes the image content

### Test Sequence 2: Document Upload

1. **Send message with document**:
   ```
   "Por favor revisa estos resultados de laboratorio del paciente"
   [Include PDF attachment]
   ```

2. **Expected behavior**:
   - Document uploaded to patient-specific folder
   - Agent processes document content
   - Upload results included in response

## Benefits

1. **Automatic Organization**: Files are automatically organized by patient
2. **Persistent Storage**: Content is preserved beyond the conversation
3. **Audit Trail**: Complete metadata and logging for compliance
4. **Deduplication**: Prevents duplicate file storage
5. **Scalable**: Handles multiple files and patients efficiently
