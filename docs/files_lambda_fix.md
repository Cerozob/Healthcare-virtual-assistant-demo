# Files Lambda Handler Fix

## Issue
The files Lambda was crashing with incomplete logs:
```
[INFO] Processing request to 
```

The agent reported "temporarily not working" in the frontend, even though everything looked normal.

## Root Cause
The files Lambda handler was trying to log an empty/None path, causing the log message to be incomplete and the function to crash. This happened when:

1. AgentCore Gateway invoked the Lambda directly (not through HTTP API Gateway)
2. The request format didn't match the expected HTTP API Gateway format
3. The Lambda tried to extract `path` from the event, which was None/empty

## Solution

### Changes to `lambdas/api/files/handler.py`

1. **Added comprehensive event logging**
   - Log all event keys for debugging
   - Log full event structure (with sensitive data handling)

2. **Fixed path logging crash**
   - Changed: `f"Processing {method} request to {path}"`
   - To: `f"Processing {method} request to {path or '(no path)'}"`

3. **Added support for direct AgentCore Gateway invocation**
   - Check if `action` field exists directly in the event (not just in body)
   - AgentCore Gateway may send: `{"action": "list", "patient_id": "123"}`
   - Not wrapped in a body field

4. **Improved error handling**
   - Return clear 400 error when request format is invalid
   - Include received event keys in error response
   - Add detailed logging for each routing type

### Request Format Support

The Lambda now supports three request formats:

1. **AgentCore Gateway (direct event)**
   ```json
   {
     "action": "list",
     "patient_id": "123",
     "file_type": "medical-history"
   }
   ```

2. **AgentCore Gateway (body wrapped)**
   ```json
   {
     "body": "{\"action\": \"list\", \"patient_id\": \"123\"}"
   }
   ```

3. **HTTP API Gateway**
   ```json
   {
     "httpMethod": "GET",
     "path": "/files",
     "queryStringParameters": {"patient_id": "123"}
   }
   ```

## How the Agent Uses files_api

The agent accesses the `files_api` tool through the information retrieval agent:

1. **Semantic Tool Discovery**: The information retrieval agent uses semantic search to find relevant tools
2. **Tool Matching**: The query "Medical files and document access, retrieval, and management" matches `files_api`
3. **Tool Invocation**: When the agent needs to list files, it calls the tool with action-based parameters
4. **AgentCore Gateway**: Routes the request to the files Lambda

## Deployment

```bash
cd infrastructure
cdk deploy AWSomeBuilder2-BackendStack --require-approval never
```

## Testing

After deployment, test the files API:

1. **Via Agent**: Ask "¿Qué archivos tiene el paciente Juan Pérez?"
2. **Via HTTP API**: `GET /files?patient_id=123`
3. **Via AgentCore Gateway**: Direct tool invocation with `{"action": "list", "patient_id": "123"}`

## Related Files

- `lambdas/api/files/handler.py` - Main handler with fixes
- `infrastructure/schemas/lambda_tool_schemas.py` - Tool schema definition
- `agents/info_retrieval/agent.py` - Agent that uses the tool
- `infrastructure/stacks/assistant_stack.py` - Gateway target configuration
