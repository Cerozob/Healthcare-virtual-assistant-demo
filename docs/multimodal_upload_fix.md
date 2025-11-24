# Multimodal Upload Fix - Lambda-Only Approach

## Problem Summary

The healthcare agent was using two different mechanisms to upload files:

1. **Lambda-based upload** (via `healthcare-files-api___files_api` tool) ✅ - Works correctly with proper IAM permissions
2. **Direct S3 upload** (via `multimodal_uploader.py`) ❌ - Fails with AccessDenied errors

The agent would successfully upload files via the Lambda tool, but then attempt to upload them again using the direct S3 uploader, which failed because the agent runtime role doesn't have S3 write permissions.

## Root Cause

The agent runtime role (`HealthcareAssistantRuntimeRole`) intentionally does not have direct S3 write permissions. All file operations should go through the Lambda API which:
- Has proper IAM permissions
- Handles file organization and classification
- Integrates with the document workflow pipeline
- Triggers BDA processing and Knowledge Base ingestion

## Changes Made

### 1. Removed Direct S3 Upload Logic

**File: `agents/healthcare_agent.py`**

- Removed `multimodal_uploader` initialization
- Removed `_setup_multimodal_uploader()` method
- Simplified `_upload_multimodal_content()` to only log multimodal content detection
- Removed import of `multimodal_uploader` module

The agent now relies exclusively on the Lambda-based file upload tool.

### 2. Removed Multimodal Uploader Module

**File: `agents/tools/multimodal_uploader.py`** - DELETED

The entire module was removed since:
- It's not needed - file uploads are handled by the Lambda API
- The agent runtime doesn't have direct S3 permissions by design
- Keeping it would only cause confusion

## How File Uploads Work Now

### Upload Flow

1. **User sends file** → Frontend converts to base64 and sends to agent
2. **Agent receives multimodal content** → Detects images/documents in content blocks
3. **Agent calls Lambda tool** → Uses `healthcare-files-api___files_api` with action "upload"
4. **Lambda processes upload** → Creates S3 key, stores metadata, returns file info
5. **Document workflow triggers** → BDA processes file, extracts data, classifies
6. **Knowledge Base ingestion** → Processed data synced to Knowledge Base

### Lambda Upload Tool

The `healthcare-files-api___files_api` tool handles:
- File upload initiation
- S3 path generation following document workflow guidelines
- Metadata creation for BDA processing
- Integration with document workflow pipeline

**Example Lambda Response:**
```json
{
  "file_id": "dce3b741-a850-4739-84a3-79d91ef2c846",
  "patient_id": "1d621da0-f89e-4691-8f56-5022bb20dcca",
  "s3_uri": "s3://ab2-cerozob-rawdata-us-east-1/1d621da0-f89e-4691-8f56-5022bb20dcca/exam-results/dce3b741-a850-4739-84a3-79d91ef2c846/file.pdf",
  "category": "exam-results",
  "workflow_stage": "uploaded",
  "next_stage": "BDA processing and classification"
}
```

## File Organization Structure

### Raw Bucket (Upload Location)
```
{patient_id}/{category}/{file_id}/{filename}
```

Example:
```
1d621da0-f89e-4691-8f56-5022bb20dcca/
  exam-results/
    dce3b741-a850-4739-84a3-79d91ef2c846/
      lab_report.pdf
```

### Processed Bucket (After BDA)
```
processed/{patient_id}/{clean_filename}/
  extracted_data.json
  metadata.json
```

Example:
```
processed/1d621da0-f89e-4691-8f56-5022bb20dcca/lab_report/
  extracted_data.json
  metadata.json
```

## Document Cleanup Behavior

The system has a cleanup Lambda (`lambdas/document_workflow/cleanup/index.py`) that:

1. **Triggers on S3 deletion events** (EventBridge)
2. **Cascades deletions** between raw and processed buckets
3. **Matches files** by patient ID and filename

### When Files Get Deleted

