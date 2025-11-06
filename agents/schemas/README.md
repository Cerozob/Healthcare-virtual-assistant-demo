# Healthcare Agent JSON Schemas

This directory contains JSON Schema definitions for all request and response types used by the healthcare agent system. These schemas ensure consistency and enable validation across the entire system.

## Schema Files

### 1. `send_message_request.json`
**Purpose**: Validates incoming requests from the frontend to the agent (Strands compatible format)  
**Used by**: Frontend → Agent API  
**Structure**:
```json
{
  "content": [
    {"text": "string"},
    {
      "image": {
        "format": "jpeg|png|gif|webp",
        "source": {"bytes": "base64_encoded_data"}
      }
    },
    {
      "document": {
        "format": "pdf|txt|doc|docx|md|csv|xls|xlsx|html",
        "name": "filename",
        "source": {"bytes": "base64_encoded_data"}
      }
    }
  ],
  "sessionId": "string (optional, min 33 chars for AgentCore)"
}
```

### 2. `agentcore_multimodal_request.json`
**Purpose**: Validates AgentCore runtime invocations with multimodal content  
**Used by**: AgentCore Runtime → Healthcare Agent  
**Structure**: Same as `send_message_request.json` but with AgentCore-specific validation rules and examples for healthcare use cases.

### 3. `agentcore_response.json`
**Purpose**: Validates healthcare agent responses from AgentCore runtime  
**Used by**: Healthcare Agent → Frontend (via AgentCore)  
**Structure**:
```json
{
  "response": "string (agent's response content)",
  "sessionId": "string (min 33 chars)",
  "patientContext": {
    "patientId": "string",
    "patientName": "string",
    "contextChanged": "boolean",
    "identificationSource": "tool_extraction|content_extraction|image_analysis|document_analysis|multimodal_analysis|default",
    "fileOrganizationId": "string (optional)",
    "aiIdentificationData": "object (optional)"
  },
  "memoryEnabled": "boolean",
  "memoryId": "string|null",
  "uploadResults": [
    {
      "success": "boolean",
      "content_type": "string",
      "s3_url": "string",
      "error": "string (if failed)",
      "patient_id": "string"
    }
  ],
  "timestamp": "datetime",
  "status": "success|error"
}
```

### 4. `chat_response.json`
**Purpose**: Validates healthcare agent responses (legacy format for frontend compatibility)  
**Used by**: Agent → Frontend Components  
**Structure**: Similar to agentcore_response but with legacy field names for backward compatibility.

### 5. `structured_output.json`
**Purpose**: Validates agent responses with full metadata (legacy format)  
**Used by**: Agent → Frontend (complete response format for backward compatibility)  
**Structure**: Legacy structured format with content/metadata separation.

### 6. `strands_multimodal_format.json`
**Purpose**: Documents the internal Strands Agent multimodal format  
**Used by**: Internal format conversion (AgentCore → Strands)  
**Structure**:
```json
[
  {"text": "string"},
  {
    "image": {
      "format": "jpeg",
      "source": {"bytes": "raw_bytes"}
    }
  },
  {
    "document": {
      "format": "txt",
      "name": "filename",
      "source": {"bytes": "raw_bytes"}
    }
  }
]
```

## Usage

### Python Validation
```python
from shared.schema_validator import validate_request, validate_response

# Validate incoming request
errors = validate_request(request_data)
if errors:
    return create_error_response(session_id, "INVALID_REQUEST", errors[0])

# Validate outgoing response  
errors = validate_response(response_data)
if errors:
    logger.error(f"Invalid response: {errors}")
```

### TypeScript Integration
The schemas can be used to generate TypeScript types:
```bash
# Generate TypeScript types from schemas
json2ts agents/schemas/send_message_request.json > types/SendMessageRequest.ts
```

### Decorators
Use validation decorators for automatic validation:
```python
from shared.schema_validator import validate_input, validate_output

@validate_input("send_message_request")
@validate_output("structured_output")
async def process_message(request_data):
    # Function automatically validates input and output
    pass
```

## Schema Validation Rules

### Request Validation
- `content` array is required with at least one content block
- `sessionId` is optional but must be minimum 33 characters for AgentCore compatibility
- Text blocks: 1-50,000 characters
- Image blocks: base64 encoded data in supported formats (jpeg, jpg, png, gif, webp)
- Document blocks: base64 encoded data with valid filename and supported formats

### Response Validation
- `response` string is required (agent's response content)
- `sessionId` must match request session ID (minimum 33 characters)
- `status` must be "success" or "error"
- `patientContext` follows strict identification source enum
- `uploadResults` array documents S3 upload outcomes
- `memoryEnabled` and `memoryId` track AgentCore Memory usage

### File Processing
- File processing results must include `fileId`, `fileName`, `status`
- Status must be one of: `processed`, `failed`, `skipped`
- Error messages required when status is `failed`

## Format Conversion

The system handles multimodal content in Strands-compatible format:

### Frontend → AgentCore Format (Request)
```json
{
  "content": [
    {"text": "Analyze this medical document"},
    {
      "document": {
        "format": "pdf",
        "name": "historial_medico.pdf",
        "source": {"bytes": "base64_encoded_data"}
      }
    }
  ],
  "sessionId": "agentcore_session_12345678-1234-1234-1234-123456789012"
}
```

### Strands Agent Format (Internal Processing)
```json
[
  {"text": "Analyze this medical document"},
  {
    "document": {
      "format": "pdf",
      "name": "historial_medico.pdf", 
      "source": {"bytes": "raw_bytes"}
    }
  }
]
```

### AgentCore → Frontend Format (Response)
```json
{
  "response": "He analizado el historial médico...",
  "sessionId": "agentcore_session_12345678-1234-1234-1234-123456789012",
  "patientContext": {
    "patientId": "juan_perez",
    "patientName": "Juan Pérez",
    "contextChanged": true,
    "identificationSource": "document_analysis"
  },
  "status": "success"
}
```

The healthcare agent processes content blocks in Strands format using the `_prepare_strands_content()` method, which converts base64 strings to bytes for internal processing.

## Benefits

1. **Consistency**: Ensures all components use the same data structures
2. **Validation**: Catches format errors early in development
3. **Documentation**: Schemas serve as living documentation
4. **Type Safety**: Can generate TypeScript types from schemas
5. **API Contracts**: Clear contracts between frontend and backend
6. **Format Compatibility**: Handles both AgentCore and Strands formats
7. **Testing**: Enables comprehensive validation testing

## Maintenance

When updating schemas:
1. Update the JSON schema file
2. Update corresponding TypeScript interfaces in `apps/frontend/src/types/api.ts`
3. Update Python models in `agents/shared/models.py` if applicable
4. Run validation tests to ensure compatibility
5. Update this README if new schemas are added

## Validation Testing

Test schema validation:
```bash
cd agents
python shared/schema_validator.py
```

This will load and validate all schemas, reporting any issues.
