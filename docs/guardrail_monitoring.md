# Guardrail Monitoring with Hooks

## Overview

The Healthcare Agent implements **shadow-mode guardrail monitoring** using Strands Hooks and Amazon Bedrock's ApplyGuardrail API. This approach allows you to track when guardrails would be triggered without actually blocking content, enabling you to monitor and tune your guardrails before enforcement.

## Architecture

### Components

1. **GuardrailMonitoringHook** (`agents/shared/guardrail_monitoring_hook.py`)
   - Implements `HookProvider` interface from Strands
   - Evaluates content using Bedrock ApplyGuardrail API
   - Logs violations without blocking responses
   - Provides detailed violation analysis

2. **Hook Integration** (`agents/healthcare_agent.py`)
   - Hook is registered with the Agent during initialization
   - Monitors both user input and assistant responses
   - Operates independently of model guardrail configuration

3. **Logging Infrastructure** (`agents/logging_config.py`)
   - Dedicated logger: `healthcare_agent.guardrail_monitoring`
   - Structured CloudWatch-compatible logging
   - Violation details captured for analysis

## How It Works

### Hook Lifecycle

```
User Input → MessageAddedEvent → check_message()
                                       ↓
                                  evaluate_content(INPUT)
                                       ↓
                                  Bedrock ApplyGuardrail API
                                       ↓
                                  Log violations + Store in hook.interventions
                                       ↓
Model Processing → Agent Response → AfterInvocationEvent
                                       ↓
                                  check_message()
                                       ↓
                                  evaluate_content(OUTPUT)
                                       ↓
                                  Bedrock ApplyGuardrail API
                                       ↓
                                  Log violations + Store in hook.interventions
                                       ↓
                                  Save to agent.state["guardrail_interventions"]
```

### Evaluation Process

1. **Content Extraction**: Text is extracted from Strands message content blocks
2. **API Call**: Content is sent to Bedrock ApplyGuardrail API
3. **Assessment**: API returns action (NONE or GUARDRAIL_INTERVENED) and detailed assessments
4. **Logging**: Violations are logged with full context for analysis
5. **State Storage**: Interventions are stored in agent state and included in response

## Monitored Guardrail Policies

### 1. Topic Policy
Detects discussions about blocked topics:
- **Cryptocurrency Trading**: Investment advice, trading strategies
- **Extreme Sports**: Dangerous activities without safety measures

**Log Format**:
```
🚫 Topic Policy Violation | source=INPUT | topic=TradingCriptomonedas | action=BLOCK | type=DENY
```

### 2. Content Policy
Detects harmful content types:
- **HATE**: Hate speech or discriminatory content
- **INSULTS**: Insulting or offensive language
- **VIOLENCE**: Violent or threatening content
- **SEXUAL**: Sexual or inappropriate content

**Log Format**:
```
⚠️ Content Policy Violation | source=OUTPUT | type=VIOLENCE | confidence=HIGH | action=BLOCK
```

### 3. Sensitive Information Policy (PII)
Detects personally identifiable information:

**Standard PII Entities**:
- AGE (monitored, not blocked)
- ADDRESS (anonymized in output)
- EMAIL (anonymized in output)
- PHONE (anonymized in output)
- CREDIT_DEBIT_CARD_NUMBER (anonymized in output)

**Healthcare-Specific Regex Patterns**:
- **CedulaColombia**: Colombian ID numbers (8-10 digits)
- **TelefonoLatam**: LATAM phone numbers
- **HistoriaClinica**: Medical record numbers
- **SeguroSocialLatam**: Social security numbers
- **LicenciaMedica**: Medical license numbers
- **PacienteID**: Patient ID numbers

**Log Format**:
```
🔒 PII Detected | source=INPUT | type=EMAIL | action=ANONYMIZE
🏥 Healthcare PII Detected | source=OUTPUT | pattern=CedulaColombia | action=ANONYMIZE
```

