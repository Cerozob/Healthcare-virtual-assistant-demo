# Amplify Gen2 Secrets Configuration

This document explains how to configure the required secrets for the healthcare frontend application using Amplify Gen2's centralized secrets management.

## Required Secrets

The frontend application requires the following secrets to be configured in the Amplify Console:

### 1. CDK_API_GATEWAY_ENDPOINT

- **Description**: The API Gateway endpoint URL from the CDK-deployed backend
- **Format**: `https://your-api-id.execute-api.region.amazonaws.com/v1`
- **How to get**: From CDK deployment outputs or AWS Console

### 2. CDK_S3_BUCKET_NAME  

- **Description**: The S3 bucket name for file storage from the CDK-deployed backend
- **Format**: `your-bucket-name` (just the bucket name, not ARN)
- **How to get**: From CDK deployment outputs or AWS Console

### 3. AWS_REGION

- **Description**: The AWS region where all resources are deployed
- **Format**: `us-east-1` (standard AWS region format)
- **How to get**: From your CDK deployment configuration

## How to Set Secrets in Amplify Gen2

### Using Amplify Console (Recommended)

1. **Navigate to Amplify Console**
   - Go to [AWS Amplify Console](https://console.aws.amazon.com/amplify/)
   - Select your healthcare frontend app

2. **Access Secrets Management**
   - Click on your app
   - Go to "Hosting" → "Secrets"
   - Click "Manage secrets"

3. **Add Secrets**
   - Click "Add secret"
   - Choose scope: "All branches" or specific branch
   - Add each secret:

   ```text
   Secret key: CDK_API_GATEWAY_ENDPOINT
   Secret value: https://your-api-id.execute-api.us-east-1.amazonaws.com/v1
   ```

   ```text
   Secret key: CDK_S3_BUCKET_NAME
   Secret value: your-s3-bucket-name
   ```

   ```text
   Secret key: AWS_REGION
   Secret value: us-east-1
   ```

4. **Save and Redeploy**
   - Click "Save"
   - Trigger a new deployment for changes to take effect

### Using Amplify CLI (Local Development)

For local development with sandbox, you can set secrets using:

```bash
# Set secrets for local sandbox
npx ampx sandbox secret set CDK_API_GATEWAY_ENDPOINT
npx ampx sandbox secret set CDK_S3_BUCKET_NAME  
npx ampx sandbox secret set AWS_REGION
```

You'll be prompted to enter the secret values interactively.

## Getting CDK Resource Values

### Get API Gateway Endpoint

```bash
# From CDK stack outputs
aws cloudformation describe-stacks \
  --stack-name AWSomeBuilder2-ApiStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text
```

### Get S3 Bucket Name

```bash
# From CDK stack outputs (if exported)
aws cloudformation describe-stacks \
  --stack-name AWSomeBuilder2-DocumentWorkflowStack \
  --query 'Stacks[0].Outputs[?OutputKey==`BucketName`].OutputValue' \
  --output text

# Or list S3 buckets and find the healthcare one
aws s3 ls | grep healthcare
```

## How Secrets Work in Gen2

### Storage Location

Secrets are automatically stored in AWS Systems Manager Parameter Store:

- **All branches**: `/amplify/shared/<app-id>/<secret-key>`
- **Specific branch**: `/amplify/<app-id>/<branch-name>-branch-<hash>/<secret-key>`

### Access in Code

Secrets are accessed using the `secret()` function in your backend code:

```typescript
import { secret } from '@aws-amplify/backend';

const apiEndpoint = secret('CDK_API_GATEWAY_ENDPOINT');
const bucketName = secret('CDK_S3_BUCKET_NAME');
const region = secret('AWS_REGION');
```

### Runtime Resolution

- **Build time**: Amplify resolves secrets and populates `amplify_outputs.json`
- **Runtime**: Frontend reads resolved values from outputs
- **Environment-specific**: Different secrets per branch/environment

## Verification

After setting the secrets, you can verify they're working by:

1. **Check Amplify Build Logs**
   - Look for the configuration messages in the build logs
   - Should show the actual values being used (secrets are masked)

2. **Check Browser Console**
   - Open the deployed app
   - Check browser console for configuration messages
   - Should show the real API endpoint and bucket name

3. **Test Functionality**
   - Try logging in (auth should work)
   - Try uploading a file (storage should work)
   - Try making API calls (API should work)

4. **Check Parameter Store**
   - Go to AWS Systems Manager → Parameter Store
   - Look for parameters under `/amplify/` prefix
   - Verify your secrets are stored there

## Troubleshooting

### Secret Not Found Error

- Verify secret names match exactly: `CDK_API_GATEWAY_ENDPOINT`, `CDK_S3_BUCKET_NAME`, `AWS_REGION`
- Check that secrets are set for the correct branch
- Ensure you've triggered a new deployment after adding secrets
- Check Parameter Store in AWS Console for the actual parameter names

### Invalid Values

- Verify API Gateway URL format includes `/v1` path
- Verify S3 bucket name is just the name, not the full ARN
- Check that the resources exist in the same AWS region

### Permission Issues

- Ensure Amplify service role has permissions to access Parameter Store
- Check that the CDK resources are deployed and accessible
- Verify IAM permissions for the Amplify app

### Local Development Issues

- Use `npx ampx sandbox secret list` to see available secrets
- Use `npx ampx sandbox secret remove <key>` to remove incorrect secrets
- Secrets set locally don't appear in Amplify Console

## Security Notes

- Secrets are encrypted at rest in Parameter Store
- Secrets are only accessible during build time and runtime
- Never commit actual secret values to version control
- Use different secrets for different environments (dev/staging/prod)
- Secrets are automatically masked in build logs
- No `team-provider-info.json` file needed in Gen2

## Migration from Gen1

If migrating from Amplify Gen1:

1. Remove `team-provider-info.json` file
2. Remove environment variables from Amplify Console
3. Set secrets using the new Gen2 approach
4. Update backend code to use `secret()` function
5. Remove any local `.env` files (not needed)
