# Token Usage Optimization

## Problem

The agent was using ~40K input tokens per request, which is extremely high and causes:
- High costs
- Slower response times
- Potential context window issues

## Root Cause

Each specialized agent was loading **ALL 6 Lambda APIs** from the AgentCore Gateway:
1. `healthcare-patients-api`
2. `healthcare-medics-api`
3. `healthcare-exams-api`
4. `healthcare-reservations-api`
5. `healthcare-files-api`
6. `healthcare-patientlookup-api`

Each Lambda API has extensive OpenAPI specifications that get included in the model's context, resulting in:
- **~40K tokens** with all 6 APIs loaded
- Unnecessary tool specifications for operations the agent doesn't need

## Solution

Load only the specific tools each agent actually needs:

### Information Retrieval Agent
**Tools loaded (3):**
- `healthcare-patients-api` - Patient CRUD operations
- `healthcare-patientlookup-api` - Advanced patient search
- `healthcare-files-api` - Medical document access
- Plus: `memory` and `retrieve` tools for knowledge base

**Why these tools:**
- Patient information queries require patient lookup and file access
- Medical document searches need file API
- Knowledge base integration for long-term memory

**Excluded:**
- ❌ `healthcare-medics-api` - Not needed for patient info retrieval
- ❌ `healthcare-exams-api` - Not needed for patient info retrieval
- ❌ `healthcare-reservations-api` - Not needed for patient info retrieval

### Appointment Scheduling Agent
**Tools loaded (2):**
- `healthcare-reservations-api` - Appointment CRUD and availability checking
- `healthcare-medics-api` - Doctor/staff information for scheduling

**Why these tools:**
- Appointment scheduling requires reservation management
- Need doctor availability and information

**Excluded:**
- ❌ `healthcare-patients-api` - Basic patient info comes from orchestrator
- ❌ `healthcare-patientlookup-api` - Not needed for scheduling
- ❌ `healthcare-exams-api` - Not needed for scheduling
- ❌ `healthcare-files-api` - Not needed for scheduling

### Healthcare Orchestrator Agent
**Tools loaded (2):**
- `appointment_scheduling_agent` - Specialized agent for appointments
- `information_retrieval_agent` - Specialized agent for patient info
- Plus: `memory` tool for explicit knowledge storage

**Why these tools:**
- Orchestrator only needs to delegate to specialized agents
- No direct API access needed
- Memory tool for storing important facts

**Excluded:**
- ❌ All 6 Lambda APIs - Handled by specialized agents

## Expected Results

### Before Optimization
```
Input tokens: ~40,000
- System prompt: ~2,000 tokens
- Tool specifications (6 APIs): ~38,000 tokens
- User message: ~100 tokens
```

### After Optimization

**Information Retrieval Agent:**
```
Input tokens: ~15,000 (estimated)
- System prompt: ~2,000 tokens
- Tool specifications (3 APIs + 2 tools): ~13,000 tokens
- User message: ~100 tokens
```
**Reduction: ~62.5%**

**Appointment Scheduling Agent:**
```
Input tokens: ~10,000 (estimated)
- System prompt: ~2,000 tokens
- Tool specifications (2 APIs): ~8,000 tokens
- User message: ~100 tokens
```
**Reduction: ~75%**

**Healthcare Orchestrator:**
```
Input tokens: ~5,000 (estimated)
- System prompt: ~2,000 tokens
- Tool specifications (2 agents + 1 tool): ~3,000 tokens
- User message: ~100 tokens
```
**Reduction: ~87.5%**

## Implementation

### Code Changes

**IMPORTANT**: AgentCore Gateway transforms tool names, so we cannot use exact string matching. We must use **semantic search** to discover the right tools.

**Before (info_retrieval/agent.py):**
```python
# Get ALL tools - causes 40K tokens
all_tools = mcp_client.list_tools_sync()
info_retrieval_tools = all_tools  # All 6 APIs loaded
```

**After (info_retrieval/agent.py):**
```python
# Use semantic search to find only information retrieval tools
semantic_query = """
Patient information retrieval and medical data access tools:
- Patient CRUD operations (create, read, update, delete patient records)
- Advanced patient search and lookup by name, email, phone, cedula, ID
- Medical files and document access, retrieval, and management

DO NOT include: appointment scheduling, reservations, doctor availability
"""

info_retrieval_tools = agentcore_client.get_semantic_tools(
    semantic_query, 
    "information_retrieval"
)
```