### 4. Contextual Grounding Policy
Detects responses that lack grounding or relevance:
- **GROUNDING**: Response not grounded in provided context
- **RELEVANCE**: Response not relevant to the query

**Log Format**:
```
📊 Grounding Violation | source=OUTPUT | type=GROUNDING | score=0.15 | threshold=0.2 | action=BLOCK
```

## Configuration

### Agent Configuration

The guardrail monitoring hook is initialized in `healthcare_agent.py`:

```python
# Create guardrail monitoring hook
guardrail_hook = create_guardrail_monitoring_hook(
    guardrail_id=config.guardrail_id,
    guardrail_version=config.guardrail_version,
    aws_region=config.aws_region,
    session_id=self.session_id
)

# Create agent with hook
self.agent = Agent(
    model=bedrock_model,
    system_prompt=get_prompt("healthcare"),
    tools=tools,
    session_manager=self.session_manager,
    hooks=[guardrail_hook]  # Add monitoring hook
)

# After processing, interventions are available in response
result = agent.process_message(content_blocks)
interventions = result.get("guardrailInterventions", [])
```

### Environment Variables

Required configuration (from `.env`):
```bash
# Guardrail Configuration
GUARDRAIL_ID=your-guardrail-id
GUARDRAIL_VERSION=DRAFT  # or specific version number
AWS_REGION=us-east-1
```

## Quick Start

### What is Shadow-Mode Monitoring?

Shadow-mode monitoring tracks when guardrails detect issues **without blocking content**. This captures:
- **GUARDRAIL_INTERVENED**: Content that would be blocked in enforcement mode
- **NONE with detections**: Content that triggers detection but doesn't meet intervention threshold

This allows you to:
- Monitor all guardrail activity in production without disrupting users
- Tune guardrail policies and thresholds before enforcement
- Generate compliance reports
- Identify false positives and tune sensitivity

### Implementation Overview

The implementation uses **Strands Hooks** to intercept messages and evaluate them with Bedrock's ApplyGuardrail API:

```
User Input → Hook → ApplyGuardrail API → Log + Store Violations → Continue Processing
                                                                        ↓
                                                                   Agent Response
                                                                        ↓
                                                                   Hook → ApplyGuardrail API
                                                                        ↓
                                                                   Log + Store Violations
                                                                        ↓
                                                                   Save to agent.state
                                                                        ↓
                                                                   Include in response
```

### Key Files

1. **`agents/shared/guardrail_monitoring_hook.py`** - Main hook implementation, evaluates content using Bedrock API, logs detailed violation information
2. **`agents/healthcare_agent.py`** - Integrates hook into agent initialization, passes guardrail configuration to hook
3. **`agents/logging_config.py`** - Configures dedicated logger for guardrail monitoring, ensures logs are visible in CloudWatch

## State Management

### Accumulation Across Conversation

Guardrail interventions are **accumulated across all messages** in a conversation session, providing a complete history of all detections.

**Why?**
- Complete audit trail of all guardrail activity
- See patterns across the conversation
- Comprehensive compliance tracking
- Full visibility into all detections without needing to check logs

### Hook Persistence

The `GuardrailMonitoringHook` instance **persists across messages** within the same session because:
- The agent is cached by session_id in `main.py`
- The hook is created once during agent initialization
- The hook remains attached to the agent for the entire session

### Intervention Lifecycle

```
Message 1:
  User Input → Check INPUT → Check OUTPUT → Append to interventions → Store in state → Return
  interventions = [detection1, detection2]

Message 2:
  User Input → Check INPUT → Check OUTPUT → Append to interventions → Store in state → Return
  interventions = [detection1, detection2, detection3]

Message 3:
  User Input → Check INPUT → Check OUTPUT → Append to interventions → Store in state → Return
  interventions = [detection1, detection2, detection3, detection4, detection5]
```

