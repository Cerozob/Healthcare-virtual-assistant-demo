# Infrastructure Setup Guide

## Overview

AWSomeBuilder uses AWS CDK (Cloud Development Kit) with Python for Infrastructure as Code. This document outlines the current infrastructure setup and deployment process.

## Current Infrastructure Components

### Base Infrastructure Stack

The `infrastructure/stacks/base_stack.py` provides the foundation for AWSomeBuilder:

- **Purpose**: Core networking, shared IAM roles, and foundational resources
- **Status**: ✅ **Complete implementation** with full VPC, security, and IAM setup
- **Implemented Components**:
  - **VPC and Networking**: Multi-AZ VPC with public, private, and database subnets
  - **Security Groups**: Dedicated security groups for API, database, and frontend components
  - **IAM Roles**: Shared execution roles for Lambda, API Gateway, and Bedrock agents
  - **KMS Keys**: Customer-managed encryption keys for medical data and CloudWatch logs
  - **CloudWatch Logging**: Centralized log groups with encryption and retention policies
  - **CloudFormation Outputs**: Exported resources for cross-stack references

### Data Storage Stack

The `infrastructure/stacks/data_storage_stack.py` provides comprehensive data storage for AWSomeBuilder:

- **Purpose**: S3 buckets and Aurora PostgreSQL for medical data storage
- **Status**: ✅ **Complete implementation** with full data layer setup
- **Implemented Components**:
  - **S3 Buckets**: Medical documents, audio files, processed data, and backup buckets with lifecycle policies
    - Documents bucket: `ab2-cerozob-medical-documents-{environment}`
    - Audio bucket: `ab2-cerozob-medical-audio-{environment}`
    - Processed data bucket: `ab2-cerozob-medical-processed-{environment}`
    - Backup bucket: `ab2-cerozob-medical-backup-{environment}`
  - **Aurora PostgreSQL**: Serverless v2 cluster with vector extension (pgvector) for AI workloads
  - **Backup Policies**: AWS Backup integration (currently simplified to avoid cyclic dependencies)
  - **Encryption**: Customer-managed KMS keys for all data at rest
  - **Monitoring**: CloudWatch alarms and Performance Insights enabled
  - **High Availability**: Multi-AZ deployment with read replicas

### Implemented CDK Constructs

The project includes production-ready CDK constructs with built-in security and monitoring:

#### AI Service Constructs

- **MedicalBedrockAgent** (`infrastructure/constructs/ai/bedrock_agent_construct.py`):
  - Bedrock agent with IAM least privilege permissions
  - CloudWatch logging and monitoring
  - Action group integration with Lambda functions
  - Knowledge base integration support
  - Automatic agent preparation and versioning

- **MedicalBedrockKnowledgeBase** (`infrastructure/constructs/ai/knowledge_base_construct.py`):
  - Knowledge base with Aurora PostgreSQL vector store (pgvector extension)
  - S3 data source integration with encryption
  - Automatic chunking and embedding configuration
  - IAM permissions for RDS Data API access
  - CloudWatch logging integration

#### Compute Service Constructs

- **MedicalLambda** (`infrastructure/constructs/compute/lambda_construct.py`):
  - Lambda functions with CloudWatch monitoring and alarms
  - Dead letter queue for failed invocations
  - X-Ray tracing enabled
  - Security best practices with least privilege IAM
  - Configurable timeout, memory, and concurrency settings

- **MedicalApiGateway** (`infrastructure/constructs/compute/api_gateway_construct.py`):
  - API Gateway with WAF protection and rate limiting
  - CORS configuration for web applications
  - CloudWatch access logging and monitoring
  - Request/response validation support
  - Throttling and quota management

#### Storage Service Constructs

- **MedicalAuroraCluster** (`infrastructure/constructs/storage/database_construct.py`):
  - Aurora PostgreSQL with vector extension (pgvector) for AI workloads
  - Encryption at rest and in transit with customer-managed KMS keys
  - Multi-AZ deployment for high availability
  - Enhanced monitoring and Performance Insights
  - Automated backups and point-in-time recovery

- **MedicalDynamoDBTable** (`infrastructure/constructs/storage/database_construct.py`):
  - DynamoDB with customer-managed encryption
  - Point-in-time recovery enabled
  - CloudWatch monitoring and alarms
  - Global secondary index support
  - DynamoDB Streams for change data capture

#### Security and Compliance

- **MandatoryTaggingAspect** (`infrastructure/constructs/aspects/tagging_aspect.py`):
  - Automatic application of compliance tags to all AWS resources
  - Project identification (AWSomeBuilder) and environment tracking (prod)
  - Ownership tracking (AnyCompany HealthCare) and technical area classification
  - HIPAA compliance status tracking (initially false, updated when compliance is achieved)
  - Configurable through `config/tags.json`

- **CdkNagSuppressionAspect** (`infrastructure/constructs/aspects/cdk_nag_suppression_aspect.py`):
  - Temporary suppression of CDK Nag security rules during development phase
  - Comprehensive documentation of all suppressed rules with reasons
  - Covers AWS Solutions, HIPAA compliance, and additional security rules
  - Enables rapid development while maintaining clear compliance roadmap

