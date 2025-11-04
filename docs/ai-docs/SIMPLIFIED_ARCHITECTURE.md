# Simplified Agent Architecture

## Overview

The agent architecture has been simplified and improved to use semantic tool filtering and proper separation of concerns. Each specialized agent now gets only the tools relevant to its domain.

## Architecture Improvements

### Before (Problems)
❌ **All agents got ALL MCP tools** - inefficient and confusing  
❌ **Patient lookup in main healthcare agent** - wrong separation of concerns  
❌ **No semantic filtering** - tools not matched to agent purpose  
❌ **Duplicated functionality** across agents  

### After (Solutions)
✅ **Semantic tool filtering** - each agent gets relevant tools only  
✅ **Patient lookup in information retrieval agent** - proper domain separation  
✅ **Efficient tool distribution** - no unnecessary tool overlap  
✅ **Clean separation of concerns** - each agent has clear responsibilities  

## Agent Responsibilities

### 1. Healthcare Agent (Orchestrator)
**Role**: Main orchestrator and multimodal content handler
**Tools**: 
- Appointment Scheduling Agent
- Information Retrieval Agent
- Multimodal upload capabilities

**Responsibilities**:
- Orchestrate conversations
- Handle multimodal content (images, documents)
- Upload files to S3 with patient organization
- Manage AgentCore Memory
- Route requests to specialized agents

### 2. Information Retrieval Agent
**Role**: Patient information and medical data queries
**Tools** (Semantically Filtered):
- Patient lookup tools (search by UUID, cédula, name)
- Medical record retrieval tools
- Document search tools
- Knowledge base queries
- **Patient identification tool** (local AI tool)

**Semantic Keywords**: `patient`, `search`, `lookup`, `find`, `get`, `retrieve`, `query`, `medical`, `record`, `history`, `document`, `file`, `data`, `cedula`, `name`, `id`, `information`, `details`

### 3. Appointment Scheduling Agent
**Role**: Appointment management and scheduling
**Tools** (Semantically Filtered):
- Appointment booking tools
- Calendar management tools
- Doctor availability tools
- Resource scheduling tools
- Basic patient lookup (for scheduling context)

**Semantic Keywords**: `appointment`, `schedule`, `book`, `reserve`, `calendar`, `availability`, `slot`, `time`, `date`, `cancel`, `modify`, `reschedule`, `doctor`, `medic`, `staff`, `resource`, `room`, `clinic`

## Semantic Tool Filtering

### How It Works
Each specialized agent analyzes the available MCP tools and filters them based on:

1. **Tool Name Analysis**: Matches keywords in tool names
2. **Tool Description Analysis**: Matches keywords in tool descriptions  
3. **Query Context**: Considers the specific request being processed
4. **Domain Exclusion**: Excludes tools from other domains

### Example Filtering

**Information Retrieval Query**: "Find patient Juan Pérez"
```python
# Gets tools like:
✅ patient_search_by_name
✅ patient_lookup_by_cedula  
✅ medical_record_retrieval
✅ document_search
❌ appointment_booking (excluded - scheduling domain)
❌ calendar_management (excluded - scheduling domain)
```

**Scheduling Query**: "Schedule appointment for Juan Pérez"
```python
# Gets tools like:
✅ appointment_booking
✅ calendar_management
✅ doctor_availability
✅ patient_lookup_basic (for scheduling context)
❌ medical_record_retrieval (excluded - info retrieval domain)
❌ document_search (excluded - info retrieval domain)
```

## Patient Identification Flow

### New Simplified Flow
1. **User Query** → Healthcare Agent (orchestrator)
2. **Patient Context Needed** → Information Retrieval Agent
3. **AI Patient Identification** → Uses local `identify_patient_from_conversation` tool
4. **Database Lookup** → Uses semantically filtered MCP tools
5. **Result** → Patient context returned to healthcare agent

### Benefits
- **Single Responsibility**: Patient identification is clearly owned by info retrieval agent
- **Semantic Tool Access**: Info retrieval agent gets patient-related MCP tools
- **No Duplication**: Patient lookup logic exists in one place
- **Proper Separation**: Each agent handles its domain

## Tool Distribution

### Healthcare Agent Tools
```python
tools = [
    appointment_scheduling_agent,  # Specialized agent
    information_retrieval_agent    # Specialized agent  
]
# No direct MCP tools - delegates to specialized agents
```

### Information Retrieval Agent Tools
```python
tools = [
    # Semantically filtered MCP tools from Gateway:
    patients_api,              # Patient CRUD operations and search
    medics_api,               # Medical staff information  
    exams_api,                # Medical exam types
    files_api,                # Medical document management
    # Other filtered tools based on semantic matching
]
```

### Appointment Scheduling Agent Tools
```python
tools = [
    # Semantically filtered MCP tools:
    appointment_booking,
    calendar_management,
    doctor_availability,
    resource_scheduling,
    patient_lookup_basic  # Basic patient info for scheduling
]
```

## Benefits of New Architecture

### 1. Efficiency
- **Reduced Tool Overhead**: Each agent loads only relevant tools
- **Faster Processing**: Less tool confusion and conflicts
- **Semantic Matching**: Tools matched to actual needs

### 2. Maintainability  
- **Clear Boundaries**: Each agent has well-defined responsibilities
- **Single Source of Truth**: Patient lookup in one place
- **Easier Debugging**: Clear tool ownership and usage

### 3. Scalability
- **Easy Extension**: Add new agents with semantic filtering
- **Tool Management**: New MCP tools automatically filtered to right agents
- **Domain Separation**: Changes in one domain don't affect others

### 4. User Experience
- **Faster Responses**: Agents work with focused tool sets
- **Better Accuracy**: Tools matched to query intent
- **Consistent Behavior**: Clear agent responsibilities

## Example Workflows

### Patient Information Query
```
User: "Find medical history for patient Juan Pérez, cédula 12345678"

Flow:
1. Healthcare Agent receives query
2. Routes to Information Retrieval Agent
3. Info Agent uses:
   - patients_api (list action to search by name/criteria)
   - patients_api (get action for specific patient_id)
   - files_api (list patient's medical documents)
4. Returns comprehensive patient information
```

### Appointment Scheduling
```
User: "Schedule appointment for María Elena tomorrow at 2 PM"

Flow:
1. Healthcare Agent receives query  
2. Routes to Appointment Scheduling Agent
3. Scheduling Agent uses:
   - patient_lookup_basic (basic patient info)
   - doctor_availability (check availability)
   - appointment_booking (create appointment)
4. Returns appointment confirmation
```

### Multimodal with Patient Context
```
User: "Here's an X-ray for patient Juan Pérez" [includes image]

Flow:
1. Healthcare Agent receives multimodal content
2. Routes patient identification to Information Retrieval Agent
3. Info Agent identifies patient using AI + MCP tools
4. Healthcare Agent uploads image to S3: s3://bucket/juan_perez/20241103_143022_a1b2c3d4_xray.jpg
5. Returns analysis with proper patient context
```

This simplified architecture provides better performance, clearer responsibilities, and easier maintenance while showcasing proper AI agent design patterns.
