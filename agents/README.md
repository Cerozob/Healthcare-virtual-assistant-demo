# Healthcare Assistant Agent

This directory contains the multi-agent virtual assistant system for healthcare using Strands Agents and Bedrock AgentCore.

## Structure

- `main.py` - Main entry point for the agent runtime
- `orchestrator/` - Orchestrator agent for coordinating conversations
- `info_retrieval/` - Information retrieval agent for knowledge base queries
- `appointment_scheduling/` - Appointment scheduling agent
- `shared/` - Shared utilities and configurations
- `Dockerfile` - Container configuration for AgentCore Runtime
- `docker-compose.yml` - Local development environment
- `pyproject.toml` - Python dependencies and project configuration

## Development

### Local Development

```bash
# Navigate to agents directory
cd agents

# Run with Docker Compose
docker-compose up

# Or build and run manually
docker build -t healthcare-assistant .
docker run -p 8080:8080 healthcare-assistant
```

### Environment Variables

See `docker-compose.yml` for the complete list of environment variables needed for configuration.

### Deployment

The agent is deployed using AWS CDK with Bedrock AgentCore Runtime. The CDK stack automatically builds and deploys the container to ECR.

```bash
# Deploy from project root
cdk deploy AssistantStack
```
