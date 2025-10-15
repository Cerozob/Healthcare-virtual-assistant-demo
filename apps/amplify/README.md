# Healthcare Management System - Amplify Backend

This directory contains the AWS Amplify backend configuration for the Healthcare Management System.

## Migration from CDK API Gateway

The API Gateway setup has been migrated from the CDK-based infrastructure to AWS Amplify for better maintainability and managed services.

### Migrated Functions

The following Lambda functions have been migrated from `lambdas/backend-api/` to Amplify functions:

- **patients** - Patient management CRUD operations
- **medics** - Medical professional management CRUD operations  
- **exams** - Medical exam and test management CRUD operations
- **reservations** - Time reservation management CRUD operations
- **chat** - Chat interface for orchestrator agent communication
- **agent-integration** - Agent health checks, direct queries, and monitoring
- **icd10** - ICD-10 code information retrieval
- **document-upload** - Document upload metadata and processing triggers

### Amplify Storage

Document uploads now use AWS Amplify Storage for direct S3 uploads:

- **Direct S3 uploads** - No Lambda overhead for file handling
- **Organized file structure** - Patient and session-based organization
- **Access control** - Path-based permissions and authentication
- **Progress tracking** - Built-in upload progress and error handling
- **File validation** - Type and size validation before upload

### API Endpoints

The REST API provides the following endpoints:

#### CRUD Resources
- `GET/POST /patients` - List/Create patients
- `GET/PUT/DELETE /patients/{id}` - Get/Update/Delete patient by ID
- `GET/POST /medics` - List/Create medics
- `GET/PUT/DELETE /medics/{id}` - Get/Update/Delete medic by ID
- `GET/POST /exams` - List/Create exams
- `GET/PUT/DELETE /exams/{id}` - Get/Update/Delete exam by ID
- `GET/POST /reservations` - List/Create reservations
- `GET/PUT/DELETE /reservations/{id}` - Get/Update/Delete reservation by ID

#### Special Endpoints
- `GET /icd10/{code}` - Get ICD-10 code information
- `POST /chat/message` - Send message to orchestrator agent
- `GET/POST /chat/sessions` - List/Create chat sessions
- `GET /chat/sessions/{id}/messages` - Get message history
- `GET/POST /agent` - Agent health checks and direct queries
- `POST /documents/upload` - Document upload metadata handling
- `GET /documents/status/{id}` - Get document processing status

#### Storage Endpoints (Direct S3 via Amplify)
- File uploads via Amplify Storage APIs
- Organized paths: `patients/{id}/`, `chat-sessions/{id}/`, `temp-uploads/`
- Automatic access control and encryption

## Deployment

To deploy the Amplify backend:

```bash
cd amplify
npm install
amplify push
```

## Configuration

Environment variables are automatically configured through the Amplify resource definitions. The functions connect to:

- Aurora Postgres database (via RDS Data API)
- S3 buckets for document storage
- Bedrock agents for AI functionality
- CloudWatch for monitoring

## Frontend Integration

The frontend should be updated to use the new Amplify API configuration:

```typescript
import { Amplify } from 'aws-amplify';
import outputs from './amplify_outputs.json';

Amplify.configure({
  ...outputs,
  REST: outputs.custom.API,
  Storage: outputs.storage
});
```

## Benefits of Migration

1. **Managed Infrastructure** - Amplify handles API Gateway configuration
2. **Simplified Deployment** - Single command deployment
3. **Better Integration** - Native Amplify features and tooling
4. **Reduced Complexity** - Less CDK boilerplate code
5. **Automatic Scaling** - Built-in scaling and optimization
