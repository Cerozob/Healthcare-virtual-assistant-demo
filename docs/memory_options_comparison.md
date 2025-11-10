# Memory Persistence Options in Strands Agents

## Overview

There are three main approaches to memory persistence in Strands Agents for your healthcare application:

## Option 1: AgentCore Memory (Session Manager) ✅ CURRENT

### What It Is
A session manager that automatically handles conversation history and memory persistence using Amazon Bedrock AgentCore Memory.

### How It Works
```python
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

session_manager = AgentCoreMemorySessionManager(
    agentcore_memory_config=agentcore_memory_config,
    region_name=self.config.aws_region
)

agent = Agent(
    model=bedrock_model,
    system_prompt=get_prompt("healthcare"),
    tools=tools,
    session_manager=session_manager  # Automatic memory management
)
```

### Features
- ✅ **Automatic conversation persistence**: No need for agent to explicitly store history
- ✅ **Short-term memory (STM)**: Conversation history within a session
- ✅ **Long-term memory (LTM)**: User preferences, facts, and session summaries
- ✅ **Multiple strategies**:
  - `summaryMemoryStrategy`: Summarizes conversation sessions
  - `userPreferenceMemoryStrategy`: Learns user preferences
  - `semanticMemoryStrategy`: Extracts factual information
- ✅ **Namespace-based organization**: `/preferences/{actorId}`, `/facts/{actorId}`, `/summaries/{actorId}/{sessionId}`
- ✅ **Seamless integration**: Works with Strands session management

### Pros
- Automatic - no agent decision-making needed
- Comprehensive memory strategies
- Production-ready
- Handles session continuity automatically
- No additional tool calls (saves tokens)

### Cons
- Requires AgentCore Memory resource setup
- Currently limited to one agent per session
- Less explicit control over what gets stored
- Additional AWS service dependency

### Best For
- Production healthcare applications
- Automatic conversation continuity
- Patient context persistence across sessions
- Applications needing multiple memory strategies

---

## Option 2: Memory Tool (Bedrock Knowledge Base)

### What It Is
A tool that the agent can explicitly call to store and retrieve information from a Bedrock Knowledge Base.

### How It Works
```python
from strands_tools import memory

agent = Agent(
    model=bedrock_model,
    system_prompt=get_prompt("healthcare"),
    tools=[memory, appointment_scheduling_agent, information_retrieval_agent]
)

# Agent decides when to use memory
# Example: "Remember that the patient is allergic to penicillin"
# Agent calls: memory(action="store", content="Patient allergic to penicillin")

# Later: "What allergies does the patient have?"
# Agent calls: memory(action="retrieve", query="patient allergies")
```

### Features
- ✅ **Explicit control**: Agent decides what to store/retrieve
- ✅ **Bedrock Knowledge Base**: Uses existing KB infrastructure
- ✅ **Semantic search**: Retrieves relevant information based on similarity
- ✅ **Configurable parameters**: `min_score`, `max_results` for retrieval
- ✅ **Simple setup**: Just add the tool to the agent

### Pros
- Agent has explicit control over memory operations
- Can use existing Bedrock Knowledge Base
- More transparent (you see when memory is used)
- Can be combined with other approaches
- No AgentCore Memory resource needed

### Cons
- Agent must remember to use the tool
- Additional tool calls (more tokens, slower)
- Requires agent to understand when to store/retrieve
- No automatic conversation history
- Need to manage Knowledge Base separately

### Best For
- Explicit knowledge management
- When you already have a Bedrock Knowledge Base
- Applications where agent should decide what to remember
- Supplementing automatic memory with explicit storage

---

## Option 3: Hybrid Approach (Recommended for Healthcare)

### What It Is
Combine AgentCore Memory for automatic conversation history with the memory tool for explicit knowledge storage.

