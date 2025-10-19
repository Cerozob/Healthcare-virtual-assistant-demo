# Healthcare System Deployment Workflow

This document outlines the complete deployment process for the healthcare management system.

## Architecture Overview

- **Backend**: Deployed via AWS CDK (API Gateway, Lambda, RDS, etc.)
- **Frontend**: Deployed via Amplify CLI (React SPA)

## Prerequisites

1. **AWS CLI** configured with appropriate permissions
2. **Node.js** 18+ installed
3. **AWS CDK** installed: `npm install -g aws-cdk`
4. **Amplify CLI** installed: `npm install -g @aws-amplify/cli`

## Deployment Steps

### 1. Deploy Backend Infrastructure (CDK)

```bash
# Install dependencies
npm install

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy all backend stacks
cdk deploy --all
```

This deploys:
- ✅ API Stack (API Gateway + Lambda functions)
- ✅ Backend Stack (RDS database)
- ✅ Document Processing Stack (S3 + processing)
- ✅ Virtual Assistant Stack (Bedrock integration)

### 2. Deploy Frontend (Amplify CLI)

```bash
# Navigate to frontend
cd apps/frontend

# Install dependencies
npm install

# Initialize Amplify (first time only)
amplify init

# Get API Gateway URL from CDK outputs
API_URL=$(aws cloudformation describe-stacks \
  --stack-name AWSomeBuilder2-ApiStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

# Set environment variables
amplify env set VITE_API_BASE_URL "$API_URL"
amplify env set VITE_AWS_REGION "us-east-1"

# Deploy frontend
amplify publish
```

### 3. Verify Deployment

1. **Backend**: Check API Gateway endpoint works
   ```bash
   curl $API_URL/config
   ```

2. **Frontend**: Visit the Amplify URL and verify:
   - ✅ App loads without errors
   - ✅ Configuration loads from API
   - ✅ API calls work correctly

## Configuration Management

### Environment Variables

The frontend uses these environment variables:

- `VITE_API_BASE_URL`: API Gateway endpoint URL
- `VITE_AWS_REGION`: AWS region (default: us-east-1)

### Configuration Loading

The frontend loads configuration in this order:
1. **API Config Endpoint**: `GET /config` (primary)
2. **Environment Variables**: `VITE_API_BASE_URL` (fallback)
3. **Localhost**: `http://localhost:3000/v1` (development)

## Development Workflow

### Local Development

```bash
# Start backend (if running locally)
cd lambdas/api
python -m http.server 3000

# Start frontend
cd apps/frontend
npm run dev
```

### Testing Changes

```bash
# Test backend changes
cdk diff
cdk deploy ApiStack

# Test frontend changes
cd apps/frontend
npm run build
amplify publish
```

## Environment Management

### Multiple Environments

```bash
# Create staging environment
amplify env add staging

# Deploy to staging
amplify env checkout staging
amplify env set VITE_API_BASE_URL "https://staging-api-url/v1"
amplify publish

# Switch back to production
amplify env checkout prod
```

### CI/CD Setup

1. **Backend CI/CD**: Use AWS CodePipeline with CDK
2. **Frontend CI/CD**: Connect Git repo to Amplify Console

## Troubleshooting

### Common Issues

1. **CDK Bootstrap Error**
   ```bash
   cdk bootstrap aws://ACCOUNT-NUMBER/REGION
   ```

2. **API Gateway URL Not Found**
   - Check CloudFormation outputs in AWS Console
   - Verify API stack deployed successfully

3. **Frontend Build Errors**
   ```bash
   cd apps/frontend
   npm run clean
   npm ci
   npm run build
   ```

4. **Configuration Not Loading**
   - Check browser network tab for API calls
   - Verify environment variables in Amplify console
   - Check `/config` endpoint directly

### Logs and Monitoring

- **Lambda Logs**: CloudWatch Logs
- **API Gateway Logs**: CloudWatch Logs  
- **Frontend Logs**: Browser console + Amplify console
- **Build Logs**: Amplify console build history

## Security Considerations

- API endpoints use CORS for browser access
- Environment variables are injected at build time
- No sensitive credentials in frontend code
- IAM roles provide least-privilege access

## Cost Optimization

- Lambda functions use appropriate memory/timeout settings
- API Gateway uses HTTP API (cheaper than REST API)
- Amplify hosting includes CDN and SSL
- RDS uses appropriate instance sizing
