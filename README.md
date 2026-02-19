# Healthcare Virtual Assistant Demo

This is a demo for a GenAI powered chat assistant capable of helping medics to retrieve patient information, make recommendations based on notes and documented diagnostics, ingest multimodal documentation and maintain context in a prolonged conversation.

## Architecture Overview

![Architecture Diagram](./docs/architecture_final.png)

The system is composed of four main components:

### 1. Frontend (Chat Interface)
React-based web application hosted on AWS Amplify that provides:
- **User Interface**: AWS Cloudscape Design System components
- **Authentication**: Amazon Cognito for secure access
- **Chat Experience**: Real-time interaction with the AI assistant
- **Document Upload**: Direct upload to S3 with progress tracking
- **API Integration**: REST API calls to backend services

### 2. Backend (Operations & Data)
Serverless backend managing healthcare data and operations:
- **API Gateway**: REST API endpoints for CRUD operations
- **Lambda Functions**: Python 3.13 functions for:
  - Patient management (CRUD)
  - Medical staff management
  - Appointment scheduling (reservations)
  - Exam type configuration
  - File operations and queries
- **RDS Aurora PostgreSQL**: Serverless v2 database (see Data Model below)
- **S3 Buckets**: Raw and processed document storage

### 3. Document Ingestion Workflow
Automated pipeline for processing medical documents:
- **S3 Upload**: Documents uploaded to raw bucket trigger processing
- **Step Functions**: Orchestrates the document workflow
- **Lambda Jobs**: Extract and structure document data
- **Bedrock Data Automation**: AI-powered document analysis
- **Knowledge Base Ingestion**: Processed documents stored as vectors in PostgreSQL
- **Processed Storage**: Final documents stored in processed bucket

### 4. Agentic Assistant (AI Layer)
Multi-agent system powered by AWS Bedrock:
- **AgentCore Runtime**: Containerized Strands agent (Python 3.11+, ARM64)
- **Agent Orchestrator**: Coordinates specialized sub-agents
- **AgentCore Gateway**: MCP protocol with semantic search for tool access
- **Specialized Agents**:
  - **Info Retrieval**: Queries patient data and medical records
  - **Appointment Scheduling**: Manages calendar and bookings
- **Lambda Tools**: Individual gateway targets for each healthcare domain (patients, medics, exams, reservations, files)
- **Bedrock Services**:
  - **Models**: Amazon Nova 2 Lite (global inference profile) - original use case used Claude Haiku 4.0 but sandboxed accounts may have restrictions
  - **Knowledge Base**: Vector search using PostgreSQL pgvector extension
  - **Guardrails**: Shadow-mode content filtering and PII detection (mostly for demo purposes)
- **Multimodal Support**: Processes text, images, and documents

## Data Model

![Database Schema](./docs/SQL%20Schema.png)

The PostgreSQL database uses a relational schema with vector search capabilities for the AI knowledge base.

### Vector Storage (Knowledge Base)

**ab2_knowledge_base**: Stores document embeddings for semantic search using pgvector extension (1024-dimensional vectors). Includes text content, vector embeddings, metadata, and custom metadata fields. Indexed with IVFFlat for efficient similarity search.

### Core Healthcare Tables

**patients**: Stores patient demographics and medical information. Includes personal details (name, email, phone, date of birth), identification (cédula/national ID), medical history and lab results (JSONB), and document references. Indexed on email, names, and cédula for fast lookups.

**medics**: Medical staff directory with contact information, specialization, license numbers, and department assignments. Each medic has a unique email and license number.

**exams**: Catalog of available medical exam types. Defines exam names, types, descriptions, duration, and preparation instructions. Used for scheduling and appointment management.

**reservations**: Appointment scheduling system linking patients, medics, and exams. Tracks reservation date/time, status (scheduled, confirmed, completed, cancelled, no_show), and notes. Enforces unique constraint on medic availability (one appointment per medic per time slot).

**processed_documents**: Metadata for documents processed through the ingestion workflow. Links to patients, stores S3 URIs, extracted data (JSONB), and processing timestamps. Used to track document processing history.

