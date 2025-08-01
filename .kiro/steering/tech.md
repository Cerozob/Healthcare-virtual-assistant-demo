# Technology Stack

## Build System & Framework

- **AWS CDK**: Infrastructure as Code using Python
- **Python 3**: Primary development language
- **Virtual Environment**: `.venv` for dependency isolation

## Core Dependencies

- `aws-cdk-lib==latest`: AWS CDK library for infrastructure
- `constructs=latest`: CDK constructs framework
- `cdk-nag==latest`:  CDK Nag for security checks and compliance
- `boto3==latest`: AWS SDK for Python

## Development Dependencies

- `pytest==6.2.5`: Testing framework

## AWS Services (Planned)

Based on healthcare AI requirements:

- **Amazon Bedrock**: LLM integration for conversational AI
- **Amazon Healthscribe**: Medical speech-to-text
- **Amazon Bedrock Data Automation**: Document processing for medical records
- **Lambda Functions**: Serverless compute for API endpoints
- **Step Functions**: Workflow orchestration
- **API Gateway**: REST API management
- **Amazon Aurora Serverless Postgres**: Structured data storage and vector store for AI systems
- **Amazon S3**: Unstructured storage
- **AWS CloudFormation**: Infrastructure deployment
- **AWS Amplify**: Frontend deployment

## Common Commands

### Environment Setup

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### CDK Operations

```bash
# List all stacks
cdk ls

# Synthesize CloudFormation template
cdk synth

# Deploy stack to AWS
cdk deploy

# Compare deployed vs current state
cdk diff

# Open CDK documentation
cdk docs
```

### Development

```bash
# Run tests
pytest

# Watch for changes (auto-synth)
cdk watch
```

## Code Style

- Follow Python PEP 8 conventions
- Use type hints for function parameters and return values
- Healthcare data must be handled with HIPAA compliance in mind
- All AWS resources should follow least-privilege security principles