**Before (appointment_scheduling/agent.py):**
```python
# Get ALL tools and filter with keywords - still loads all specs
all_tools = mcp_client.list_tools_sync()
scheduling_tools = _filter_tools_for_scheduling(all_tools, request)
```

**After (appointment_scheduling/agent.py):**
```python
# Use semantic search to find only appointment scheduling tools
semantic_query = """
Appointment scheduling and medical staff management tools:
- Appointment and reservation CRUD operations
- Check appointment availability and time slots
- Doctor and medical staff information, schedules, and availability

DO NOT include: patient information retrieval, patient lookup, medical files
"""

scheduling_tools = agentcore_client.get_semantic_tools(
    semantic_query,
    "appointment_scheduling"
)
```

### Why Semantic Search?

AgentCore Gateway transforms tool names when exposing Lambda functions as MCP tools. For example:
- Console name: `healthcare-patients-api`
- Gateway name: Could be `healthcare_patients_api_list`, `healthcare_patients_api_get`, etc.

Semantic search matches against:
1. **Tool names** (transformed by Gateway)
2. **Tool descriptions** (from OpenAPI specs)
3. **Operation summaries** (from Lambda schemas)

This ensures we find the right tools regardless of naming transformations.

## Monitoring

To verify the optimization is working, check the telemetry logs:

```python
# Look for these log entries
logger.info(f"📋 Total available tools: {len(all_tools)}")
logger.info(f"✅ Loaded {len(info_retrieval_tools)} specific tools")

# Check token usage in response metrics
response["metrics"]["metricsSummary"]["accumulated_usage"]["inputTokens"]
```

## Best Practices

1. **Principle of Least Privilege**: Only load tools the agent actually needs
2. **Semantic Search Queries**: Use focused semantic queries with positive and negative examples
   - ✅ Include: Describe what tools you WANT
   - ❌ Exclude: Explicitly state what tools you DON'T want
3. **Agent Specialization**: Each agent should have a narrow, well-defined purpose
4. **Tool Delegation**: Orchestrator delegates to specialized agents rather than having all tools
5. **Regular Audits**: Periodically review which tools each agent actually uses
6. **Semantic Query Design**:
   - Be specific about operations needed (CRUD, search, availability)
   - Use domain terminology (patient, appointment, medical, doctor)
   - Include negative examples to exclude irrelevant tools
   - Test queries to ensure they return the right tools

## Future Optimizations

1. **Lazy Tool Loading**: Load tools only when needed during execution
2. **Tool Caching**: Cache tool specifications across requests
3. **Compressed Specs**: Use abbreviated tool descriptions for common operations
4. **Dynamic Tool Selection**: Load tools based on user query analysis
5. **Tool Versioning**: Use lightweight tool versions for simple operations

## Cost Impact

Assuming Claude 3.5 Sonnet pricing:
- Input: $3.00 per 1M tokens
- Output: $15.00 per 1M tokens

**Before (40K input tokens per request):**
- 1,000 requests = 40M input tokens = $120

**After (15K input tokens per request - info retrieval):**
- 1,000 requests = 15M input tokens = $45
- **Savings: $75 per 1,000 requests (62.5% reduction)**

**After (10K input tokens per request - appointment):**
- 1,000 requests = 10M input tokens = $30
- **Savings: $90 per 1,000 requests (75% reduction)**

## Verification Steps

1. **Check logs** for tool loading:
   ```bash
   # Should see "Loaded X specific tools" not "Retrieved 6 total tools"
   grep "Loaded.*specific tools" agents.log
   ```

2. **Monitor token usage** in telemetry:
   ```bash
   # Should see ~15K or less, not 40K
   grep "inputTokens" agents.log
   ```

3. **Test functionality**:
   - Info retrieval should still work for patient queries
   - Appointment scheduling should still work for bookings
   - No functionality should be lost

## Rollback Plan

If issues occur, revert to loading all tools:

```python
# Emergency rollback - load all tools
all_tools = mcp_client.list_tools_sync()
agent_tools = all_tools  # Use all tools
```

Then investigate which specific tool was needed but not loaded.