**Note**: Interventions accumulate throughout the session, providing a complete history.

## Testing

### Test Scenarios

Test the guardrail monitoring with these scenarios:

1. **Safe Healthcare Query**: "¿Cuáles son los horarios disponibles para citas?" - Should pass all guardrails
2. **Patient Information with PII**: "El paciente Juan Pérez con cédula 12345678 necesita una cita" - Detects names and cédulas
3. **Cryptocurrency Trading**: "¿Cómo puedo iniciar en el trading de criptomonedas?" - Detects blocked topic
4. **Extreme Sports**: "Necesito información sobre escalada sin equipo de seguridad" - Detects blocked topic
5. **Contact Information**: "Mi email es juan@example.com y mi teléfono es +57 300 1234567" - Detects email and phone PII

### Expected Output

```
🛡️ Guardrail monitoring initialized | guardrail_id=xxx | version=DRAFT
✅ Guardrail monitoring hooks registered

Test Case 1: Safe Healthcare Query
✅ Content passed guardrail check | source=INPUT | length=45

Test Case 2: Patient Information with PII
🚨 GUARDRAIL WOULD BLOCK | source=INPUT | content_preview=El paciente Juan Pérez...
🔒 PII Detected | source=INPUT | type=NAME | action=ANONYMIZE
🏥 Healthcare PII Detected | source=INPUT | pattern=CedulaColombia | action=ANONYMIZE
```

## CloudWatch Integration

### Log Groups

Guardrail monitoring logs are sent to CloudWatch with structured formatting:

```
2024-11-10 15:30:45 | WARNING  | HEALTHCARE_AGENT     | 🚨 GUARDRAIL WOULD BLOCK | source=INPUT | content_preview=...
2024-11-10 15:30:45 | WARNING  | HEALTHCARE_AGENT     | 🚫 Topic Policy Violation | source=INPUT | topic=TradingCriptomonedas
```

### CloudWatch Insights Queries

**Count violations by type**:
```sql
fields @timestamp, @message
| filter @message like /GUARDRAIL WOULD BLOCK/
| parse @message /source=(?<source>\w+)/
| stats count() by source
```

**Find PII detections**:
```sql
fields @timestamp, @message
| filter @message like /PII Detected/
| parse @message /type=(?<pii_type>\w+)/
| stats count() by pii_type
```

**Topic policy violations**:
```sql
fields @timestamp, @message
| filter @message like /Topic Policy Violation/
| parse @message /topic=(?<topic>\w+)/
| stats count() by topic
```

## Response Structure

The healthcare agent response now includes guardrail intervention data:

```json
{
  "response": "Agent response text...",
  "sessionId": "session-123",
  "patientContext": {...},
  "memoryEnabled": true,
  "uploadResults": [...],
  "timestamp": "2024-11-10T15:30:45.123Z",
  "status": "success",
  "metrics": {...},
  "guardrailInterventions": [
    {
      "source": "INPUT",
      "action": "GUARDRAIL_INTERVENED",
      "content_preview": "¿Cuál es la mejor criptomoneda...",
      "timestamp": "2024-11-10T15:30:45.000Z",
      "violations": [
        {
          "type": "topic_policy",
          "topic": "TradingCriptomonedas",
          "action": "BLOCK",
          "policy_type": "DENY"
        }
      ]
    },
    {
      "source": "OUTPUT",
      "action": "GUARDRAIL_INTERVENED",
      "content_preview": "El paciente Juan Pérez con cédula...",
      "timestamp": "2024-11-10T15:30:46.000Z",
      "violations": [
        {
          "type": "pii_regex",
          "pattern": "CedulaColombia",
          "action": "ANONYMIZE"
        }
      ]
    }
  ]
}
```

### Intervention Data Structure

Each intervention contains:
- **source**: "INPUT" or "OUTPUT"
- **action**: "GUARDRAIL_INTERVENED" or "NONE"
- **content_preview**: First 100 characters of flagged content
- **timestamp**: When the evaluation occurred
- **violations**: Array of specific violations detected

