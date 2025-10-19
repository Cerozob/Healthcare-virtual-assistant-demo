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

### Step 3: Initialize Amplify (First Time Only)
```bash
cd apps/frontend
amplify init
```

Follow the prompts:
- **Project name**: `healthcare-frontend`
- **Environment name**: `prod`
- **Default editor**: Your preferred editor
- **App type**: `javascript`
- **Framework**: `react`
- **Source directory**: `src`
- **Build directory**: `dist`
- **Build command**: `npm run build`
- **Start command**: `npm run dev`

### Step 4: Set Environment Variables
```bash
# Set the API Gateway URL (replace with your actual URL)
amplify env set VITE_API_BASE_URL "https://your-api-gateway-url/v1"
amplify env set VITE_AWS_REGION "us-east-1"
```

### Step 5: Deploy Frontend
```bash
amplify publish
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
