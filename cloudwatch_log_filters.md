# CloudWatch Log Filters for Agent Memory Debugging

Use these filter patterns in CloudWatch Logs to debug agent memory issues.

## Log Groups to Monitor

1. **AgentCore Runtime Logs**: `/aws/bedrock/agentcore/runtime/{RUNTIME_ID}`
2. **Healthcare Agent Logs**: Look for your agent's log group (likely in Lambda or ECS)

## Filter Patterns

### 1. Memory Operations
```
[timestamp, request_id, level="INFO", message="MEMORY_DEBUG:*"]
```

### 2. Session Management
```
[timestamp, request_id, level="INFO", message="SESSION_DEBUG:*"]
```

### 3. AgentCore Memory Operations
```
[timestamp, request_id, level="INFO", message="AGENTCORE_MEMORY:*"]
```

### 4. Memory Retrieval Operations
```
[timestamp, request_id, level="INFO", message="MEMORY_RETRIEVAL:*"]
```

### 5. Session Management Operations
```
[timestamp, request_id, level="INFO", message="SESSION_MANAGEMENT:*"]
```

### 6. All Memory-Related Logs (Combined)
```
[timestamp, request_id, level="INFO", message="MEMORY_DEBUG:*"] OR [timestamp, request_id, level="INFO", message="SESSION_DEBUG:*"] OR [timestamp, request_id, level="INFO", message="AGENTCORE_MEMORY:*"]
```

### 7. Specific Session ID
Replace `YOUR_SESSION_ID` with the actual session ID you're testing:
```
[timestamp, request_id, level, message="*YOUR_SESSION_ID*"]
```

### 8. Memory Failures Only
```
[timestamp, request_id, level="ERROR", message="*MEMORY*"] OR [timestamp, request_id, level="ERROR", message="*SESSION*"]
```

## Key Events to Look For

### Session Initialization
- `SESSION_INIT_START` - Agent initialization begins
- `MEMORY_SETUP_START` - Memory setup begins
- `MEMORY_SETUP_SUCCESS` - Memory setup completes
- `SESSION_INIT_SUCCESS` - Agent initialization completes

### Memory Operations
- `AGENTCORE_MEMORY_CONFIG_CREATED` - Memory configuration created
- `MEMORY_RETRIEVAL_CONTEXT_RETRIEVED` - Context retrieved from memory
- `SESSION_CONTINUITY_CHECK` - Session continuity verified

### Streaming Operations
- `MEMORY_STREAM_START` - Stream begins
- `MEMORY_TOOL_USE` - Tool usage during stream
- `MEMORY_RETRIEVAL_EVENT` - Memory retrieval during stream
- `MEMORY_STREAM_COMPLETE` - Stream completes

### Failures
- `SESSION_INIT_FAILURE` - Agent initialization failed
- `MEMORY_SETUP_FAILURE` - Memory setup failed
- `MEMORY_STREAM_FAILURE` - Stream failed

## Sample CloudWatch Insights Queries

### 1. Memory Operations Timeline
```sql
fields @timestamp, session_id, operation, duration_ms
| filter @message like /AGENTCORE_MEMORY/
| sort @timestamp desc
| limit 100
```

### 2. Session Consistency Check
```sql
fields @timestamp, session_id, event_type
| filter @message like /SESSION_DEBUG/
| stats count() by session_id
| sort count desc
```

### 3. Memory Retrieval Analysis
```sql
fields @timestamp, session_id, namespace, results_count
| filter @message like /MEMORY_RETRIEVAL/
| stats avg(results_count) by namespace
```

### 4. Error Analysis
```sql
fields @timestamp, session_id, error, error_type
| filter @level = "ERROR" and (@message like /MEMORY/ or @message like /SESSION/)
| stats count() by error_type
| sort count desc
```

### 5. Performance Analysis
```sql
fields @timestamp, session_id, operation, duration_ms
| filter @message like /AGENTCORE_MEMORY/ and duration_ms > 0
| stats avg(duration_ms), max(duration_ms), min(duration_ms) by operation
| sort avg desc
```

## Testing Workflow

1. **Start a test session** with the 3-prompt memory test
2. **Note the session ID** from the logs or debug panel
3. **Use the session-specific filter** to track that session
4. **Look for these key events**:
   - Session initialization
   - Memory setup
   - Context retrieval during each message
   - Any failures or errors

## Expected Log Flow for Successful Memory

1. `SESSION_INIT_START` - Agent starts
2. `MEMORY_SETUP_START` - Memory setup begins
3. `AGENTCORE_MEMORY_CONFIG_CREATED` - Memory configured
4. `MEMORY_SETUP_SUCCESS` - Memory ready
5. `SESSION_INIT_SUCCESS` - Agent ready
6. `MEMORY_STREAM_START` - First message
7. `MEMORY_RETRIEVAL_CONTEXT_RETRIEVED` - Context retrieved (may be empty for first message)
8. `MEMORY_STREAM_COMPLETE` - First message complete
9. `MEMORY_STREAM_START` - Second message
10. `MEMORY_RETRIEVAL_CONTEXT_RETRIEVED` - Context retrieved (should have data from first message)
11. `MEMORY_STREAM_COMPLETE` - Second message complete
12. And so on...

## Troubleshooting Common Issues

### No Memory Retrieval Events
- Check if `MEMORY_SETUP_SUCCESS` occurred
- Verify memory configuration in logs
- Look for `AGENTCORE_MEMORY_CONFIG_CREATED` event

### Empty Context Retrieval
- Check retrieval thresholds (0.3, 0.5, 0.7)
- Verify namespace configuration
- Look for `results_count: 0` in retrieval logs

### Session ID Inconsistency
- Look for multiple `SESSION_INIT_START` events
- Check for session ID changes in logs
- Verify frontend session management

### Memory Setup Failures
- Check AWS permissions for AgentCore
- Verify memory ID configuration
- Look for `MEMORY_SETUP_FAILURE` events