### Violation Types

**Topic Policy Violation:**
```json
{
  "type": "topic_policy",
  "topic": "TradingCriptomonedas",
  "action": "BLOCK",
  "policy_type": "DENY"
}
```

**Content Policy Violation:**
```json
{
  "type": "content_policy",
  "content_type": "VIOLENCE",
  "confidence": "HIGH",
  "action": "BLOCK"
}
```

**PII Entity Detection:**
```json
{
  "type": "pii_entity",
  "pii_type": "EMAIL",
  "action": "ANONYMIZE"
}
```

**PII Regex Detection:**
```json
{
  "type": "pii_regex",
  "pattern": "CedulaColombia",
  "action": "ANONYMIZE"
}
```

**Grounding Violation:**
```json
{
  "type": "grounding_policy",
  "grounding_type": "GROUNDING",
  "score": 0.15,
  "threshold": 0.2,
  "action": "BLOCK"
}
```

## Benefits of Shadow Mode

### 1. Non-Disruptive Monitoring
- Responses are never blocked
- Users experience normal functionality
- Violations are logged for analysis

### 2. Guardrail Tuning
- Identify false positives
- Adjust thresholds and policies
- Test changes before enforcement

### 3. Compliance Tracking
- Monitor PII exposure patterns
- Track policy violations
- Generate compliance reports

### 4. Performance Analysis
- Measure guardrail effectiveness
- Identify common violation patterns
- Optimize guardrail configuration

## Migration to Enforcement Mode

When ready to enforce guardrails:

### Option 1: Model-Level Enforcement
Update the BedrockModel configuration:
```python
bedrock_model = BedrockModel(
    model_id=config.model_id,
    guardrail_id=config.guardrail_id,
    guardrail_version=config.guardrail_version,
    guardrail_trace="enabled_full",
    guardrail_redact_input=True,   # Enable input redaction
    guardrail_redact_output=True,  # Enable output redaction
)
```

### Option 2: Hook-Level Enforcement
Modify the hook to block content:
```python
def evaluate_content(self, content: str, source: str) -> Optional[Dict[str, Any]]:
    response = self.bedrock_client.apply_guardrail(...)
    
    if response.get("action") == "GUARDRAIL_INTERVENED":
        # Block the content
        raise GuardrailViolationError("Content blocked by guardrail")
    
    return response
```

### Option 3: Hybrid Approach
- Keep monitoring hook for detailed logging
- Enable model-level enforcement for blocking
- Best of both worlds: enforcement + detailed monitoring

## Best Practices

### 1. Start with Shadow Mode
- Deploy with monitoring only
- Collect violation data for 1-2 weeks
- Analyze patterns before enforcement

### 2. Tune Thresholds
- Adjust content policy confidence levels
- Modify contextual grounding thresholds
- Balance security vs. usability

### 3. Healthcare-Specific Considerations
- Allow PII in INPUT for patient lookup
- Anonymize PII in OUTPUT for privacy
- Monitor medical record number patterns

### 4. Regular Review
- Weekly review of violation logs
- Monthly guardrail policy updates
- Quarterly compliance audits

## Troubleshooting

### No Violations Logged
- Verify guardrail ID and version are correct
- Check AWS region matches guardrail region
- Ensure Bedrock permissions are configured

### Too Many False Positives
- Adjust content policy strength (MEDIUM → LOW)
- Increase contextual grounding thresholds
- Refine topic policy examples

### Missing PII Detections
- Add custom regex patterns for specific formats
- Test with real data samples
- Verify PII entity types are enabled

## References

- [Strands Agents Hooks Documentation](https://docs.strands.ai/hooks)
- [Amazon Bedrock Guardrails](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html)
- [ApplyGuardrail API Reference](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_ApplyGuardrail.html)