- **Manual deletion** → User deletes file from S3
- **Cascade deletion** → Cleanup Lambda deletes related files in other bucket
- **Workflow cleanup** → BDA output cleanup after processing

### Important Notes

- The cleanup Lambda does NOT automatically delete existing files
- It only triggers when a file is explicitly deleted
- Files uploaded via the Lambda tool should remain in S3 unless manually deleted

## Investigating File Disappearance

If files are disappearing from the patient directory, check:

### 1. CloudWatch Logs - Cleanup Lambda
```bash
# Search for deletion events
aws logs filter-log-events \
  --log-group-name /aws/lambda/AWSomeBuilder2-DocumentWorkflow-Cleanup \
  --filter-pattern "Processing deletion" \
  --start-time $(date -u -d '1 hour ago' +%s)000
```

### 2. S3 Event History
```bash
# Check S3 access logs or CloudTrail for DeleteObject events
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=DeleteObject \
  --max-results 50
```

### 3. Document Workflow Logs
```bash
# Check BDA extraction Lambda for cleanup operations
aws logs filter-log-events \
  --log-group-name /aws/lambda/AWSomeBuilder2-DocumentWorkflow-Extraction \
  --filter-pattern "cleanup" \
  --start-time $(date -u -d '1 hour ago' +%s)000
```

### 4. Verify Files in S3
```bash
# List files for a specific patient
aws s3 ls s3://ab2-cerozob-rawdata-us-east-1/1d621da0-f89e-4691-8f56-5022bb20dcca/ --recursive
```

## Testing the Fix

### 1. Upload a File via Agent
```
User: "Subir archivo médico para paciente ID 1d621da0-f89e-4691-8f56-5022bb20dcca"
[Attach file]
```

### 2. Check Agent Logs
Look for:
- ✅ Lambda tool call success
- ✅ No multimodal uploader errors
- ✅ File upload confirmation

### 3. Verify S3 Storage
```bash
# Check raw bucket
aws s3 ls s3://ab2-cerozob-rawdata-us-east-1/1d621da0-f89e-4691-8f56-5022bb20dcca/ --recursive

# Wait 2-5 minutes for BDA processing

# Check processed bucket
aws s3 ls s3://ab2-cerozob-processeddata-us-east-1/processed/1d621da0-f89e-4691-8f56-5022bb20dcca/ --recursive
```

### 4. Verify Knowledge Base
Query the Knowledge Base to confirm the file is indexed and searchable.

## Expected Behavior After Fix

1. **No AccessDenied errors** - Agent doesn't try direct S3 upload
2. **Single upload path** - Only Lambda tool is used
3. **Proper file organization** - Files follow document workflow structure
4. **Successful processing** - BDA and Knowledge Base integration work
5. **Files persist** - No unexpected deletions

## Rollback Plan

If issues occur and you need to restore direct S3 upload capability (not recommended):

1. Restore `agents/tools/multimodal_uploader.py` from git history
2. Restore the import in `healthcare_agent.py`
3. Restore `_setup_multimodal_uploader()` call
4. Add S3 write permissions to agent runtime role
5. Update `_upload_multimodal_content()` to use uploader

**Note:** This is not recommended as it bypasses the document workflow pipeline and requires additional IAM permissions.

## Related Files

- `agents/healthcare_agent.py` - Main agent logic (modified)
- `agents/tools/multimodal_uploader.py` - DELETED (no longer needed)
- `lambdas/api/files/handler.py` - Lambda-based file upload API
- `lambdas/document_workflow/cleanup/index.py` - Cleanup Lambda
- `lambdas/document_workflow/extraction/index.py` - BDA processing Lambda

## Next Steps

1. Deploy the updated agent code
2. Test file uploads with the agent
3. Monitor CloudWatch logs for any errors
4. Verify files persist in S3
5. Check Knowledge Base integration
6. If files are still disappearing, investigate cleanup Lambda triggers
