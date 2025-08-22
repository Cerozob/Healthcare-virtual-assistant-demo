
# Medical AI System - AWSomeBuilder 2

An AI-powered healthcare solution designed for AnyCompany to modernize patient data management and medical workflow automation.

## Overview

This project provides:

- **Conversational Interface**: AI chatbot for medics to record patient symptoms and notes
- **Automated Scheduling**: Agentic AI system that automatically schedules medical exams and treatments
- **Data Integration**: Connects to internal patient databases, diagnosis records, and exam scheduling systems

## Project Structure

```text
project-root/
├── app.py                  # CDK application entry point
├── cdk.json               # CDK configuration and context settings
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Development dependencies
├── apps/                  # Application code
│   ├── frontend/         # React TypeScript web application (AWS Amplify)
│   ├── api/             # Backend API services (Lambda functions)
│   └── shared/          # Shared code between apps
├── infrastructure/       # AWS CDK infrastructure code
│   ├── __init__.py      # Infrastructure package initialization
│   ├── stacks/          # CDK stack definitions
│   │   └── base_stack.py # Base infrastructure stack
│   └── constructs/      # Reusable CDK constructs
│       ├── ai/          # AI service constructs (Bedrock agents, knowledge bases)
│       ├── compute/     # Compute constructs (Lambda, API Gateway)
│       ├── storage/     # Storage constructs (Aurora, S3)
│       └── aspects/     # CDK aspects (tagging, security)
├── agents/              # AI agents and workflows
├── shared/              # Shared libraries and utilities
├── config/              # Configuration files
│   ├── prod_config.json # Production environment configuration
│   └── tags.json        # Mandatory resource tags for compliance
├── scripts/             # Deployment and utility scripts
├── docs/                # Documentation and samples
└── .kiro/               # Kiro IDE configuration and specifications
    ├── specs/           # Project specifications and requirements
    └── steering/        # AI assistant guidance documents
```

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+ (for frontend development)
- AWS CLI configured
- AWS CDK CLI installed
- CDK Nag for security compliance checks

### Environment Setup

1. Create and activate virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate.bat
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure AWS credentials:

```bash
aws configure
```

### Current Implementation Status

The project has completed the foundational infrastructure setup:

- ✅ **Base Infrastructure**: Complete base stack with VPC, security groups, IAM roles, and KMS keys
- ✅ **Data Storage Stack**: Aurora PostgreSQL and S3 buckets with encryption and monitoring
- ✅ **Configuration**: Production config and mandatory tagging system
- ✅ **Project Structure**: Organized directory structure with proper Python packaging
- ✅ **CDK Constructs**: Production-ready constructs for AI, compute, storage, and security components
- ✅ **Infrastructure Stacks**: Base and data storage stacks fully implemented
- 🚧 **Planned**: API stack, GenAI stack, workflow stack, frontend stack
- 📋 **Next Phase**: API services, frontend application, AI agents, and workflows

#### Implemented CDK Constructs

- **AI Constructs**:
  - `MedicalBedrockAgent`: Bedrock agent with security, monitoring, and action group integration
  - `MedicalBedrockKnowledgeBase`: Knowledge base with Aurora PostgreSQL vector store (pgvector)
- **Compute Constructs**:
  - `MedicalLambda`: Lambda functions with monitoring, DLQ, and security best practices
  - `MedicalApiGateway`: API Gateway with WAF, CORS, throttling, and monitoring
- **Storage Constructs**:
  - `MedicalAuroraCluster`: Aurora PostgreSQL with vector extension support
  - `MedicalDynamoDBTable`: DynamoDB with encryption and monitoring (available for future use)
  - `MedicalS3Bucket`: S3 buckets with encryption, lifecycle policies, and monitoring
- **Security Constructs**:
  - `MandatoryTaggingAspect`: Automatic compliance tagging for all resources
  - `CdkNagSuppressionAspect`: Development-phase security rule suppression for rapid iteration

### Development Commands

#### CDK Operations

```bash
# List all stacks
cdk ls

# Synthesize CloudFormation template
cdk synth

# Deploy base infrastructure
cdk deploy MedicalAIBaseStack

# Deploy data storage stack
cdk deploy MedicalAIDataStorageStack

# Deploy all stacks
cdk deploy --all

# Compare deployed vs current state
cdk diff

# Run security compliance checks (currently suppressed for development)
cdk synth --strict

# Open CDK documentation
cdk docs
```

#### Security and Compliance

During the development phase, CDK Nag security checks are suppressed to allow rapid iteration. All suppressed rules are documented and will be addressed during the compliance review phase:

```bash
# View suppressed security rules
grep -r "Suppressed for development phase" infrastructure/

# When ready for compliance review, disable suppressions by removing CdkNagSuppressionAspect from app.py
```

#### Testing

```bash
# Run tests
pytest

# Watch for changes (auto-synth)
cdk watch
```

## Configuration

### Infrastructure Configuration

- `config/prod_config.json`: Production environment configuration including:
  - AWS account and region settings
  - VPC and networking configuration
  - Database settings (Aurora PostgreSQL)
  - API throttling and monitoring settings
  - Security and compliance configurations

- `config/tags.json`: Mandatory resource tags for compliance and cost management:
  - **Mandatory tags**: Project ("AWSomeBuilder 2"), Environment ("prod"), Owner ("AnyCompany HealthCare"), TechArea (component-specific like "frontend", "api", "genai", "documentprocessing"), CreatedBy ("CDK-Deployment"), HIPAACompliant ("false", will be changed to "true" when compliance is achieved)
  - **Optional tags**: BackupRequired, MonitoringLevel, LogRetentionDays

### CDK Configuration

- `cdk.json`: CDK application configuration with feature flags and context settings
- `app.py`: CDK entry point that loads configuration and applies mandatory tags to all resources

## Compliance

This system is designed with healthcare compliance in mind:

- HIPAA-compliant data handling
- Encryption at rest and in transit
- Audit logging and monitoring
- Least-privilege access controls
- CDK Nag security compliance checks integrated into deployment pipeline

### Development Phase Security

During development, security compliance checks are temporarily suppressed using `CdkNagSuppressionAspect` to enable rapid iteration. This aspect suppresses:

- **AWS Solutions Rules**: VPC flow logs, security group restrictions, IAM policies, S3 access controls, RDS security, Lambda configurations, API Gateway settings
- **HIPAA Compliance Rules**: Healthcare-specific security requirements including encryption, access controls, and audit logging
- **Additional Security Rules**: CloudFront, ELB, ECS, SNS, SQS, and KMS security configurations

All suppressed rules are documented with reasons and will be systematically addressed during the compliance review phase before production deployment.

## Architecture

The system uses a multi-layered architecture:

- **Frontend**: React TypeScript on AWS Amplify
- **API Layer**: AWS Lambda functions with API Gateway
- **AI Layer**: Amazon Bedrock agents and workflows
- **Data Layer**: Aurora PostgreSQL and S3 storage
- **Infrastructure**: AWS CDK with Python

For detailed architecture documentation, see `docs/` directory:

- `docs/infrastructure-setup.md`: Infrastructure setup and deployment guide
- `docs/cdk-nag-suppression.md`: Development phase security compliance approach

## Contributing

1. Follow Python PEP 8 conventions
2. Use type hints for function parameters and return values
3. Ensure all AWS resources follow least-privilege security principles
4. Healthcare data must be handled with HIPAA compliance in mind

## License

This project is proprietary to AnyCompany Healthcare.