### How It Works
```python
from strands_tools import memory
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

# Setup AgentCore Memory for automatic conversation history
session_manager = AgentCoreMemorySessionManager(
    agentcore_memory_config=agentcore_memory_config,
    region_name=self.config.aws_region
)

# Add memory tool for explicit knowledge storage
agent = Agent(
    model=bedrock_model,
    system_prompt=get_prompt("healthcare"),
    tools=[
        memory,  # Explicit knowledge storage
        appointment_scheduling_agent,
        information_retrieval_agent
    ],
    session_manager=session_manager  # Automatic conversation history
)
```

### Features
- ✅ **Automatic conversation history**: Via AgentCore Memory Session Manager
- ✅ **Explicit knowledge storage**: Via memory tool when agent decides
- ✅ **Best of both worlds**: Automatic + explicit control
- ✅ **Flexible**: Agent can store important facts explicitly while conversation flows automatically

### Use Cases
- **AgentCore Memory (automatic)**:
  - Conversation history
  - Patient context across messages
  - Session continuity
  
- **Memory Tool (explicit)**:
  - Important medical facts: "Patient allergic to penicillin"
  - Long-term patient preferences: "Patient prefers morning appointments"
  - Critical information: "Patient has diabetes, requires insulin"

### Pros
- Combines automatic and explicit memory
- Conversation history is guaranteed
- Agent can store critical information explicitly
- Flexible for different use cases

### Cons
- More complex setup
- Two memory systems to manage
- Potential for confusion about which memory to use

### Best For
- Healthcare applications needing both automatic and explicit memory
- Critical information that must be explicitly stored
- Applications where some information is more important than others

---

## Comparison Table

| Feature | AgentCore Memory | Memory Tool | Hybrid |
|---------|-----------------|-------------|--------|
| **Automatic conversation history** | ✅ Yes | ❌ No | ✅ Yes |
| **Explicit control** | ❌ No | ✅ Yes | ✅ Yes |
| **Setup complexity** | Medium | Low | High |
| **Token usage** | Low | High | Medium |
| **Agent decision required** | No | Yes | Partial |
| **Production ready** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Multiple memory strategies** | ✅ Yes | ❌ No | ✅ Yes |
| **Requires AgentCore Memory** | ✅ Yes | ❌ No | ✅ Yes |
| **Requires Knowledge Base** | ❌ No | ✅ Yes | ⚠️ Optional |

---

## Recommendation for Your Healthcare Application

### Keep AgentCore Memory (Current Setup) ✅

**Why:**
1. **Automatic conversation persistence**: Critical for healthcare where you can't rely on the agent remembering to store history
2. **Patient context continuity**: Ensures patient information persists across messages
3. **Session management**: Handles session continuity automatically
4. **Production-ready**: Designed for production applications
5. **Already integrated**: You've already set it up and it's working

### Optionally Add Memory Tool

**When to add:**
- If you need explicit control over specific medical facts
- If you want the agent to decide what's important to remember long-term
- If you already have a Bedrock Knowledge Base for medical information

**How to add:**
```python
# In healthcare_agent.py _setup_all_tools method
from strands_tools import memory

def _setup_all_tools(self) -> List[Any]:
    tools = []
    
    # Add memory tool for explicit knowledge storage (optional)
    if self.config.enable_memory_tool:  # Add config flag
        tools.append(memory)
    
    # Add specialized agent tools
    tools.extend([appointment_scheduling_agent, information_retrieval_agent])
    
    return tools
```

---

## Summary

**Current Setup (AgentCore Memory)**: ✅ **Keep it!**
- Provides automatic conversation persistence
- Handles session continuity
- Production-ready for healthcare applications

**Memory Tool**: ⚠️ **Optional Enhancement**
- Add only if you need explicit control over specific knowledge storage
- Useful for critical medical facts that must be explicitly stored
- Can supplement AgentCore Memory, not replace it

**Recommendation**: Stick with AgentCore Memory for now. It's the right choice for your healthcare application. Consider adding the memory tool later if you find specific use cases where the agent needs explicit control over knowledge storage.
