# Project Structure Design Document

## Overview

This design document outlines the recommended directory structure for a comprehensive medical AI system built on AWS. The structure supports a multi-layered architecture with clear separation of concerns between frontend (React TypeScript on AWS Amplify), backend APIs (with agent-ready action groups), AI agents, and Python CDK infrastructure.

## Architecture

The project follows a domain-driven design approach with the following key architectural principles:

- **Separation of Concerns**: Frontend, backend, infrastructure, and AI components are clearly separated
- **Domain Organization**: Code is organized by business domains (medical processing, patient management, etc.)
- **Infrastructure as Code**: All AWS resources are defined using Python CDK for production deployment
- **Agent-Ready APIs**: API functions double as action groups for AI agents
- **Demo-Focused**: Streamlined for rapid development and demonstration purposes

## Components and Interfaces

### CDK Construct Usage Pattern

Each construct encapsulates its own security and monitoring, while tagging is handled by CDK aspects:

```python
# Tagging aspect applied at app level
from constructs.aspects.tagging_aspect import MandatoryTaggingAspect

# In app.py - applies tags to ALL resources
app = App()
Aspects.of(app).add(MandatoryTaggingAspect())

# Usage in stacks:
from constructs.compute.lambda_construct import MedicalLambda

lambda_function = MedicalLambda(
    self, "PatientAPI",
    function_name="patient-handler",
    runtime=Runtime.PYTHON_3_13,
    # Security and monitoring built-in, tags applied by aspect
)

# Example: S3 construct with built-in security
from constructs.storage.s3_construct import MedicalS3Bucket

bucket = MedicalS3Bucket(
    self, "DocumentStorage",
    bucket_name="medical-documents-prod"
    # Encryption, logging, lifecycle policies built-in
    # Tags applied automatically by aspect
)
```

### Root Level Structure

```
project-root/
├── apps/                    # Application code
├── infrastructure/          # AWS CDK infrastructure code
├── agents/                  # AI agents and workflows
├── shared/                  # Shared libraries and utilities
├── config/                  # Configuration files
├── scripts/                 # Deployment and utility scripts
├── docs/                    # Documentation and samples
├── tests/                   # Integration and E2E tests
├── template.json            # SAM template for local testing
├── samconfig.json           # SAM configuration
└── events/                  # Sample events for SAM local testing
```

### Applications Layer (`apps/`)

```
apps/
├── frontend/               # React TypeScript web application (AWS Amplify)
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API client services
│   │   ├── stores/         # State management (Redux/Zustand)
│   │   ├── types/          # TypeScript type definitions
│   │   └── utils/          # Frontend utilities
│   ├── public/             # Static assets
│   ├── amplify.json        # AWS Amplify build configuration
│   ├── package.json
│   └── tsconfig.json
├── api/                    # Backend API services (Lambda functions)
│   ├── src/
│   │   ├── handlers/       # Lambda function handlers
│   │   ├── action-groups/  # Agent-ready action group implementations
│   │   ├── services/       # Business logic
│   │   ├── repositories/   # Data access layer
│   │   ├── models/         # Data models
│   │   └── utils/          # Backend utilities
│   ├── requirements.txt    # Python dependencies
│   └── serverless.json     # Serverless framework config (optional)
├── document-processing-workflow/         # Non-agentic document workflows
│   ├── workflow_config.json      # Step Functions configurations
│   ├── bedrock_data_automation/ # Bedrock Data Automation configs
│   ├── comprehend_medical/      # Comprehend Medical processing
│   ├── healthscribe/            # HealthScribe configurations
│   └── step_functions/          # Document processing workflows
└── shared/                 # Shared code between apps
    ├── schemas/            # Data validation schemas
    ├── constants/          # Shared constants
    └── types/              # Shared type definitions
```

### Infrastructure Layer (`infrastructure/`)

```
infrastructure/
├── stacks/
│   ├── base_stack.py             # Core networking, IAM roles, shared resources
│   ├── api_stack.py              # API Gateway, Lambda functions, security, monitoring
│   ├── data_storage_stack.py     # S3, Aurora PostgreSQL, DynamoDB, security, monitoring
│   ├── workflow_stack.py         # Step Functions, document processing, security, monitoring
│   ├── genai_stack.py            # Bedrock agents, models, security, monitoring
│   └── frontend_stack.py         # AWS Amplify hosting, security, monitoring
├── constructs/                   # Reusable CDK constructs
│   ├── __init__.py
│   ├── aspects/
│   │   ├── __init__.py
│   │   └── tagging_aspect.py     # CDK aspect for mandatory tagging
│   ├── compute/
│   │   ├── __init__.py
│   │   ├── lambda_construct.py   # Lambda with IAM, CloudWatch
│   │   └── api_gateway_construct.py # API Gateway with WAF, logging
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── s3_construct.py       # S3 with encryption, access logging
│   │   └── database_construct.py # RDS/DynamoDB with encryption, monitoring
│   └── ai/
│       ├── __init__.py
│       ├── bedrock_agent_construct.py # Agent with IAM, CloudWatch
│       └── knowledge_base_construct.py # Knowledge base with security
├── config/
│   └── prod_config.py            # Production environment config
├── app.py                        # CDK app entry point
├── requirements.txt              # Python CDK dependencies
└── cdk.json
```

