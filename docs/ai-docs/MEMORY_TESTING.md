# AgentCore Memory Testing Guide

## Overview

The Healthcare Agent now includes AgentCore Memory integration for persistent short-term and long-term memory across conversations. This allows the agent to remember user preferences, medical information, and conversation context.

## Memory Configuration

- **Memory ID**: `HealthcareShortTermMemory-V9XVmfAXyb` (configured in `.env`)
- **Session Management**: Each conversation gets a unique session ID
- **Actor ID**: Daily-based user identifier for cross-session memory
- **Memory Strategies**: Preferences, facts, and summaries

## Testing Memory Functionality

### Test Sequence 1: Basic Memory Storage and Retrieval

1. **Store Preferences**:
   ```
   "I prefer morning appointments between 9-11 AM and I am allergic to penicillin and latex."
   ```

2. **Query Preferences**:
   ```
   "What do you know about my appointment preferences and allergies?"
   ```

3. **Verify Memory**:
   The agent should recall both the appointment time preference and allergies.

### Test Sequence 2: Healthcare Context Memory

1. **Store Medical Information**:
   ```
   "I have diabetes and take metformin twice daily. My last HbA1c was 7.2%."
   ```

2. **Store Additional Context**:
   ```
   "I also have high blood pressure and take lisinopril 10mg once daily."
   ```

3. **Query Medical History**:
   ```
   "What medications am I currently taking and what are my health conditions?"
   ```

4. **Verify Comprehensive Memory**:
   The agent should recall all medications and conditions from previous messages.

### Test Sequence 3: Cross-Session Memory (Same Day)

1. **First Session**: Store information as in Test 1
2. **New Session**: Start a new conversation (new session ID)
3. **Query Previous Information**:
   ```
   "Do you remember my appointment preferences from earlier?"
   ```

4. **Verify Cross-Session Memory**:
   The agent should recall information from the previous session (same actor ID).

## Memory Namespaces

The AgentCore Memory integration uses three namespaces:

- **`/preferences/{actorId}`**: User preferences across sessions
- **`/facts/{actorId}`**: Factual information about the user
- **`/summaries/{actorId}/{sessionId}`**: Session-specific conversation summaries

## Expected Behavior

✅ **Working Memory**:
- Agent recalls information from earlier in the conversation
- Agent remembers preferences across multiple exchanges
- Agent can reference previous medical information
- Agent maintains context throughout the session

❌ **Memory Issues**:
- Agent doesn't remember information from previous messages
- Agent asks for information already provided
- Agent loses context between exchanges

## Logging and Debugging

Memory operations are logged with structured events:
- `MEMORY_SETUP_START/SUCCESS/FAILURE`: Memory initialization
- `MEMORY_PROCESSING_START/SUCCESS/ERROR`: Memory usage during processing

Check CloudWatch logs for memory-related events with prefix `MEMORY_DEBUG:`.

## Configuration Details

```python
# Memory configuration in healthcare_agent.py
agentcore_memory_config = AgentCoreMemoryConfig(
    memory_id=self.config.agentcore_memory_id,
    session_id=self.session_id,
    actor_id=actor_id,
    retrieval_config={
        "preferences": RetrievalConfig(top_k=5, relevance_score=0.7),
        "facts": RetrievalConfig(top_k=10, relevance_score=0.6),
        "summaries": RetrievalConfig(top_k=3, relevance_score=0.8)
    }
)
```

## Troubleshooting

If memory isn't working:

1. Check that `AGENTCORE_MEMORY_ID` is set in `.env`
2. Verify AWS permissions for AgentCore Memory
3. Check CloudWatch logs for memory-related errors
4. Ensure the memory resource exists in the AWS account
