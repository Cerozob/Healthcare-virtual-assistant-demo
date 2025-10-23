# Sample Data Loading Guide

This document explains how to load sample healthcare data into the system after deployment.

## Overview

The sample data loading process has been separated from the database initialization to avoid timeout issues. The process now works in two stages:

1. **Database Initialization** (automatic during deployment)
   - Creates database schema and tables only
   - No sample data loaded at all
   - Completes quickly within Lambda timeout limits

2. **Sample Data Loading** (manual trigger after deployment)
   - Loads patient profiles from S3 into the database
   - Loads basic sample data (medics and exams)
   - Fast and lightweight (JSON data only)

3. **Document Upload** (optional, manual)
   - Upload sample PDFs and images to raw bucket
   - Triggers document workflow for processing
   - Separate from database loading for flexibility

## Architecture Changes

### Before (Problematic)
```
S3 Deployment → Database Init Lambda (900s timeout)
                ├── Create schema
                ├── Load ALL sample data (37MB+)
                └── ❌ TIMEOUT
```

### After (Optimized)
```
S3 Deployment → Database Init Lambda (fast)
                └── Create schema only (no data)

Manual Trigger → Data Loader Lambda (15min timeout)
                ├── Load patient profiles to database
                ├── Load basic sample data (medics, exams)
                └── Upload files to raw bucket → Document Workflow
```

## How to Load Sample Data

### Method 1: Using the Unified Script (Recommended)

```bash
# Load both database data and documents
python scripts/load_sample_data.py

# Or load only database data (skip documents)
python scripts/load_sample_data.py --skip-documents

# Or upload only documents (if data already loaded)
python scripts/load_sample_data.py --documents-only
```

This script will:
- ✅ Check prerequisites (AWS access, buckets, etc.)
- 🔍 Find the data loader Lambda function automatically
- 📥 Trigger the database data loading process
- 📄 Upload sample documents to the raw bucket
- 📊 Show progress and results for both steps

### Method 2: Using AWS CLI

```bash
# Get the function name from CloudFormation outputs
FUNCTION_NAME=$(aws cloudformation describe-stacks \
  --stack-name <your-backend-stack-name> \
  --query 'Stacks[0].Outputs[?OutputKey==`DataLoaderFunctionName`].OutputValue' \
  --output text)

# Invoke the function
aws lambda invoke \
  --function-name $FUNCTION_NAME \
  --payload '{}' \
  response.json

# Check the result
cat response.json
```

### Method 3: Using AWS Console

1. Go to AWS Lambda console
2. Find the function named like `<stack-name>-DataLoaderFunction-<random>`
3. Click "Test" and create a new test event (empty JSON: `{}`)
4. Execute the test and check the results

## What Gets Loaded

### Database Records
- **Patient profiles**: ~20 patient records with personal information, medical history, lab results
- **Medics**: 3 sample healthcare providers (Dr. Wilson, Dr. Brown, Dr. Davis)
- **Exams**: 4 sample medical examinations (X-Ray, ECG, Blood Test, Physical Exam)

### Raw Bucket Files
- **PDFs**: Medical records, prescriptions, lab results (~60 files)
- **Images**: Reference scans and medical images (~20 files)

**Note**: These files are uploaded by the main data loading script. If you need to upload them separately:
```bash
python scripts/load_sample_data.py --documents-only
```

Once uploaded, files are automatically processed by the document workflow system.

## Monitoring and Troubleshooting

### Check Lambda Logs
```bash
# View recent logs
aws logs tail /aws/lambda/<function-name> --follow
```

### Verify Database Content
```sql
-- Check loaded patients
SELECT COUNT(*) FROM patients;
SELECT full_name, email FROM patients LIMIT 5;

-- Check medics and exams
SELECT COUNT(*) FROM medics;
SELECT COUNT(*) FROM exams;
```

### Verify Raw Bucket Content
```bash
# List files in raw bucket
aws s3 ls s3://ab2-cerozob-rawdata-<region>/patients/ --recursive
```

## Configuration

The data loader function uses these environment variables:

- `SAMPLE_DATA_BUCKET`: Source bucket with sample data
- `DATABASE_CLUSTER_ARN`: Aurora cluster ARN
- `DATABASE_SECRET_ARN`: Database credentials secret ARN
- `DATABASE_NAME`: Database name (default: healthcare)

Raw bucket location is retrieved from SSM parameter: `/healthcare/document-workflow/raw-bucket`

## Performance Notes

- **DB Init**: 5 minutes timeout, 256 MB memory (schema creation only)
- **Data Loader**: 15 minutes timeout, 1024 MB memory (data processing)
- **Batch processing**: Processes patients one by one to avoid memory issues
- **Error handling**: Continues processing even if individual patients fail

## Expected Results

After successful data loading:

- ✅ ~20 patient records in the database
- ✅ ~60+ PDF files in the raw bucket
- ✅ ~20+ image files in the raw bucket
- ✅ Document workflow automatically triggered for uploaded files
- ✅ Processed documents appear in the processed bucket

## Troubleshooting Common Issues

### "Function not found"
- Ensure the backend stack is deployed successfully
- Check CloudFormation outputs for the correct function name

### "Access denied to S3 bucket"
- Verify the sample data bucket exists and is accessible
- Check IAM permissions for the Lambda function

### "Database connection failed"
- Ensure the Aurora cluster is running (may need to resume from auto-pause)
- Verify the database secret is accessible

### "Partial data loading"
- Check Lambda logs for specific patient processing errors
- Some patients may fail while others succeed (this is expected behavior)

## Next Steps

After loading sample data:

1. **Test the API**: Use the healthcare API to query patient data
2. **Check document processing**: Verify that uploaded files are being processed
3. **Test the chat interface**: Use the frontend to interact with the loaded data
4. **Monitor workflows**: Check that the document classification workflow is working

For more information, see:
- [API Documentation](api/README.md)
- [Document Workflow Guide](DOCUMENT_WORKFLOW.md)
- [Frontend Setup](../apps/frontend/README.md)
