# Healthcare Assistant

Multi-agent virtual assistant system for healthcare using Strands Agents framework.

## Overview

This healthcare assistant provides intelligent support for medical professionals through a multi-agent architecture built on AWS Bedrock and the Strands Agents framework.

## Features

- Multi-agent conversation management
- AWS Bedrock integration for AI capabilities
- Healthcare-specific knowledge base
- Secure and compliant architecture
- Real-time observability and monitoring

## Architecture

The system consists of multiple specialized agents:
- **Triage Agent**: Initial patient assessment and routing
- **Medical Knowledge Agent**: Access to medical databases and guidelines
- **Appointment Agent**: Scheduling and calendar management
- **Documentation Agent**: Medical record management and documentation

## Deployment

This application is designed to run on AWS using:
- AWS Lambda for serverless execution
- Amazon Bedrock for AI model access
- Amazon DynamoDB for data storage
- AWS CloudWatch for monitoring

## Development

Built with:
- Python 3.11+
- Strands Agents framework
- FastAPI for API endpoints
- Pydantic for data validation
- OpenTelemetry for observability
