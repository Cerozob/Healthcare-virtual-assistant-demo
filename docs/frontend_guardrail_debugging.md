# Frontend Guardrail Debugging Implementation

## Overview

The frontend now includes a fully functional **GuardRails debugging tab** in the Debug Panel that displays guardrail interventions detected during agent processing.

## Implementation

### Components Modified

#### 1. DebugPanel Component (`apps/frontend/src/components/debug/DebugPanel.tsx`)

**Added Types:**
```typescript
interface GuardrailViolation {
  type: 'topic_policy' | 'content_policy' | 'pii_entity' | 'pii_regex' | 'grounding_policy';
  topic?: string;
  content_type?: string;
  pii_type?: string;
  pattern?: string;
  grounding_type?: string;
  confidence?: string;
  score?: number;
  threshold?: number;
  action?: string;
  policy_type?: string;
}

interface GuardrailIntervention {
  source: 'INPUT' | 'OUTPUT';
  action: 'GUARDRAIL_INTERVENED' | 'NONE';
  content_preview?: string;
  timestamp?: string;
  violations: GuardrailViolation[];
}
```

**New Prop:**
- `guardrailInterventions?: GuardrailIntervention[]` - Array of guardrail interventions from the agent response

**Features:**
- ✅ Success alert when no violations detected
- ⚠️ Warning alert showing count of interventions
- 📊 Expandable sections for each intervention
- 🎨 Color-coded violation types with icons
- 📝 Detailed violation information display
- 🔍 Raw JSON view of all interventions
- 📚 Policy documentation reference

#### 2. ChatPage Component (`apps/frontend/src/pages/ChatPage.tsx`)

**Updated State:**
```typescript
const [debugInfo, setDebugInfo] = useState<{
  lastResponse: unknown;
  lastRequest: unknown;
  patientContext: unknown;
  guardrailInterventions: GuardrailIntervention[];
}>({
  lastResponse: null,
  lastRequest: null,
  patientContext: null,
  guardrailInterventions: []
});
```

**Response Handling:**
```typescript
setDebugInfo({
  lastResponse: response,
  lastRequest: requestData,
  patientContext: response.patientContext,
  guardrailInterventions: response.guardrailInterventions || []
});
```

## UI Features

### Intervention Display

Each intervention shows:
- **Source**: INPUT (user) or OUTPUT (agent) with color-coded status indicator
- **Action**: GUARDRAIL_INTERVENED or NONE
- **Content Preview**: First 100 characters of flagged content
- **Timestamp**: When the evaluation occurred
- **Violations**: Detailed list of all violations detected

### Violation Types

**🚫 Topic Policy Violations:**
- Shows topic name (e.g., "TradingCriptomonedas")
- Displays policy type (DENY/ALLOW)
- Shows action (BLOCK)

**⚠️ Content Policy Violations:**
- Shows content type (HATE, INSULTS, VIOLENCE, SEXUAL)
- Displays confidence level (LOW, MEDIUM, HIGH)
- Shows action (BLOCK)

**🔒 PII Entity Detection:**
- Shows PII type (EMAIL, PHONE, ADDRESS, etc.)
- Displays action (ANONYMIZE)

**🏥 Healthcare PII Detection:**
- Shows pattern name (CedulaColombia, HistoriaClinica, etc.)
- Displays action (ANONYMIZE)

**📊 Grounding Policy Violations:**
- Shows grounding type (GROUNDING, RELEVANCE)
- Displays score and threshold
- Shows action (BLOCK)

### Policy Reference

The tab includes a built-in reference section documenting all active guardrail policies:
- Topic policies (cryptocurrency, extreme sports)
- Content policies (hate, insults, violence, sexual)
- PII detection (standard entities and healthcare-specific patterns)
- Contextual grounding policies

## Usage

### Accessing the Debug Panel

1. Navigate to the Chat page
2. Click "Mostrar Panel de Depuración" button
3. Select the "GuardRails" tab

### Viewing Interventions

When guardrail interventions are detected:
1. A warning alert shows the count of interventions
2. Each intervention is displayed in an expandable section
3. Click to expand and see detailed violation information
4. View the raw JSON for complete data

### No Violations

When no violations are detected:
- A success alert confirms clean processing
- Policy reference is still available for documentation

## Example Response Data

```json
{
  "response": "Lo siento, no puedo proporcionar consejos sobre inversiones...",
  "sessionId": "session-123",
  "guardrailInterventions": [
    {
      "source": "INPUT",
      "action": "GUARDRAIL_INTERVENED",
      "content_preview": "¿Cuál es la mejor criptomoneda para invertir ahora?",
      "timestamp": "2024-11-10T15:30:45.123Z",
      "violations": [
        {
          "type": "topic_policy",
          "topic": "TradingCriptomonedas",
          "action": "BLOCK",
          "policy_type": "DENY"
        }
      ]
    }
  ]
}
```

## Benefits

### For Developers
- 🔍 Real-time visibility into guardrail detections
- 🐛 Easy debugging of policy configurations
- 📊 Detailed violation analysis
- 🎯 Quick identification of false positives

### For Compliance
- 📝 Audit trail of all detections
- 🔒 PII exposure tracking
- ⚠️ Policy violation monitoring
- 📈 Pattern analysis for tuning

### For Testing
- ✅ Verify guardrail policies are working
- 🧪 Test different content types
- 🎨 Visual feedback on detections
- 📋 Complete data for analysis

## Shadow Mode

The guardrails are currently in **shadow mode**:
- ✅ Violations are detected and logged
- ✅ Detailed information is captured
- ❌ Content is NOT blocked
- ✅ Users experience normal functionality

This allows safe monitoring and tuning before enabling enforcement.

## Future Enhancements

Potential improvements:
- 📊 Aggregated statistics across sessions
- 📈 Trend analysis over time
- 🔔 Real-time alerts for specific violations
- 📥 Export functionality for compliance reports
- 🎨 Customizable violation severity levels
- 🔍 Search and filter capabilities

## Related Documentation

- [Guardrail Monitoring Guide](./guardrail_monitoring.md)
- [Guardrail Monitoring Quick Start](./guardrail_monitoring_quick_start.md)
- [Backend Implementation Summary](./GUARDRAIL_MONITORING_SUMMARY.md)