## Prerequisites

### For Deployment

- **AWS Account** with appropriate permissions
- **AWS CLI** configured with credentials
- **Python 3.11+** (for agents) and **Python 3.13** (for Lambda functions)
- **Node.js 24+** (for frontend)
- **AWS CDK CLI**: `npm install -g aws-cdk`
- **Python package manager**: pip, uv, or any Python package installer
- **Docker**: To build agent containers (ARM64 architecture - **mandatory for AgentCore**)
- **GitHub Personal Access Token**: Stored in AWS Secrets Manager as `github_access_token_demo` (for Amplify deployment)

## Deployment

### Step 1: Deploy Backend Infrastructure

Deploy all backend stacks using AWS CDK. This will create the database, API Gateway, Lambda functions, document workflow, and AI agent infrastructure.

```bash
# Ensure you're in the project root directory
cd Healthcare-virtual-assistant-demo

# Install Python dependencies
pip install -r requirements.txt

# Bootstrap CDK (first time only in your AWS account/region)
cdk bootstrap

# Deploy all stacks (this may take 15-20 minutes)
cdk deploy --all

# Note: This will:
# - Build and push the agent container (ARM64) to ECR
# - Create Aurora PostgreSQL Serverless v2 database
# - Initialize database schema using Lambda
# - Set up API Gateway and Lambda functions
# - Configure Bedrock Knowledge Base and Guardrails
# - Create Amplify application (not yet deployed)
# - Set up document processing workflow
```

**Important**: Save the CDK outputs displayed after deployment. You'll need these values for the frontend configuration:
- `AgentCoreRuntimeId`
- `ApiGatewayUrl` (API base URL)
- `DatabaseClusterIdentifier`
- `RawBucketName`
- `ProcessedBucketName`
- `AmplifyAppId`

### Step 2: Deploy Frontend via Amplify Console

The backend deployment creates an Amplify application, but you need to configure it manually in the AWS Console.

#### 2.1 Access Amplify Console

1. Go to AWS Console → AWS Amplify
2. Find the application named "HealthCareAssistantDemo"
3. Click on the application

#### 2.2 Link Repository Branch

1. Click "Connect branch" or check if a branch is already connected
2. If no branch is connected or configuration is incorrect:
   - Click "Connect branch"
   - Select your GitHub repository
   - Choose the branch to deploy (typically `main` or `prod`)
   - **Important**: Check these boxes:
     - ✅ "Override build settings"
     - ✅ "This is a monorepo"
   - Set monorepo path: `apps/frontend`
   - Set Node.js version: **Node.js 24**

**Optional - GitHub Token (Deprecated)**: You can populate the AWS Secrets Manager secret named `github_access_token_demo` with a GitHub Personal Access Token to enable automatic branch deployment. However, note that token-based access is deprecated by GitHub and may stop working soon. Manual branch connection via the Amplify Console is the recommended approach.

#### 2.3 Configure Environment Variables


In the Amplify Console, go to "Environment variables" and verify/set these variables using the values from your CDK deployment outputs:

| Variable | Value (from CDK outputs) | Example |
|----------|--------------------------|---------|
| `AMPLIFY_MONOREPO_APP_ROOT` | `apps/frontend` | `apps/frontend` |
| `VITE_AGENTCORE_RUNTIME_ID` | Your AgentCore Runtime ID | `healthcare_assistant-oaiduaosidua` |
| `VITE_API_BASE_URL` | Your API Gateway URL | `https://example.execute-api.us-east-1.amazonaws.com/v1` |
| `VITE_AWS_REGION` | Your deployment region | `us-east-1` |
| `VITE_DB_CLUSTER_IDENTIFIER` | Your Aurora cluster ID | `cluster-ASDADAD87ASD9` |
| `VITE_S3_BUCKET_NAME` | Your raw bucket name | `demo-healthcareva-dfx5-rawdata-us-east-1` |
| `VITE_S3_PROCESSED_BUCKET_NAME` | Your processed bucket name | `demo-healthcareva-dfx5-processeddata-us-east-1` |

