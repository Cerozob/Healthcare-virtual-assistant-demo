# AgentCore Gateway Migration

This document outlines the architectural changes made to migrate from direct database access to using AWS Bedrock AgentCore Gateways for database operations.

## Overview

The original architecture had agents directly accessing the database through SQL queries. This has been refactored to use AgentCore Gateways, where agents call Lambda functions as tools through the gateway, following AWS best practices for agent-to-service communication.

## Architecture Changes

### Before (Direct Database Access)
```
Agents → Direct SQL Queries → Aurora Database
```

### After (AgentCore Gateway Pattern)
```
Agents → MCP Gateway Tools → AgentCore Gateway → Lambda Functions → Aurora Database
```

## Key Components Modified

### 1. Infrastructure Stack (`infrastructure/stacks/assistant_stack.py`)

**Added:**
- `lambda_functions` parameter to constructor to receive Lambda functions from API stack
- `_create_unified_lambda_gateway_target()` method to create a single gateway target with all tool schemas
- Import of tool schemas from separate `infrastructure/schemas/lambda_tool_schemas.py` file
- IAM permissions for AgentCore Gateway access
- Environment variables for gateway URL and ID

**Simplified Architecture:**
- Single gateway target instead of multiple targets (one per Lambda)
- All tool schemas defined in a single `inline_payload` array
- Cleaner, more maintainable code structure

### 2. Tool Schemas (`infrastructure/schemas/lambda_tool_schemas.py`)

**New file containing:**
- Individual schema functions for each Lambda API (patients, medics, exams, reservations, files)
- `get_all_tool_schemas()` function that returns all schemas as a list
- Complete input and output schema definitions
- Separated from infrastructure code for better maintainability

**Tool Schemas:**
Each Lambda function has a comprehensive tool definition with:
- `name`: Tool identifier (e.g., "patients_api")
- `description`: Human-readable description of the tool's purpose
- `input_schema`: JSON schema defining available actions, parameters, and validation rules
- `output_schema`: JSON schema defining the expected response structure from the Lambda function

The schemas include:
- Available actions (list, get, create, update, delete, etc.)
- Required and optional parameters with validation
- Data structures for requests and responses
- Pagination support
- Error handling patterns

### 2. Application Entry Point (`app.py`)

**Modified:**
- Pass Lambda functions from API stack to Assistant stack
- Create `lambda_functions` dictionary mapping function names to CDK constructs

### 3. Agent Configuration (`agents/shared/config.py`)

**Added:**
- `gateway_url`: AgentCore Gateway URL
- `gateway_id`: AgentCore Gateway identifier

### 4. MCP Gateway Tools (`agents/shared/mcp_gateway_tools.py`)

**New file providing:**
- `MCPGatewayClient`: HTTP client for gateway communication
- MCP tool functions for each data type:
  - `query_patients_mcp()`
  - `query_medics_mcp()`
  - `query_exams_mcp()`
  - `query_reservations_mcp()`
  - `query_files_mcp()`
- Convenience functions for common operations
- Proper error handling and logging

### 5. Agent Updates

**Appointment Scheduling Agent (`agents/appointment_scheduling/agent.py`):**
- Replaced direct API calls with MCP gateway tools
- Updated tool implementations:
  - `_schedule_appointment_tool()` → uses `schedule_appointment_mcp()`
  - `_check_availability_tool()` → uses `check_availability_mcp()`
  - `_get_appointments_tool()` → uses `query_reservations_mcp()`
  - `_cancel_appointment_tool()` → uses `query_reservations_mcp()`
  - `_get_medics_tool()` → uses `query_medics_mcp()`

**Information Retrieval Agent (`agents/info_retrieval/agent.py`):**
- Updated patient search tools to use MCP gateway
- `_search_patient_tool()` → uses `get_patient_by_id_mcp()` and `list_patients_mcp()`

### 6. Lambda Function Updates

**Patients Handler (`lambdas/api/patients/handler.py`):**
- Added `_is_mcp_gateway_event()` to detect MCP vs API Gateway requests
- Added `handle_mcp_gateway_request()` for action-based routing
- Supports both API Gateway (HTTP) and MCP Gateway (action-based) invocations

**Reservations Handler (`lambdas/api/reservations/handler.py`):**
- Similar dual-mode support for API Gateway and MCP Gateway
- Action-based routing for MCP requests
- Parameter mapping between MCP and API Gateway formats

## MCP Gateway Request Format

The MCP Gateway uses a standardized request format:

```json
{
  "method": "tools/call",
  "params": {
    "name": "patients_api",
    "arguments": {
      "action": "list",
      "pagination": {
        "limit": 50,
        "offset": 0
      }
    }
  }
}
```

## Lambda Function Action Support

### Patients API
- `list`: Get paginated list of patients
- `get`: Get specific patient by ID
- `create`: Create new patient
- `update`: Update existing patient
- `delete`: Delete patient

### Reservations API
- `list`: Get paginated list of reservations with filters
- `get`: Get specific reservation by ID
- `create`: Create new reservation/appointment
- `update`: Update existing reservation
- `delete`: Cancel reservation
- `check_availability`: Check medic availability

### Medics API
- `list`: Get paginated list of medics with specialty filter
- `get`: Get specific medic by ID
- `create`: Create new medic
- `update`: Update existing medic
- `delete`: Delete medic

### Exams API
- `list`: Get paginated list of exams with type filter
- `get`: Get specific exam by ID
- `create`: Create new exam
- `update`: Update existing exam
- `delete`: Delete exam

### Files API
- `list`: Get paginated list of files with filters
- `get`: Get specific file by ID
- `upload`: Upload new file
- `delete`: Delete file
- `classify`: Classify file content
- `search`: Search knowledge base

## Security and Permissions

### IAM Roles
- **Agent Runtime Role**: Permissions to invoke AgentCore Gateway and Lambda functions
- **Gateway IAM Role**: Credentials for gateway target authentication

### Gateway Authentication
- Uses AWS IAM for authentication
- Gateway targets configured with `GATEWAY_IAM_ROLE` credential provider

## Benefits of This Architecture

1. **Security**: No direct database access from agents
2. **Scalability**: Lambda functions handle database operations efficiently
3. **Maintainability**: Clear separation of concerns
4. **Monitoring**: Better observability through Lambda and Gateway metrics
5. **Compliance**: Follows AWS best practices for agent architectures
6. **Flexibility**: Supports both API Gateway (external) and MCP Gateway (internal) access

## Environment Variables

The following environment variables are now available to agents:

- `GATEWAY_URL`: AgentCore Gateway endpoint URL
- `GATEWAY_ID`: AgentCore Gateway identifier
- All existing database and API configuration remains for Lambda functions

## Migration Notes

1. **Backward Compatibility**: Lambda functions still support API Gateway for external access
2. **Gradual Migration**: Agents can be migrated one at a time
3. **Testing**: Both old and new patterns can coexist during transition
4. **Monitoring**: Enhanced logging for MCP Gateway requests

## Next Steps

1. **Deploy Infrastructure**: Deploy updated CDK stacks
2. **Test Gateway Connectivity**: Verify agent-to-gateway communication
3. **Monitor Performance**: Check latency and error rates
4. **Complete Migration**: Update remaining agents to use MCP tools
5. **Remove Legacy Code**: Clean up direct database access code once migration is complete

This migration establishes a robust, scalable, and secure architecture for agent-to-database communication using AWS Bedrock AgentCore Gateways.
