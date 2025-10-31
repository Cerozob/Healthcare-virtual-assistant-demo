# Semantic Search Deployment Guide

## Important Notes for AgentCore Gateway Semantic Search

### 🚨 **Critical Requirements:**

1. **Gateway Creation Only**: Semantic search can ONLY be enabled when creating a gateway, not when updating an existing one.

2. **Required IAM Permission**: The identity creating the gateway must have `bedrock-agentcore:SynchronizeGatewayTargets` permission.

3. **Unified Target Required**: Semantic search requires a single unified gateway target, not multiple individual targets.

### 🔄 **If You Have an Existing Gateway:**

If you already have an AgentCore Gateway deployed without semantic search, you need to:

1. **Delete the existing gateway** (this will require redeployment)
2. **Deploy with the new unified configuration**

```bash
# If you have an existing gateway, you may need to destroy and recreate
cdk destroy AWSomeBuilder2-VirtualAssistantStack
cdk deploy AWSomeBuilder2-VirtualAssistantStack
```

### ✅ **What's Configured:**

1. **Gateway Role Permissions:**
   - `bedrock-agentcore:SynchronizeGatewayTargets` ✅
   - `BedrockAgentCoreFullAccess` managed policy ✅
   - Lambda invoke permissions ✅

2. **Individual Targets Architecture:**
   - Individual gateway targets per Lambda function ✅
   - Direct Lambda invocation (no routing needed) ✅
   - Better observability and separation of concerns ✅
   - Gateway targets: `healthcare-patients-api`, `healthcare-medics-api`, etc. ✅

3. **Semantic Search Configuration:**
   - Gateway configured with `search_type="SEMANTIC"` ✅
   - MCP protocol configuration ✅

### 🧪 **Testing Semantic Search:**

After deployment, test semantic search functionality:

```bash
cd agents
python test_gateway_tools.py --test-semantic-search
```

### 🛠️ **How Individual Targets Work:**

1. **AgentCore Gateway** receives MCP tool calls with semantic search
2. **Gateway Target Selection** routes calls directly to appropriate Lambda:
   - `healthcare-patients-api___patients_api` → `healthcare-patients` Lambda
   - `healthcare-medics-api___medics_api` → `healthcare-medics` Lambda
   - `healthcare-exams-api___exams_api` → `healthcare-exams` Lambda
   - `healthcare-reservations-api___reservations_api` → `healthcare-reservations` Lambda
   - `healthcare-files-api___files_api` → `healthcare-files` Lambda
3. **Target Lambda** processes the healthcare request directly
4. **Response** flows back through gateway to client

### 📋 **Deployment Checklist:**

- [ ] Ensure you have `bedrock-agentcore:SynchronizeGatewayTargets` permission
- [ ] If existing gateway exists, plan for destroy/recreate
- [ ] Deploy backend stack first (creates unified router Lambda)
- [ ] Deploy assistant stack (creates gateway with semantic search)
- [ ] Test semantic search functionality
- [ ] Verify all healthcare tools are accessible

### 🔍 **Troubleshooting:**

**Error: "Search type cannot be updated to SEMANTIC"**
- Solution: Delete existing gateway and redeploy

**Error: "Access denied for SynchronizeGatewayTargets"**
- Solution: Add the required IAM permission to your deployment role

**Tools not found after deployment:**
- Check unified router Lambda logs
- Verify tool name mapping in router
- Test individual healthcare Lambda functions

### 🎯 **Expected Results:**

After successful deployment:
- ✅ Gateway supports semantic search queries
- ✅ All 5 healthcare tools available through individual targets
- ✅ Semantic search tool (`x_amz_bedrock_agentcore_search`) functional
- ✅ Healthcare agents can use semantic tool discovery
- ✅ Better observability per healthcare domain
