# Frontend Deployment Guide

This guide explains how to deploy the healthcare frontend using Amplify CLI after deploying the CDK backend.

## Prerequisites

1. **AWS CLI** configured with appropriate permissions
2. **Amplify CLI** installed globally:
   ```bash
   npm install -g @aws-amplify/cli
   ```
3. **CDK backend** deployed (API stack must be deployed first)

## Deployment Workflow

### Step 1: Deploy CDK Backend
```bash
# From project root
cdk deploy --all
```

### Step 2: Get API Gateway URL
After CDK deployment, get the API Gateway URL:
```bash
aws cloudformation describe-stacks \
  --stack-name AWSomeBuilder2-ApiStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text
```

### Step 3: Initialize Amplify Gen2 (First Time Only)
```bash
cd apps/frontend

# Install dependencies
npm install

# Start the sandbox environment
npx ampx sandbox
```

This will:
- Deploy Cognito User Pool and Identity Pool for authentication
- Generate `amplify_outputs.json` with configuration
- Create local secrets in Parameter Store (for sandbox only)

**Note**: For local development, you can set secrets using:
```bash
npx ampx sandbox secret set CDK_API_GATEWAY_ENDPOINT
npx ampx sandbox secret set CDK_S3_BUCKET_NAME
npx ampx sandbox secret set AWS_REGION
```

### Step 4: Configure Secrets for CDK Resources
After the sandbox is running, you need to configure secrets in the Amplify Console:

1. **Get CDK Resource Values**:
   ```bash
   # Get API Gateway endpoint
   API_ENDPOINT=$(aws cloudformation describe-stacks \
     --stack-name AWSomeBuilder2-ApiStack \
     --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
     --output text)
   
   # Get S3 bucket name (adjust stack name as needed)
   BUCKET_NAME=$(aws s3 ls | grep healthcare | awk '{print $3}')
   
   echo "API Endpoint: $API_ENDPOINT"
   echo "S3 Bucket: $BUCKET_NAME"
   ```

2. **Set Secrets in Amplify Console** (Gen2 approach):
   - Go to [Amplify Console](https://console.aws.amazon.com/amplify/)
   - Select your app → Hosting → Secrets → Manage secrets
   - Add these secrets:
     - `CDK_API_GATEWAY_ENDPOINT`: `https://your-api-id.execute-api.us-east-1.amazonaws.com/v1`
     - `CDK_S3_BUCKET_NAME`: `your-s3-bucket-name`
     - `AWS_REGION`: `us-east-1`

   See [AMPLIFY_SECRETS.md](./AMPLIFY_SECRETS.md) for detailed instructions.

### Step 5: Deploy to Production
```bash
# Deploy the Amplify backend
npx ampx deploy --branch main

# Or use Amplify Console for CI/CD
```

## Environment Management

### Production Environment
```bash
amplify env checkout prod
amplify env set VITE_API_BASE_URL "https://prod-api-gateway-url/v1"
amplify publish
```

### Staging Environment
```bash
amplify env add staging
amplify env set VITE_API_BASE_URL "https://staging-api-gateway-url/v1"
amplify publish
```

## Configuration

The frontend will:
1. **Try to fetch config** from `${VITE_API_BASE_URL}/config` endpoint
2. **Fall back to environment variable** if config endpoint fails
3. **Use localhost** for development if no environment variables set

## Troubleshooting

### API Gateway URL Not Found
If you can't get the API Gateway URL from CDK outputs:
1. Check that the API stack deployed successfully
2. Look in the AWS Console → CloudFormation → AWSomeBuilder2-ApiStack → Outputs
3. Or check API Gateway console for the endpoint URL

### Environment Variables Not Working
1. Verify variables are set: `amplify env get --name prod`
2. Check the Amplify console → App Settings → Environment Variables
3. Redeploy: `amplify publish`

### Build Failures
1. Check Node.js version (should be 18+)
2. Clear cache: `npm run clean && npm ci`
3. Check build locally: `npm run build`

## Automated Deployment Script

Use the provided script for easier deployment:
```bash
# From project root
chmod +x scripts/deploy-frontend.sh
./scripts/deploy-frontend.sh
```

This script will:
1. Get the API Gateway URL from CDK outputs
2. Initialize Amplify if needed
3. Set environment variables
4. Deploy the frontend

## CI/CD Setup

To set up continuous deployment:
1. Connect your Git repository in Amplify console
2. Configure build settings to use `apps/frontend/amplify.yml`
3. Set environment variables in Amplify console
4. Enable auto-deployment on push to main branch
