# Fix S3 Upload Issue - Custom Bucket Solution

## Problem
You're getting a "SignatureDoesNotMatch" error when uploading files to S3. This is caused by authentication/authorization issues between Amplify and your custom S3 bucket.

## Root Cause
1. The storage service was trying to use custom bucket configuration that conflicts with Amplify's authentication
2. The App component was overriding the storage configuration incorrectly
3. Amplify secrets might not be properly configured for your custom bucket

## Changes Made

### 1. Created Proper Storage Resource (`apps/frontend/amplify/storage/resource.ts`)
- **NEW FILE**: Defines default Amplify storage with proper access patterns
- Configures access for both authenticated and guest users
- Sets up proper path-based permissions for `patients/*` and `public/*`

### 2. Fixed Amplify Backend Configuration (`apps/frontend/amplify/backend.ts`)
- **Uses proper Amplify Gen 2 approach** with `defineStorage`
- Imports your existing CDK bucket using `Bucket.fromBucketName`
- Creates IAM policies for both authenticated and unauthenticated users (guest access)
- Attaches policies to both user roles for comprehensive access

### 3. Updated Storage Service (`apps/frontend/src/services/storageService.ts`)
- **All methods now use custom bucket configuration**
- Passes `bucket: { bucketName, region }` to all Amplify Storage APIs
- Maintains consistent bucket usage across upload, download, delete, and list operations

### 4. Simplified App Configuration (`apps/frontend/src/app.tsx`)
- Removed storage configuration override
- Uses default Amplify configuration with custom bucket access via API parameters

## Critical: Configure Environment Variables

**This is the most important step** - you need to ensure your environment variables match your custom bucket:

### Option 1: Update .env files (Recommended)
```bash
cd apps/frontend

# Update .env file
echo "VITE_S3_BUCKET_NAME=ab2-cerozob-rawdata-us-east-1" >> .env
echo "VITE_AWS_REGION=us-east-1" >> .env
echo "VITE_API_BASE_URL=https://your-api-endpoint.com" >> .env

# Update .env.local if it exists
echo "VITE_S3_BUCKET_NAME=ab2-cerozob-rawdata-us-east-1" >> .env.local
echo "VITE_AWS_REGION=us-east-1" >> .env.local
```

### Option 2: Configure Amplify Secrets (Optional)
```bash
# These are available in amplify_outputs.json custom section but not required for basic functionality
npx amplify sandbox secret set CDK_S3_BUCKET_NAME ab2-cerozob-rawdata-us-east-1
npx amplify sandbox secret set AWS_REGION us-east-1
npx amplify sandbox secret set CDK_API_GATEWAY_ENDPOINT https://your-api-endpoint.com
```

## Deployment Steps

1. **Verify Environment Variables:**
   ```bash
   cd apps/frontend
   cat .env | grep VITE_S3_BUCKET_NAME
   cat .env | grep VITE_AWS_REGION
   ```

2. **Deploy Amplify Backend:**
   ```bash
   npx amplify sandbox delete  # Clean up existing sandbox
   npx amplify sandbox  # Deploy with new configuration
   ```

3. **Verify Configuration:**
   - Check that your environment variables are correctly set
   - The IAM policies now use wildcard patterns to support different bucket names

## Verification Steps

1. **Check Bucket Exists:**
   ```bash
   aws s3 ls s3://ab2-cerozob-rawdata-us-east-1
   ```

2. **Verify Amplify Outputs:**
   ```bash
   cat apps/frontend/amplify_outputs.json | jq '.storage'
   ```

3. **Test Upload:**
   - Try uploading a file again
   - Check browser console for authentication details

## Why This Works with Custom Buckets

- **Flexible Configuration**: Uses secrets so you can change bucket names without code changes
- **Proper IAM Policies**: References the actual bucket ARN from the imported bucket
- **Amplify Integration**: Maintains full compatibility with Amplify's authentication system
- **Environment Agnostic**: Works across different environments with different bucket names

## Expected Result
After configuring the secrets and redeploying, your file uploads should work correctly with your custom bucket and the SignatureDoesNotMatch error should be resolved.
