# Healthcare Management System

A comprehensive healthcare management system built with AWS services, featuring a React frontend and serverless backend.

## Architecture

### Backend (AWS CDK)
- **API Gateway**: HTTP API for all backend services
- **Lambda Functions**: Serverless compute for business logic
- **RDS**: PostgreSQL database for data persistence
- **S3**: Document storage and processing
- **Bedrock**: AI/ML capabilities for virtual assistant

### Frontend (Amplify CLI)
- **React SPA**: Modern single-page application
- **Cloudscape Design**: AWS design system components
- **Amplify Hosting**: CDN, SSL, and global distribution

## Project Structure

```
├── apps/
│   └── frontend/           # React frontend application
├── infrastructure/
│   ├── stacks/            # CDK stack definitions
│   └── constructs/        # Reusable CDK constructs
├── lambdas/
│   └── api/               # Lambda function code
├── config/                # Configuration files
└── scripts/               # Deployment scripts
```

## Quick Start

### Prerequisites
- AWS CLI configured
- Node.js 18+
- AWS CDK: `npm install -g aws-cdk`
- Amplify CLI: `npm install -g @aws-amplify/cli`

### 1. Deploy Backend
```bash
# Install dependencies
npm install

# Deploy CDK stacks
cdk deploy --all
```

### 2. Deploy Frontend
```bash
# Navigate to frontend
cd apps/frontend

# Follow Amplify deployment guide
# See: apps/frontend/DEPLOYMENT.md
```

## Features

### Healthcare Management
- **Patient Management**: CRUD operations for patient records
- **Medical Staff**: Doctor and nurse management
- **Appointments**: Scheduling and reservation system
- **Medical Exams**: Test results and medical history

### Document Processing
- **Upload & Storage**: Secure document handling
- **Processing Pipeline**: Automated document analysis
- **Integration**: Seamless workflow integration

### Virtual Assistant
- **AI Chat**: Bedrock-powered conversational AI
- **Context Awareness**: Healthcare domain knowledge
- **Multi-modal**: Text and document understanding

## Configuration

### Backend Configuration
Edit `config/config.json` to enable/disable features:
```json
{
  "enableBackend": true,
  "enableApi": true,
  "enableDocumentProcessing": true,
  "enableVirtualAssistant": false
}
```

### Frontend Configuration
The frontend uses hardcoded configuration values for demo/development purposes:

**Current Configuration** (in `apps/frontend/src/services/configService.ts`):
- **API Endpoint**: `https://pg5pv01t3j.execute-api.us-east-1.amazonaws.com/v1`
- **S3 Bucket**: `ab2-cerozob-rawdata-us-east-1`
- **Region**: `us-east-1`

**To Update Configuration**:
1. Deploy your CDK infrastructure to get new endpoints
2. Update the hardcoded values in `configService.ts`
3. Redeploy the frontend

**Note**: For production deployments, consider using environment variables or AWS Parameter Store instead of hardcoded values.

## Development

### Local Backend Development
```bash
# Start local API server (if needed)
cd lambdas/api
python -m http.server 3000
```

### Local Frontend Development
```bash
cd apps/frontend
npm install
npm run dev
```

## Deployment

See [DEPLOYMENT_WORKFLOW.md](./DEPLOYMENT_WORKFLOW.md) for complete deployment instructions.

### Quick Deployment
```bash
# 1. Deploy backend
cdk deploy --all

# 2. Deploy frontend
cd apps/frontend
amplify init
amplify publish
```

## Environment Management

### Multiple Environments
```bash
# Backend environments via CDK
cdk deploy --profile staging

# Frontend environments via Amplify
amplify env add staging
amplify env checkout staging
```

## Security

- **IAM Roles**: Least-privilege access patterns
- **CORS**: Properly configured for browser access
- **Environment Variables**: Secure configuration management
- **No Hardcoded Secrets**: All sensitive data via AWS services

## Monitoring & Logging

- **CloudWatch Logs**: Lambda function logs
- **API Gateway Logs**: Request/response logging
- **Amplify Console**: Frontend build and deployment logs
- **CloudWatch Metrics**: Performance monitoring

## Cost Optimization

- **Serverless Architecture**: Pay-per-use Lambda functions
- **HTTP API**: Cost-effective API Gateway option
- **Amplify Hosting**: Includes CDN and SSL
- **Right-sized Resources**: Appropriate memory/timeout settings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

- **Backend Issues**: Check CloudWatch logs
- **Frontend Issues**: Check browser console and Amplify logs
- **Deployment Issues**: See troubleshooting guides in documentation

## License

This project is licensed under the MIT License - see the LICENSE file for details.
