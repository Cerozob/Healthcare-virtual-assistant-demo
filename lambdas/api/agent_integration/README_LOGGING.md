# Enhanced Logging for AgentCore Integration

This document describes the enhanced logging capabilities implemented for the AgentCore integration Lambda function to improve debugging and monitoring of the AgentCore deployment.

## Overview

The enhanced logging system provides:
- **Structured JSON logging** for consistent log parsing
- **Request-scoped logging** with unique request IDs
- **Performance metrics** tracking for all operations
- **Detailed error information** with stack traces
- **AWS API call monitoring** with timing and success metrics
- **Contextual information** for debugging AgentCore issues

## Key Features

### 1. Structured JSON Logging

All log messages are formatted as JSON with consistent fields:

```json
{
  "timestamp": "2025-10-28T09:30:15.123Z",
  "level": "INFO",
  "logger": "agent_integration",
  "message": "AgentCore invocation completed successfully",
  "function": "handle_agentcore_chat",
  "line": 245,
  "request_id": "req_12345",
  "session_id": "agentcore_session_abc123",
  "agentcore_arn": "arn:aws:bedrock-agentcore:us-east-1:123456789012:agent-runtime/HEALTHCARE",
  "agentcore_duration_ms": 850.2
}
```

### 2. Request Tracking

Every request gets a unique `request_id` that appears in all related log messages, making it easy to trace a complete request flow through CloudWatch logs.

### 3. Performance Monitoring

Detailed timing information is captured for:
- **Total request duration**
- **SSM parameter retrieval time**
- **AgentCore invocation time**
- **Response processing time**

### 4. Error Handling

Enhanced error logging includes:
- **Error type classification**
- **AWS error codes and messages**
- **Stack traces for debugging**
- **Context information** (session ID, ARN, etc.)

### 5. AgentCore-Specific Logging

Special attention to AgentCore operations:
- **Runtime ARN tracking**
- **Session ID management**
- **Payload size monitoring**
- **Response validation**
- **Health check details**

## Log Levels and Usage

### INFO Level
- Request start/completion
- Successful operations
- Performance metrics
- Health check results

### DEBUG Level
- Request body parsing
- Attachment processing
- Response parsing details
- Internal state information

### WARNING Level
- Invalid HTTP methods
- Response parsing issues
- Rate limiting concerns

### ERROR Level
- AgentCore invocation failures
- AWS API errors
- Validation failures
- Unexpected exceptions

## Sample Log Messages

### Successful Request Flow

```json
{"timestamp": "2025-10-28T09:30:15.123Z", "level": "INFO", "message": "Request received: POST /agentcore/chat", "request_id": "req_12345", "source_ip": "10.0.1.100", "user_agent": "HealthcareApp/1.0"}

{"timestamp": "2025-10-28T09:30:15.145Z", "level": "INFO", "message": "Retrieved AgentCore runtime ARN successfully", "request_id": "req_12345", "agentcore_arn": "arn:aws:bedrock-agentcore:us-east-1:123456789012:agent-runtime/HEALTHCARE", "ssm_duration_ms": 22.5}

{"timestamp": "2025-10-28T09:30:15.167Z", "level": "INFO", "message": "Invoking AgentCore runtime", "request_id": "req_12345", "session_id": "agentcore_session_abc123", "payload_size_bytes": 512}

{"timestamp": "2025-10-28T09:30:16.012Z", "level": "INFO", "message": "AgentCore invocation completed successfully", "request_id": "req_12345", "session_id": "agentcore_session_abc123", "agentcore_duration_ms": 845.2}

{"timestamp": "2025-10-28T09:30:16.025Z", "level": "INFO", "message": "Chat request completed successfully", "request_id": "req_12345", "total_duration_ms": 902.1, "response_length": 245}
```

### Error Scenario

```json
{"timestamp": "2025-10-28T09:30:15.123Z", "level": "ERROR", "message": "AgentCore invocation failed: ValidationException - Invalid session ID format", "request_id": "req_12345", "session_id": "invalid_session", "agentcore_arn": "arn:aws:bedrock-agentcore:us-east-1:123456789012:agent-runtime/HEALTHCARE", "error_code": "ValidationException", "agentcore_duration_ms": 125.7}
```

### Health Check

```json
{"timestamp": "2025-10-28T09:30:15.123Z", "level": "INFO", "message": "Health check completed successfully", "request_id": "req_health_001", "health_session_id": "agentcore_health_check_xyz789", "agentcore_duration_ms": 234.5, "total_duration_ms": 267.8, "status": "healthy"}
```

## CloudWatch Log Insights Queries

Use these queries to analyze the enhanced logs in CloudWatch:

### Find All Requests for a Specific Session
```
fields @timestamp, message, request_id, session_id
| filter session_id = "agentcore_session_abc123"
| sort @timestamp asc
```

### Monitor AgentCore Performance
```
fields @timestamp, message, agentcore_duration_ms, total_duration_ms
| filter ispresent(agentcore_duration_ms)
| stats avg(agentcore_duration_ms), max(agentcore_duration_ms), min(agentcore_duration_ms) by bin(5m)
```

### Track Error Rates
```
fields @timestamp, message, error_code, level
| filter level = "ERROR"
| stats count() by error_code, bin(5m)
```

### Find Slow Requests
```
fields @timestamp, message, total_duration_ms, request_id
| filter total_duration_ms > 2000
| sort total_duration_ms desc
```

### Monitor Health Check Status
```
fields @timestamp, message, status, agentcore_duration_ms
| filter message like /Health check/
| sort @timestamp desc
```

## Debugging AgentCore Issues

### Common Issues and Log Patterns

1. **AgentCore Runtime Not Found**
   - Look for: `"error_code": "ParameterNotFound"`
   - Check SSM parameter configuration

2. **Invalid Session ID**
   - Look for: `"error_code": "ValidationException"`
   - Check session ID generation logic

3. **Timeout Issues**
   - Look for: `agentcore_duration_ms > 30000`
   - Check AgentCore runtime health

4. **Payload Issues**
   - Look for: `"error": "Invalid response from AgentCore"`
   - Check payload format and size

### Performance Analysis

Monitor these metrics:
- **SSM retrieval time**: Should be < 100ms
- **AgentCore response time**: Typically 500-2000ms
- **Total request time**: Should be < 5000ms
- **Payload sizes**: Monitor for unusually large payloads

## Testing the Logging

Run the test script to verify logging functionality:

```bash
cd lambdas/api/agent_integration
python test_logging.py
```

This will demonstrate all logging features and output sample structured logs.

## Integration with Monitoring

The structured logs integrate well with:
- **CloudWatch Dashboards**: Create metrics from log data
- **CloudWatch Alarms**: Alert on error rates or performance issues
- **AWS X-Ray**: Correlate with distributed tracing
- **Third-party tools**: Export structured logs to external systems

## Best Practices

1. **Always include request_id** in log messages
2. **Use appropriate log levels** (DEBUG for detailed info, ERROR for failures)
3. **Include timing information** for performance analysis
4. **Add contextual data** (session_id, agentcore_arn, etc.)
5. **Log both success and failure cases**
6. **Use structured data** instead of string concatenation
7. **Sanitize sensitive information** before logging

## Configuration

The logging system can be configured via environment variables:
- `LOG_LEVEL`: Set to DEBUG, INFO, WARNING, or ERROR
- `STRUCTURED_LOGGING`: Enable/disable structured JSON logging

## Troubleshooting

If logs are not appearing as expected:
1. Check Lambda function log level configuration
2. Verify CloudWatch log group permissions
3. Ensure structured formatter is properly applied
4. Check for any logging library conflicts
