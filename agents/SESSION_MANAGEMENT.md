# Healthcare Assistant - S3 Session Management

This document describes the implementation of session management for the healthcare assistant using Strands Agents with Amazon S3 storage and Bedrock Knowledge Base integration.

## Overview

The session management system automatically saves medical conversations as notes with patient context metadata, enabling:

- **Patient-specific note organization**: Notes are stored in patient-specific S3 prefixes
- **Conversation persistence**: Full conversation history is maintained across sessions
- **Context preservation**: Patient information is preserved and accessible across interactions
- **Knowledge base integration**: Notes can be ingested into Bedrock Knowledge Base for retrieval

## Architecture

```
S3 Bucket Structure (Consistent with Document Processing):
processed/
├── patient_123_medical_notes/
│   └── session_20241028_143022/
│       ├── session.json
│       └── agents/
│           └── agent_healthcare/
│               ├── agent.json
│               └── messages/
│                   ├── message_0.json
│                   ├── message_1.json
│                   └── ...
├── patient_456_medical_notes/
│   └── session_20241028_144530/
│       └── ...
├── patient_123_document_name/     # Document processing uses same pattern
│   ├── extracted_data.json
│   └── result.html
└── unknown_medical_notes/         # Sessions without patient context
    └── session_20241028_145012/
        └── ...
```

## Configuration

### Environment Variables

```bash
# S3 Session Management
SESSION_BUCKET=ab2-cerozob-processeddata-us-east-1
SESSION_PREFIX=medical-notes/
AWS_REGION=us-east-1
ENABLE_SESSION_MANAGEMENT=true

# Agent Configuration
LOG_LEVEL=INFO
DEFAULT_LANGUAGE=es-LATAM
```

### Docker Compose

The session management is configured in `docker-compose.yml`:

```yaml
environment:
  - SESSION_BUCKET=${SESSION_BUCKET:-ab2-cerozob-processeddata-us-east-1}
  - SESSION_PREFIX=${SESSION_PREFIX:-medical-notes/}
  - ENABLE_SESSION_MANAGEMENT=${ENABLE_SESSION_MANAGEMENT:-true}
```

## Implementation Details

### Patient ID Extraction

The system automatically extracts patient IDs from user messages using various patterns:

```python
# Supported patterns:
- "paciente id: 123"
- "cedula: 12345678"
- "esta sesión es del paciente Juan_Perez"
- "notas del paciente Maria_Garcia"
```

### Session Manager Creation

```python
from strands.session.s3_session_manager import S3SessionManager

def create_session_manager(session_id: str, patient_id: str = None):
    if patient_id:
        prefix = f"medical-notes/patients/{patient_id}/"
    else:
        prefix = f"medical-notes/no-patient/"
    
    return S3SessionManager(
        session_id=session_id,
        bucket="ab2-cerozob-processeddata-us-east-1",
        prefix=prefix,
        region_name="us-east-1"
    )
```

### Agent with Session Management

```python
from strands import Agent

# Create agent with session management
agent = Agent(
    system_prompt=HEALTHCARE_SYSTEM_PROMPT,
    session_manager=session_manager,
    callback_handler=None
)

# Add patient context to agent state
if patient_id:
    agent.state["patient_id"] = patient_id
    agent.state["session_context"] = "patient_session"
```

## API Integration

### AgentCore Invocation

The Lambda handler passes session information to the agent:

```python
# Extract session ID and patient context
session_id = body.get('sessionId', f'agentcore_session_{uuid.uuid4().hex}')
patient_id = extract_patient_id_from_message(message_content)

# Prepare payload with session management
payload_data = {
    "prompt": message_content,
    "sessionId": session_id
}
```

### Response Format

The agent returns enhanced responses with session information:

```json
{
  "message": "Respuesta del asistente médico...",
  "timestamp": "2024-10-28T14:30:22Z",
  "model": "healthcare-assistant",
  "capabilities": ["patient_info", "appointments", "knowledge_base", "documents", "session_management"],
  "session_id": "agentcore_session_abc123",
  "patient_context": {
    "patient_id": "Juan_Perez_123",
    "has_patient_context": true,
    "session_prefix": "medical-notes/patients/Juan_Perez_123/"
  },
  "session_info": {
    "bucket": "ab2-cerozob-processeddata-us-east-1",
    "region": "us-east-1",
    "notes_saved": true,
    "conversation_persisted": true
  }
}
```

## Usage Examples

### Patient Session

```python
# User message with patient context
message = "Esta sesión es del paciente Juan_Perez_123. Tengo dolor de cabeza."

# System automatically:
# 1. Extracts patient_id = "Juan_Perez_123"
# 2. Creates session manager with prefix "medical-notes/patients/Juan_Perez_123/"
# 3. Saves conversation to S3 with patient context
# 4. Returns response with session information
```

### General Session (No Patient)

