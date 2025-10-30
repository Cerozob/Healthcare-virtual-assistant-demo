# Healthcare Management System

AWS serverless healthcare management system with React frontend, AI virtual assistant, and document processing.

## Architecture

- **Backend**: AWS CDK, Lambda, RDS PostgreSQL, S3, Bedrock
- **Frontend**: React + TypeScript, AWS Cloudscape Design, Amplify hosting
- **AI Assistant**: Strands Agents framework with multi-agent architecture

## Quick Start

```bash
# Deploy backend
cdk deploy --all

# Deploy frontend
cd apps/frontend && npm run dev

# Load sample data
python scripts/load_sample_data.py
```

## Features

- Patient and medical staff management
- Appointment scheduling system
- AI-powered document processing (AWS Textract + Bedrock)
- Multi-agent virtual assistant for healthcare queries
- Secure HIPAA-compliant storage

## Configuration

Backend features controlled via `config/config.json`. Frontend configuration in `apps/frontend/src/services/configService.ts`.

## Development

- **Backend**: Python 3.11+, AWS CDK
- **Frontend**: Node.js 18+, React 18, TypeScript
- **AI Agents**: Strands Agents, FastAPI, Pydantic
