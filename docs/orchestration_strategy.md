# Orchestration Strategy: When to Use Direct Tools vs Specialized Agents

## Architecture Overview

The healthcare system uses a **hybrid orchestration pattern** where the main orchestrator has access to both:
1. **Direct MCP Tools** - Healthcare APIs (patients, medics, exams, reservations, files)
2. **Specialized Agents** - Domain-specific agents with their own tools

## Decision Criteria

### Use Direct MCP Tools When:

**Simple, straightforward operations:**
- ✅ "Show me patient with ID 12345"
- ✅ "List all cardiologists"
- ✅ "Get appointment details for reservation ID 789"
- ✅ "Create a new patient record"
- ✅ User provides exact IDs or complete information

**Characteristics:**
- Single API call needed
- Exact identifiers provided (patient_id, medic_id, etc.)
- No complex logic or coordination required
- Direct CRUD operations

**Benefits:**
- Faster (single LLM call)
- Lower token usage
- Simpler execution path

### Use Specialized Agents When:

**Complex operations requiring multiple steps or intelligence:**

#### appointment_scheduling_agent
- ✅ "Schedule appointment for Juan Pérez tomorrow at 3pm"
- ✅ "Find available slots for Dr. Smith next week"
- ✅ "Book a cardiology consultation for next Monday"

**Why specialized agent:**
- Needs to look up patient by name → patient_id
- Needs to find doctor by specialty → medic_id
- Needs to check availability
- Needs to coordinate multiple resources
- Requires workflow orchestration

#### information_retrieval_agent
- ✅ "Find patient named 'María' (partial name)"
- ✅ "Search for patients with cedula starting with 123"
- ✅ "Analyze this medical document and find the patient"
- ✅ "Show me all medical records for this patient"

**Why specialized agent:**
- Fuzzy/partial name matching
- Document analysis and content extraction
- Complex search across multiple fields
- Multimodal content processing (images, PDFs)

## Tool Distribution Strategy

### Healthcare Orchestrator
**Has access to:**
- ✅ All 6 MCP Healthcare APIs (for simple operations)
- ✅ `memory` tool (knowledge base)
- ✅ `appointment_scheduling_agent` (for complex scheduling)
- ✅ `information_retrieval_agent` (for complex searches)

**Token usage:** ~5-10K tokens (only loads when needed)

### Appointment Scheduling Agent
**Has access to:**
- ✅ Reservations API (appointments CRUD, availability)
- ✅ Medics API (doctor information)
- ✅ Exams API (exam types)
- ✅ Basic patient lookup (for getting patient_id)

**Why these tools:**
- Needs to coordinate appointments, doctors, and exams
- Needs basic patient lookup to convert "Juan Pérez" → patient_id
- Does NOT need advanced patient search or medical files

**Token usage:** ~10-15K tokens

### Information Retrieval Agent
**Has access to:**
- ✅ Patients API (patient CRUD)
- ✅ Patient Lookup API (advanced search)
- ✅ Files API (medical documents)
- ✅ `memory` tool (knowledge base)
- ✅ `retrieve` tool (Bedrock KB)

**Why these tools:**
- Specializes in finding and retrieving patient information
- Handles complex searches and document analysis
- Does NOT need appointment or doctor management

**Token usage:** ~15-20K tokens

## Example Workflows

### Example 1: Simple Patient Query
```
User: "Show me patient with ID 12345"
  ↓
Orchestrator (direct tool)
  → healthcare-patients-api(action="get", patient_id="12345")
  ↓
Response: Patient details
```
**Token usage:** ~5K tokens
**Speed:** Fast (1 LLM call)

### Example 2: Complex Appointment Scheduling
```
User: "Schedule appointment for Juan Pérez tomorrow at 3pm with cardiologist"
  ↓
Orchestrator (evaluates complexity)
  ↓ (delegates to specialized agent)
Appointment Scheduling Agent
  → healthcare-patients-api(action="list", name="Juan Pérez") → patient_id: "12345"
  → healthcare-medics-api(action="list", specialty="cardiology") → medic_id: "789"
  → healthcare-exams-api(action="list") → exam_id: "456"
  → healthcare-reservations-api(action="check_availability", medic_id="789", date="2024-01-15T15:00:00")
  → healthcare-reservations-api(action="create", patient_id="12345", medic_id="789", exam_id="456", date="2024-01-15T15:00:00")
  ↓
Orchestrator
  ↓
Response: Appointment confirmation
```
**Token usage:** ~10-15K tokens (specialized agent)
**Speed:** Moderate (2 LLM calls: orchestrator + agent)