```python
# User message without patient context
message = "¿Qué es la hipertensión?"

# System automatically:
# 1. Detects no patient context
# 2. Creates session manager with prefix "medical-notes/no-patient/"
# 3. Saves conversation to S3 without patient context
```

### Session Continuation

```python
# Using existing session_id automatically restores conversation history
agent = create_healthcare_agent(existing_session_id, patient_id)
# Agent now has full conversation history from S3
```

## S3 Storage Structure

### Session Metadata (`session.json`)

```json
{
  "session_id": "agentcore_session_abc123",
  "session_type": "AGENT",
  "created_at": "2024-10-28T14:30:22Z",
  "updated_at": "2024-10-28T14:35:45Z"
}
```

### Agent State (`agent.json`)

```json
{
  "agent_id": "healthcare_assistant",
  "state": {
    "patient_id": "Juan_Perez_123",
    "session_context": "patient_session",
    "metadata": {
      "timestamp": "2024-10-28T14:30:22Z",
      "session_type": "medical_consultation",
      "patient_context": {
        "patient_id": "Juan_Perez_123",
        "has_patient_context": true
      }
    }
  },
  "conversation_manager_state": {},
  "created_at": "2024-10-28T14:30:22Z",
  "updated_at": "2024-10-28T14:35:45Z"
}
```

### Message Storage (`message_0.json`)

```json
{
  "message": {
    "role": "user",
    "content": [
      {
        "type": "text",
        "text": "Esta sesión es del paciente Juan_Perez_123. Tengo dolor de cabeza."
      }
    ]
  },
  "redact_message": null,
  "message_id": 0,
  "created_at": "2024-10-28T14:30:22Z",
  "updated_at": "2024-10-28T14:30:22Z"
}
```

## Security and Privacy

### Patient Data Protection

- **Prefix Isolation**: Each patient's data is stored in a separate S3 prefix
- **Access Control**: S3 bucket policies control access to patient data
- **Encryption**: All data is encrypted at rest using S3 server-side encryption
- **Audit Trail**: CloudTrail logs all S3 access for compliance

### Data Sanitization

The system includes utilities for sanitizing sensitive information in logs:

```python
from shared.utils import sanitize_for_logging

# Automatically removes PII/PHI from logs
sanitized_data = sanitize_for_logging(user_data)
```

## Knowledge Base Integration

### Automatic Ingestion

The stored session data can be automatically ingested into Bedrock Knowledge Base:

1. **Session Completion**: When a session ends, trigger knowledge base ingestion
2. **Patient Context**: Include patient metadata in knowledge base documents
3. **Retrieval**: Use patient context to filter knowledge base queries

### Data Format for Knowledge Base

```json
{
  "content": "Conversation transcript...",
  "metadata": {
    "patient_id": "Juan_Perez_123",
    "session_id": "agentcore_session_abc123",
    "timestamp": "2024-10-28T14:30:22Z",
    "session_type": "medical_consultation",
    "source": "healthcare_assistant"
  }
}
```

## Monitoring and Observability

### CloudWatch Metrics

- Session creation rate
- Message storage success/failure
- Patient context detection rate
- S3 storage utilization

### Logging

```python
# Structured logging with patient context
logger.info("Session created", extra={
    "session_id": session_id,
    "patient_id": patient_id,
    "s3_prefix": prefix,
    "bucket": bucket_name
})
```

## Testing

### Running Examples

```bash
# Run the session management examples
cd agents
python session_management_example.py
```

### Unit Tests

```bash
# Run tests for session management
pytest tests/test_session_management.py -v
```

## Troubleshooting

### Common Issues

1. **S3 Access Denied**
   - Check IAM permissions for S3 bucket access
   - Verify bucket policy allows the Lambda execution role

2. **Session Not Found**
   - Verify session_id format and S3 prefix
   - Check if session was created in correct patient directory

3. **Patient ID Not Extracted**
   - Review patient ID extraction patterns
   - Add custom patterns for your use case

### Debug Commands

```bash
# List sessions for a patient
aws s3 ls s3://ab2-cerozob-processeddata-us-east-1/medical-notes/patients/Juan_Perez_123/

# Get session info via API
curl -X GET "https://api.example.com/sessions/agentcore_session_abc123/info"
```

## Best Practices

1. **Session ID Format**: Use descriptive, unique session IDs
2. **Patient ID Normalization**: Normalize patient IDs (remove spaces, special characters)
3. **Error Handling**: Implement robust error handling for S3 operations
4. **Monitoring**: Monitor S3 costs and storage usage
5. **Cleanup**: Implement session cleanup policies for old data
6. **Security**: Regular security audits of S3 access patterns

## Future Enhancements

- **Session Expiration**: Automatic cleanup of old sessions
- **Compression**: Compress large conversation histories
- **Search**: Full-text search across patient sessions
- **Analytics**: Patient interaction analytics and insights
- **Integration**: Direct integration with EHR systems
