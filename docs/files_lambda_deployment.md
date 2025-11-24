# Files Lambda Deployment Checklist

## Pre-Deployment

- [x] Fixed path logging crash in `lambda_handler`
- [x] Added support for direct AgentCore Gateway invocation
- [x] Added comprehensive event logging
- [x] Improved error handling and messages
- [x] Created test script
- [x] Created documentation

## Deployment Steps

1. **Review Changes**
   ```bash
   git diff lambdas/api/files/handler.py
   ```

2. **Run Local Tests** (optional)
   ```bash
   python lambdas/api/files/test_handler.py
   ```

3. **Deploy Backend Stack**
   ```bash
   cd infrastructure
   cdk deploy AWSomeBuilder2-BackendStack --require-approval never
   ```

4. **Monitor Deployment**
   - Watch CloudFormation console for stack updates
   - Verify Lambda function is updated
   - Check for any deployment errors

## Post-Deployment Verification

### 1. Check Lambda Logs
```bash
aws logs tail /aws/lambda/healthcare-files --follow
```

### 2. Test via Agent
Ask the agent: "¿Qué archivos tiene el paciente Juan Pérez?"

Expected behavior:
- Agent should use the `files_api` tool
- Lambda should log: "Using AgentCore Gateway routing (direct event) with action: list"
- Should return list of files (or empty array if none exist)

### 3. Test via HTTP API
```bash
curl -X GET "https://YOUR_API_URL/files?patient_id=test-123"
```

Expected behavior:
- Lambda should log: "Using HTTP API Gateway routing: GET /files"
- Should return 200 with files array

### 4. Check for Errors
Look for these log patterns:
- ✅ "Files Lambda invoked with event keys: [...]"
- ✅ "Using AgentCore Gateway routing (direct event) with action: list"
- ✅ "Processing AgentCore action: list"
- ❌ "Invalid request format" (should not appear for valid requests)
- ❌ "Unhandled error in files API" (should not appear)

## Rollback Plan

If issues occur:

1. **Quick Rollback**
   ```bash
   cd infrastructure
   git checkout HEAD~1 lambdas/api/files/handler.py
   cdk deploy AWSomeBuilder2-BackendStack --require-approval never
   ```

2. **Check Previous Version**
   ```bash
   aws lambda get-function --function-name healthcare-files
   ```

## Success Criteria

- [ ] Lambda deploys successfully
- [ ] No errors in CloudWatch logs
- [ ] Agent can list files for a patient
- [ ] HTTP API returns 200 for valid requests
- [ ] Invalid requests return 400 with clear error messages
- [ ] Log messages are complete (no truncated logs)

## Troubleshooting

### Issue: Lambda still crashes
- Check CloudWatch logs for full error message
- Verify event structure in logs
- Check if `parse_event_body` is working correctly

### Issue: Agent says "temporarily not working"
- Check if AgentCore Gateway is invoking the Lambda
- Verify tool schema in `lambda_tool_schemas.py`
- Check agent logs for tool invocation attempts

### Issue: Empty file list returned
- Verify Knowledge Base is configured
- Check if `KNOWLEDGE_BASE_ID` environment variable is set
- Test Knowledge Base query directly

## Related Documentation

- [Files Lambda Fix](./files_lambda_fix.md) - Detailed explanation of the fix
- [Lambda Tool Schemas](../infrastructure/schemas/lambda_tool_schemas.py) - Tool definitions
- [Information Retrieval Agent](../agents/info_retrieval/agent.py) - Agent that uses the tool
