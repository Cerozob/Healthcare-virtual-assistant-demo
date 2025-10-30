# Healthcare Agent Logging Configuration

This document explains the logging configuration for the Healthcare Agent, specifically designed to work with AgentCore and prevent WSGI server log suppression.

## Problem Statement

WSGI servers (like uvicorn) often suppress or redirect application logs, making them invisible in AgentCore CloudWatch logs. This configuration ensures all logs are properly visible.

## Solution Overview

The logging configuration uses multiple strategies to ensure log visibility:

1. **Force stdout output** - All logs go to stdout (required for AgentCore)
2. **Disable framework log handlers** - Prevent uvicorn from capturing logs
3. **Unbuffered output** - Immediate log visibility
4. **Comprehensive testing** - Multiple test scripts to verify logging works

## Files

### Core Configuration
- `logging_config.py` - Main logging configuration module
- `main.py` - Updated with AgentCore-optimized logging

### Testing Scripts
- `test_logging.py` - Standalone logging test (no framework)
- `test_mcp_gateway.py` - MCP Gateway integration test with logging
- `run_with_logging_test.py` - Production-like server test

## Quick Test

### 1. Test Basic Logging
```bash
cd agents
python test_logging.py
```

Expected output:
```
🧪 COMPREHENSIVE LOGGING TEST SUITE
====================================
🧪 BASIC LOGGING TEST (No Framework)
==================================================
2025-10-28 10:30:15 | DEBUG    | test_basic      | 🔍 Basic DEBUG message
2025-10-28 10:30:15 | INFO     | test_basic      | ℹ️ Basic INFO message
2025-10-28 10:30:15 | WARNING  | test_basic      | ⚠️ Basic WARNING message
2025-10-28 10:30:15 | ERROR    | test_basic      | ❌ Basic ERROR message
✅ Basic logging test complete
```

### 2. Test Agent Logging
```bash
cd agents
python -c "from logging_config import setup_agentcore_logging; setup_agentcore_logging()"
```

### 3. Test Full Server
```bash
cd agents
python run_with_logging_test.py
```

## Environment Variables

### Required for AgentCore
```bash
export PYTHONUNBUFFERED=1
export PYTHONIOENCODING=utf-8
export LOG_LEVEL=INFO
```

### Optional Configuration
```bash
export ENVIRONMENT=production
export AWS_REGION=us-east-1
export USE_MCP_GATEWAY=true
export MCP_GATEWAY_URL=https://your-gateway-url/mcp
```

## Deployment Configuration

### For AgentCore Deployment

1. **Set environment variables** in your deployment configuration
2. **Verify logging works** using the test scripts
3. **Monitor CloudWatch logs** for the structured log output

### Expected Log Format
```
2025-10-28 10:30:15 | INFO     | agents.main         | invoke_agent    | 🚀 === AGENT INVOCATION STARTED ===
2025-10-28 10:30:15 | INFO     | agents.main         | invoke_agent    | 📝 Request: prompt_length=25, sessionId=None
2025-10-28 10:30:15 | INFO     | agents.main         | invoke_agent    | 🔑 Session ID: healthcare_session_20251028_103015
```

## Troubleshooting

### Logs Not Visible

1. **Check environment variables**:
   ```bash
   echo $PYTHONUNBUFFERED
   echo $LOG_LEVEL
   ```

2. **Test basic logging**:
   ```bash
   python test_logging.py
   ```

3. **Check uvicorn configuration**:
   - Ensure `--access-log` is enabled
   - Use `--log-level info` or higher
   - Avoid `--quiet` flag

### Common Issues

#### Issue: No logs in CloudWatch
**Solution**: Ensure `PYTHONUNBUFFERED=1` and logs go to stdout

#### Issue: Logs appear locally but not in AgentCore
**Solution**: Check that stderr is redirected to stdout in the configuration

#### Issue: Framework logs missing
**Solution**: Verify framework loggers have `propagate=True`

### Verification Commands

```bash
# Test that logs go to stdout
python -c "import logging; logging.basicConfig(); logging.getLogger().info('TEST')" 2>&1

# Test environment variables
env | grep PYTHON

# Test agent configuration
cd agents && python -c "from main import logger; logger.info('AGENT TEST')"
```

## Production Checklist

- [ ] `PYTHONUNBUFFERED=1` set
- [ ] `LOG_LEVEL` configured appropriately
- [ ] Test scripts pass
- [ ] CloudWatch logs show structured output
- [ ] Request/response logging visible
- [ ] Error logs include full tracebacks
- [ ] MCP Gateway logs (if enabled) are visible

## Log Levels

- **DEBUG**: Detailed debugging information
- **INFO**: General operational messages (recommended for production)
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failures

## Performance Impact

The logging configuration is designed for minimal performance impact:
- Structured formatting is efficient
- Log levels can be adjusted to reduce verbosity
- Async logging doesn't block request processing
- Framework noise (boto3, urllib3) is reduced to WARNING level

## Support

If logging issues persist:
1. Run all test scripts and share output
2. Check AgentCore CloudWatch logs for any error messages
3. Verify environment variable configuration
4. Test with a minimal FastAPI application to isolate issues
