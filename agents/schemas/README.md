# Healthcare Agent JSON Schemas

This directory contains JSON Schema definitions for all request and response types used by the healthcare agent system. These schemas ensure consistency and enable validation across the entire system.

## Schema Files

### 1. `send_message_request.json`
**Purpose**: Validates incoming requests from the frontend to the agent (AgentCore format)  
**Used by**: Frontend → Agent API  
**Structure**:
```json
{
  "prompt": "string (required)",
  "sessionId": "string (optional)", 
  "media": {
    "type": "image|document|audio",
    "format": "jpeg|png|pdf|txt|etc",
    "data": "base64_encoded_content"
  }
}
```

### 2. `structured_output.json`
**Purpose**: Validates agent responses with full metadata  
**Used by**: Agent → Frontend (complete response format)  
**Structure**:
```json
{
  "content": {
    "message": "string",
    "type": "text|markdown"
  },
  "metadata": {
    "processingTimeMs": "number",
    "agentUsed": "string",
    "toolsExecuted": ["string"],
    "requestId": "string",
    "timestamp": "datetime",
    "sessionId": "string"
  },
  "patientContext": {
    "patientId": "string",
    "patientName": "string", 
    "contextChanged": "boolean",
    "identificationSource": "enum"
  },
  "fileProcessingResults": [...],
  "errors": [...],
  "success": "boolean"
}
```

### 3. `chat_response.json`
**Purpose**: Validates chat service responses (frontend interface)  
**Used by**: Chat Service → Frontend Components  
**Structure**: Similar to structured_output but with additional chat-specific fields like `messageId` and `isComplete`.

### 4. `loading_state.json`
**Purpose**: Validates loading state information during processing  
**Used by**: Frontend loading indicators  
**Structure**:
```json
{
  "isLoading": "boolean",
  "stage": "uploading|processing|analyzing|completing",
  "progress": "number (optional, 0-100)"
}
```

### 5. `strands_multimodal_format.json`
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
- `message` is required and must be 1-10,000 characters
- `sessionId` is optional, alphanumeric with dashes/underscores
- `attachments` limited to 10 files, each max 100MB
- File categories are restricted to predefined medical types

### Response Validation
- `content.message` and `content.type` are required
- `metadata` must include all timing and identification fields
- `success` boolean is required
- `errors` array is required when `success: false`
- `patientContext` follows strict identification source enum

### File Processing
- File processing results must include `fileId`, `fileName`, `status`
- Status must be one of: `processed`, `failed`, `skipped`
- Error messages required when status is `failed`

## Format Conversion

The system handles two different multimodal formats:

### AgentCore SDK Format (External API)
```json
{
  "prompt": "Analyze this image",
  "media": {
    "type": "image",
    "format": "jpeg",
    "data": "base64_encoded_data"
  }
}
```

### Strands Agent Format (Internal Processing)
```json
[
  {"text": "Analyze this image"},
  {
    "image": {
      "format": "jpeg", 
      "source": {"bytes": "raw_bytes"}
    }
  }
]
```

The healthcare agent processes content blocks in Strands format using the `_prepare_strands_content()` method.

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