**Note**: Use the actual values from your CDK deployment outputs, not the examples shown above.

#### 2.4 Trigger Deployment

1. After configuring environment variables, click "Save"
2. Go to the connected branch
3. Click "Redeploy this version" or push a commit to trigger a build
4. Wait for the build to complete (typically 5-10 minutes)
5. Once deployed, you'll see a URL like: `https://prod.xxxxx.amplifyapp.com`

#### 2.5 Access the Application

1. Open the Amplify-provided URL in your browser
2. Click "Sign up" to create a new account
3. Enter your email and create a password
4. Verify your email using the code sent by Cognito
5. Log in with your credentials

You should now have access to the Healthcare Virtual Assistant demo!

## Additional Features and Considerations

### CDK Nag Compliance Checks

The CDK application includes optional compliance and best practices checks via CDK Nag. Edit `config/config.json` to enable:

```json
{
  "enableHIPAAChecks": true,
  "enableAWSSolutionsChecks": true,
  "enableServerlessChecks": true
}
```

These checks will flag potential issues during `cdk synth` or `cdk deploy`:
- **HIPAA Checks**: Regulatory compliance for healthcare data
- **AWS Solutions Checks**: AWS best practices and security
- **Serverless Checks**: Serverless architecture optimization

Useful for planning production deployments or meeting regulatory requirements.

### Loading Sample Patient Data

You can preload patient data using the provided Python script:

```bash
cd scripts
python load_sample_data.py
```

**Requirements**:
- Boto3 credentials configured correctly (`aws configure`)
- Backend stack deployed successfully
- Sample data exists in `apps/SampleFileGeneration/output/`

**Note**: Patient documents must be uploaded manually through the web UI:
1. Log in to the application
2. Click on your username (top right)
3. Go to the Configuration tab
4. Upload documents for each patient

### Aurora Auto-Pause Behavior

The Aurora Serverless v2 cluster has auto-pause enabled (10 minutes of inactivity). This saves costs but can cause delays when resuming.

**For demos or presentations**:
- Disable auto-pause temporarily in the Aurora console, or
- Send a test query 5-10 minutes before your demo to wake the cluster

**To disable auto-pause**: Modify `infrastructure/stacks/backend_stack.py`:
```python
serverless_v2_auto_pause_duration=None,  # Disable auto-pause
serverless_v2_min_capacity=0.5 # set to greater than 0 to disable auto pausing, enabling auto pause neds this value to be zero
```

### Conversation Context & Session Management

**Context Preservation**:
- The agent maintains conversation context across messages
- AgentCore automatically handles context of the current conversation in the background
- Context is preserved within a session but conversation history is not visible (but is saved in an S3 bucket as JSON files if needed)

**Session Management**:
- Each conversation has a unique session ID
- AgentCore and Strands use this session ID to retrieve conversation context
- Session IDs are managed automatically by the frontend

**Note**: Message history is stored by AgentCore but the current frontend implementation doesn't display it.

### AgentCore Gateway & MCP Tools

**Lambda Tool Exposure**:
- The AgentCore Gateway exposes Lambda functions as MCP tools to the agents
- Each healthcare domain (patients, medics, exams, reservations, files) has its own gateway target
- Tools are discoverable via semantic search

**Semantic Search**:
- Currently uses a fixed prompt for tool discovery
- You can implement a custom tool to let the agent dynamically generate search prompts
- This would allow more flexible tool selection based on conversation context

**Example**: Instead of a fixed "find patient tools" prompt, the agent could generate context-aware prompts like "tools for scheduling appointments with cardiologists".

## Project Structure

```
.
├── agents/                    # AI agent system
├── apps/
│   ├── frontend/              # React web application
│   └── SampleFileGeneration/  # Sample data generator
├── infrastructure/            # AWS CDK infrastructure
├── lambdas/                   # Lambda function code
├── scripts/                   # Deployment scripts
├── config/                    # Configuration files
└── app.py                    # CDK app entry point
```

## Additional Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Strands Agents Framework](https://github.com/awslabs/strands)
- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [AWS Cloudscape Design System](https://cloudscape.design/)
