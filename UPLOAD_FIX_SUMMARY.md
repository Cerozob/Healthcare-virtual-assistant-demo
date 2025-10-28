# File Upload Permission and Path Structure Fix

## Issues Fixed

### 1. S3 Permission Denied Error
**Problem**: Chat window file uploads were failing with `AccessDenied` error because the IAM policy only allowed uploads to `patients/*` and `public/*` paths.

**Solution**: Updated Amplify backend IAM policy to allow uploads to all paths in the raw bucket for authenticated users.

**File Changed**: `apps/frontend/amplify/backend.ts`
- Changed from restrictive path patterns (`patients/*`, `public/*`) to `/*` (all paths)
- Removed unnecessary prefix conditions from ListBucket permission

### 2. Incorrect S3 Path Structure
**Problem**: Both ChatPage and ConfigurationPage were using a complex nested path structure that didn't match the expected BDA workflow structure.

**Incorrect Structure**: `{patient_id}/{category}/{timestamp}/{fileId}/{filename}`

**Correct Structure**: `{patient_id}/{filename}` (simple, flat structure)

**Rationale**: 
- BDA trigger lambda expects: `s3://raw-bucket/{patient_id}/{filename}`
- BDA outputs to: `s3://processed-bucket/processed/{patient_id}/{filename}/{job_id}/...`
- Extraction lambda parses patient_id from first path segment
- Sample data follows this simple structure

**Files Changed**:
- `apps/frontend/src/pages/ChatPage.tsx`
- `apps/frontend/src/pages/ConfigurationPage.tsx`

### 3. Missing Drag-and-Drop Functionality
**Problem**: Chat window didn't support drag-and-drop file uploads.

**Solution**: Replaced FileInput icon button with proper FileUpload component that has built-in drag-and-drop support.

**File Changed**: `apps/frontend/src/pages/ChatPage.tsx`
- Replaced `FileInput` (icon button) with `FileUpload` component
- Added `constraintText` property to make drag-and-drop zone always visible
- Uses same component as Configuration page for consistent UX
- Built-in visual feedback and drag-and-drop zone
- Files can be dragged directly into the upload area or selected via button

## Deployment Steps

### 1. Deploy Amplify Backend Changes
```bash
cd apps/frontend
npx ampx sandbox --once
```

This will update the IAM policies for authenticated users to allow S3 uploads to all paths.

### 2. Deploy Frontend Changes
The frontend changes will be automatically deployed when you push to your Amplify-connected branch, or you can build locally:

```bash
cd apps/frontend
npm run build
```

## Testing

1. **Test Chat Upload**:
   - Select a patient in the chat sidebar
   - Attach a file using the file button or drag-and-drop
   - Send the message
   - Verify file uploads to `s3://ab2-cerozob-rawdata-us-east-1/{patient_id}/{filename}`

2. **Test Configuration Page Upload**:
   - Go to Configuration page
   - Select a patient
   - Upload a file
   - Verify same path structure

3. **Test Drag-and-Drop**:
   - Drag a file into the chat window
   - Verify it appears in the file list
   - Send and verify upload

## Expected Behavior

1. Files upload to: `{patient_id}/{filename}`
2. BDA processes and outputs to: `processed/{patient_id}/{filename}/{job_id}/...`
3. Extraction lambda correctly parses patient_id from path
4. Knowledge base ingestion works automatically
5. No more AccessDenied errors

## Notes

- The simplified path structure matches the sample data structure
- Metadata still includes category information for classification
- BDA will auto-classify documents regardless of upload path
- The processed bucket maintains the full workflow structure