### AI Agents Layer (`agents/`)

```
agents/
├── appointment-scheduler/        # Agent for scheduling appointments
│   ├── agent_definition.json     # Bedrock agent configuration
│   ├── action_groups/           # Action group implementations
│   ├── prompt.md                # Agent prompts and instructions
├── qa-knowledge-retrieval/      # Question answering and knowledge retrieval
│   ├── agent_definition.json    # Bedrock agent configuration
│   ├── action_groups/           # Action group implementations
│   ├── prompt.md                # Agent prompts and instructions
│   └── knowledge_base/          # Medical knowledge base
├── orchestrator/                # Main orchestrator agent
│   ├── agent_definition.json    # Bedrock agent configuration
│   ├── prompt.md                 # Orchestration prompts
│   └── workflows/               # Agent coordination logic
└── shared/
    ├── bedrock_config.json      # Bedrock model configurations
    ├── models/                  # Shared AI model configurations
    ├── prompts/                 # Common prompts and templates
    └── utils/                   # Agent utilities
```

### Configuration Layer (`config/`)

```
config/
├── prod_config.json              # Production environment configuration
├── tags.json                     # Mandatory resource tags
```

## Data Models

### Core Entities

- **Patient**: Patient information and medical history
- **Medical Staff**: Doctor/medic information and specializations
- **Document**: Medical documents and metadata
- **Examination**: Medical examinations and results (linked to responsible medic)
- **Appointment**: Scheduled appointments between patients and medical staff
- **Agent**: AI agent configurations and state
- **Workflow**: Processing workflow definitions

### Data Flow

1. **Text-based Document Ingestion**: S3 → Bedrock Data Automation → Comprehend Medical → S3
2. **Audio Document Processing**: S3 → HealthScribe → S3
3. **AI Processing**: Bedrock Agents → Action Groups (Lambda) → Data Layer
4. **API Layer**: API Gateway → Lambda → Business Logic → Data Layer
5. **Frontend**: React TypeScript (Amplify) → API Client → REST APIs

## Error Handling

### Infrastructure Level

- CloudWatch alarms for service health monitoring
- Dead letter queues for failed message processing
- Circuit breaker patterns for external service calls

### Application Level

- Centralized error handling middleware
- Structured logging with correlation IDs
- Graceful degradation for AI service failures

### Agent Level

- Retry mechanisms with exponential backoff
- Fallback strategies for AI model failures
- State persistence for long-running workflows

## Development Workflow

### Local Development

- **AWS SAM**: Used for local testing of Lambda functions and API Gateway
- Direct AWS development account usage (no LocalStack)
- Hot reload for React frontend development
- AWS CDK for infrastructure management, cdk-nag for compliance and best practices management

### SAM Configuration

The project includes SAM templates for local testing:

```json
{
  "AWSTemplateFormatVersion": "2010-09-09",
  "Transform": "AWS::Serverless-2016-10-31",
  "Globals": {
    "Function": {
      "Runtime": "python3.13",
      "Environment": {
        "Variables": {
          "ENVIRONMENT": "local"
        }
      }
    }
  },
  "Resources": {
    "PatientAPI": {
      "Type": "AWS::Serverless::Function",
      "Properties": {
        "CodeUri": "apps/api/src/",
        "Handler": "handlers.patient_handler.lambda_handler",
        "Events": {
          "PatientEndpoint": {
            "Type": "Api",
            "Properties": {
              "Path": "/patients",
              "Method": "get"
            }
          }
        }
      }
    }
  }
}
```

### Local Testing Commands

```bash
# Start SAM local API
sam local start-api

# Invoke specific function locally
sam local invoke PatientAPI --event events/patient-event.json

# Start local DynamoDB (if needed)
sam local start-lambda
```

### Monitoring and Observability

- **Resource Tagging**: All AWS resources must include mandatory tags for cost monitoring and resource management
- CloudWatch dashboards for system metrics
- X-Ray tracing for distributed request tracking
- Custom metrics for business KPIs
- Cost allocation tags for budget tracking

### Resource Tagging Strategy

All AWS resources must include the following mandatory tags:

- `Project`: Medical AI System
- `Environment`: prod
- `Owner`: [Team/Individual responsible]
- `CostCenter`: [Budget allocation]
- `CreatedBy`: [CDK deployment identifier]
