# AgentCore Gateway Tools Test Script

Quick test script to list all tools available in the AgentCore Gateway.

## Usage

### Basic tool listing:
```bash
python test_gateway_tools.py
```

### With semantic search testing:
```bash
python test_gateway_tools.py --test-semantic-search
```

### JSON output:
```bash
python test_gateway_tools.py --json
```

## Prerequisites

1. **Environment Setup**: Make sure you have a `.env` file in the `agents/` directory with:
   ```
   MCP_GATEWAY_URL=https://agentcoregateway-xxxxxxxxxx.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp
   AWS_REGION=us-east-1
   GATEWAY_ID=your-gateway-id-here
   ```

2. **AWS Credentials**: Ensure your AWS credentials are configured (via AWS CLI, environment variables, or IAM role)

3. **Dependencies**: The script uses the existing agent dependencies from the `agents/` directory

## Expected Tools

Based on the infrastructure configuration, the gateway should expose these tools:

- **patients_api** - Patient management (CRUD operations)
- **medics_api** - Medical professionals management  
- **exams_api** - Medical exams and procedures
- **reservations_api** - Appointment scheduling
- **files_api** - Medical document management
- **patient_lookup** - Advanced patient search

## Tool Naming Convention

Tools in the AgentCore Gateway follow the pattern:
`{target-name}__{tool-name}`

For example:
- `healthcare-patients-api__patients_api`
- `healthcare-medics-api__medics_api`

## Troubleshooting

- **Rate Limiting**: The script includes built-in rate limiting (2 TPS) to respect AgentCore limits
- **Authentication**: Uses AWS SigV4 authentication via boto3 session credentials
- **Connection Issues**: Check that your gateway URL and AWS region are correct