### Example 3: Complex Patient Search
```
User: "Find patient named María with cedula starting with 123"
  ↓
Orchestrator (evaluates complexity)
  ↓ (delegates to specialized agent)
Information Retrieval Agent
  → healthcare-patientlookup-api(action="search", name="María", cedula_prefix="123")
  → Fuzzy matching and ranking
  ↓
Orchestrator
  ↓
Response: List of matching patients
```
**Token usage:** ~15-20K tokens (specialized agent)
**Speed:** Moderate (2 LLM calls: orchestrator + agent)

## Token Optimization Strategy

### Before Optimization (All agents load all tools)
- Orchestrator: 40K tokens (all 6 APIs)
- Appointment Agent: 40K tokens (all 6 APIs)
- Info Retrieval Agent: 40K tokens (all 6 APIs)
- **Total per complex request:** 80-120K tokens

### After Optimization (Semantic tool filtering)
- Orchestrator: 5-10K tokens (loads tools as needed)
- Appointment Agent: 10-15K tokens (4 APIs: reservations, medics, exams, basic patient)
- Info Retrieval Agent: 15-20K tokens (3 APIs: patients, patientlookup, files + KB tools)
- **Total per complex request:** 25-35K tokens

**Savings: 60-70% reduction in token usage**

## Why Some Tools Appear in Multiple Agents

### Patient Lookup Tools

**Basic patient lookup** (by exact name/ID):
- ✅ Orchestrator: For simple queries
- ✅ Appointment Agent: To convert "Juan Pérez" → patient_id during scheduling
- ❌ Info Retrieval Agent: Has advanced patient lookup instead

**Advanced patient search** (fuzzy, partial, document analysis):
- ❌ Orchestrator: Delegates to info retrieval agent
- ❌ Appointment Agent: Not needed for scheduling
- ✅ Info Retrieval Agent: Specializes in complex searches

### Design Principle: Minimal Overlap

Each agent gets the **minimum tools needed** for its specific purpose:
- Orchestrator: All tools for simple operations, delegates complex ones
- Specialized agents: Only tools needed for their domain
- Overlap is intentional and minimal (e.g., basic patient lookup for scheduling)

## Best Practices

1. **Evaluate Complexity First**: Orchestrator should assess if operation is simple or complex
2. **Prefer Direct Tools**: Use direct MCP tools for simple operations (faster, cheaper)
3. **Delegate Complexity**: Use specialized agents for multi-step workflows
4. **Minimize Tool Overlap**: Only include tools an agent actually needs
5. **Semantic Queries**: Use focused semantic queries to load only relevant tools
6. **Monitor Token Usage**: Track token usage to identify optimization opportunities

## Common Pitfalls to Avoid

❌ **Loading all tools in all agents** - Causes 40K+ token usage
❌ **Over-specialization** - Creating too many agents increases complexity
❌ **Under-specialization** - Orchestrator doing everything defeats the purpose
❌ **Exact name matching** - AgentCore Gateway transforms names, use semantic search
❌ **Ignoring workflow needs** - Appointment agent needs basic patient lookup for its workflow

## Monitoring and Optimization

### Metrics to Track
1. **Token usage per agent** - Should be 10-20K, not 40K
2. **Tool usage frequency** - Which tools are actually being called
3. **Agent delegation rate** - How often orchestrator delegates vs direct tools
4. **Response latency** - Direct tools should be faster than agents

### Optimization Opportunities
1. **Unused tools** - Remove tools that are never called
2. **Redundant delegation** - Simple operations being delegated unnecessarily
3. **Missing tools** - Agent failing because it lacks a needed tool
4. **Semantic query tuning** - Adjust queries to get exactly the right tools
