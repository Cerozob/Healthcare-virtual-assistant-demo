# Extraction Lambda Fix Summary

## Issues Fixed

### 1. NameError: 'stored_document_id' is not defined
**Problem**: The extraction lambda was referencing an undefined variable `stored_document_id` in the return statement.

**Root Cause**: The variable was never defined because we're not storing documents in a database - we're organizing them in S3.

**Solution**: Removed the undefined variable from the return statement since document storage is handled by S3 organization.

### 2. Missing Document Classification in Metadata
**Problem**: The lambda was classifying documents but not updating the original document's S3 metadata with classification information.

**Solution**: 
- Added `update_original_document_metadata()` function to update S3 object metadata
- Updates original document with classification category, confidence, and workflow stage
- Uses S3 copy-object with REPLACE metadata directive

### 3. Frontend Not Reading Classification from Metadata
**Problem**: The frontend was not checking S3 object metadata for document classification.

**Solution**:
- Updated `storageService.listFiles()` to optionally fetch S3 object metadata
- Added `HeadObjectCommand` to efficiently fetch metadata without downloading files
- Updated `ConfigurationPage.loadFiles()` to parse classification from metadata
- Displays auto-classification status, confidence, and category from S3 metadata

## Changes Made

### lambdas/document_workflow/extraction/index.py

1. **Removed undefined variable**:
   ```python
   # Before
   'storedDocumentId': stored_document_id,  # ❌ Undefined
   
   # After
   # Removed - not needed since we use S3 organization
   ```

2. **Added metadata update function**:
   ```python
   def update_original_document_metadata(
       document_id: str,
       patient_id: Optional[str],
       classification: Optional[Dict[str, Any]] = None
   ) -> None:
       """Update the original document's S3 metadata with classification."""
       # Updates S3 object metadata with:
       # - document-category
       # - classification-confidence
       # - original-classification
       # - auto-classified
       # - confidence-threshold-met
       # - workflow-stage
       # - classification-timestamp
   ```

3. **Updated organize_processed_data signature**:
   - Added `classification` parameter
   - Includes classification in processed data metadata

4. **Added classification update call**:
   ```python
   # Update original document metadata with classification
   update_original_document_metadata(
       document_id=document_id,
       patient_id=patient_id,
       classification=classification
   )
   ```

### infrastructure/stacks/document_workflow_stack.py

1. **Added SOURCE_BUCKET_NAME environment variable**:
   ```python
   environment={
       "SOURCE_BUCKET_NAME": self.raw_bucket.bucket_name,  # ✅ Added
       "PROCESSED_BUCKET_NAME": self.processed_bucket.bucket_name,
       "KNOWLEDGE_BASE_ID": "healthcare-kb",
       "CLASSIFICATION_CONFIDENCE_THRESHOLD": "80"
   }
   ```

2. **Granted raw bucket permissions**:
   ```python
   # Grant permissions to extraction lambda
   self.raw_bucket.grant_read_write(self.extraction_lambda)  # ✅ Added
   self.processed_bucket.grant_read_write(self.extraction_lambda)
   ```

### apps/frontend/src/services/storageService.ts

1. **Updated FileItem interface**:
   ```typescript
   interface FileItem {
     key: string;
     size?: number;
     lastModified?: Date;
     metadata?: { [key: string]: string };  // ✅ Added
   }
   ```

2. **Enhanced listFiles function**:
   ```typescript
   async listFiles(
     prefix?: string,
     options?: {
       pageSize?: number;
       includeMetadata?: boolean;  // ✅ Added
     }
   ): Promise<FileItem[]>
   ```

3. **Added metadata fetching**:
   - Uses `HeadObjectCommand` to fetch metadata efficiently
   - Only fetches metadata when `includeMetadata: true`
   - Gracefully handles metadata fetch failures

### apps/frontend/src/pages/ConfigurationPage.tsx

1. **Updated loadFiles to fetch metadata**:
   ```typescript
   const s3Files = await storageService.listFiles(undefined, { 
     includeMetadata: true  // ✅ Fetch metadata
   });
   ```

2. **Parse classification from metadata**:
   ```typescript
   const metadata = s3File.metadata || {};
   const category = metadata['document-category'] || 'other';
   const confidence = parseFloat(metadata['classification-confidence'] || '0');
   const autoClassified = metadata['auto-classified'] === 'true';
   const originalClassification = metadata['original-classification'];
   ```

3. **Display classification in UI**:
   - Shows auto-classification badge
   - Displays confidence percentage
   - Shows original classification if different
   - Highlights "not-identified" documents

## Document Classification Flow

1. **Upload**: User uploads document with initial category (or 'auto')
2. **BDA Processing**: Bedrock Data Automation analyzes document
3. **Extraction**: Lambda extracts classification from BDA results
4. **Metadata Update**: Lambda updates original S3 object metadata with classification
5. **Frontend Display**: Frontend reads metadata and displays classification status

## Metadata Fields

The following metadata fields are set on S3 objects:

- `document-category`: Final classification (medical-history, exam-results, etc.)
- `classification-confidence`: Confidence score (0-100)
- `original-classification`: Original BDA classification before threshold check
- `auto-classified`: Whether classification was automatic (true/false)
- `confidence-threshold-met`: Whether confidence exceeded threshold (true/false)
- `workflow-stage`: Current workflow stage (uploaded, classified, etc.)
- `classification-timestamp`: When classification was performed

## Testing Recommendations

1. Upload a document and verify metadata is set correctly
2. Check CloudWatch logs for classification information
3. Verify frontend displays classification from metadata
4. Test with documents that have low confidence (< 80%)
5. Verify "not-identified" documents are highlighted
6. Test metadata update with different document types

## Benefits

1. **No Database Required**: Classification stored directly in S3 metadata
2. **Efficient**: HeadObject is faster than GetObject for metadata
3. **Persistent**: Classification survives lambda restarts
4. **Auditable**: Metadata includes timestamps and confidence scores
5. **Flexible**: Easy to update classification manually if needed