### CDK Application Structure

```text
infrastructure/
├── __init__.py              # Package initialization
├── stacks/
│   ├── __init__.py         # Stacks package
│   ├── base_stack.py       # Base infrastructure stack
│   └── data_storage_stack.py # Data storage stack with S3 and Aurora
└── constructs/             # Reusable CDK constructs
    ├── __init__.py
    ├── ai/                 # AI service constructs
    │   ├── __init__.py
    │   ├── bedrock_agent_construct.py      # Bedrock agent with security & monitoring
    │   └── knowledge_base_construct.py     # Knowledge base with Aurora PostgreSQL vector store
    ├── compute/            # Compute service constructs
    │   ├── __init__.py
    │   ├── lambda_construct.py             # Lambda with monitoring, DLQ, security
    │   └── api_gateway_construct.py        # API Gateway with WAF, CORS, throttling
    ├── storage/            # Storage service constructs
    │   ├── __init__.py
    │   ├── database_construct.py           # Aurora PostgreSQL & DynamoDB with encryption
    │   └── s3_construct.py                 # S3 with encryption & monitoring
    └── aspects/            # CDK aspects for cross-cutting concerns
        ├── __init__.py
        ├── tagging_aspect.py               # Mandatory compliance tagging
        └── cdk_nag_suppression_aspect.py   # Development-phase security suppression
```

## Configuration Management

### Environment Configuration

The system uses `config/prod_config.json` for environment-specific settings:

```json
{
  "environment": "prod",
  "region": "us-east-1",
  "vpc": {
    "cidr": "10.0.0.0/16",
    "max_azs": 2
  },
  "database": {
    "aurora_postgres": {
      "engine_version": "15.4",
      "instance_class": "serverless"
    }
  },
  "security": {
    "enable_waf": true,
    "enable_encryption": true
  }
}
```

### Mandatory Tagging

All AWS resources are automatically tagged using `config/tags.json`:

- **Project**: AWSomeBuilder
- **Environment**: prod
- **Owner**: AnyCompany HealthCare
- **TechArea**: Component-specific (frontend, api, genai, documentprocessing, etc.)
- **CreatedBy**: CDK-Deployment
- **HIPAACompliant**: false (will be changed to true when compliance is achieved)

## Deployment Commands

```bash
# List available stacks
cdk ls

# Synthesize CloudFormation templates
cdk synth

# Run security compliance checks (currently suppressed for development)
cdk synth --strict

# Deploy base infrastructure
cdk deploy MedicalAIBaseStack

# View differences before deployment
cdk diff
```

## Security and Compliance

### Healthcare Compliance Features

- **Encryption**: All data encrypted at rest and in transit
- **Access Control**: Least-privilege IAM policies
- **Audit Logging**: CloudTrail and CloudWatch integration
- **Network Security**: VPC with private subnets and security groups
- **Security Validation**: CDK Nag integration for automated security compliance checks
- **AWS SDK Integration**: Latest boto3 for secure AWS service interactions

### Development Phase Security Approach

During the development phase, the project uses `CdkNagSuppressionAspect` to temporarily suppress security compliance checks, enabling rapid iteration without being blocked by compliance requirements. This approach:

- **Suppresses AWS Solutions Rules**: Including VPC flow logs, security group restrictions, IAM policy validations, S3 access controls, RDS security settings, Lambda configurations, and API Gateway security requirements
- **Suppresses HIPAA Compliance Rules**: Healthcare-specific security requirements such as encryption standards, access controls, and audit logging configurations
- **Documents All Suppressions**: Each suppressed rule includes a reason and reference for future compliance implementation
- **Enables Rapid Development**: Allows developers to focus on functionality while maintaining a clear path to compliance

**Important**: All suppressed rules are documented and will be systematically addressed during the compliance review phase before production deployment. The suppression aspect can be easily removed from `app.py` when ready for full compliance validation.

For detailed information about the suppression approach and compliance transition strategy, see `docs/cdk-nag-suppression.md`.

### Mandatory Tags for Compliance

Every AWS resource receives compliance tags automatically:

- Project identification (AWSomeBuilder)
- Environment classification (prod)
- Ownership tracking (AnyCompany HealthCare)
- Technical area classification (frontend, api, genai, documentprocessing, etc.)
- HIPAA compliance status (initially false, updated when compliance is achieved)
- Creation tracking (CDK-Deployment)

## Next Steps

The infrastructure is ready for the following planned stacks:

1. **API Stack**: Lambda functions, API Gateway
2. **GenAI Stack**: Bedrock agents and knowledge bases
3. **Workflow Stack**: Step Functions for document processing
4. **Frontend Stack**: AWS Amplify hosting

## Development Guidelines

- All infrastructure code follows Python PEP 8 conventions
- Use type hints for all function parameters and return values
- Healthcare data handling must maintain HIPAA compliance
- Apply least-privilege security principles to all AWS resources
- Run CDK Nag security checks before deployment (`cdk synth --strict`)
- Use latest boto3 SDK features for optimal AWS service integration
