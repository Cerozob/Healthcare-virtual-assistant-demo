# Guardrail Detection Fix

## Problem

Guardrail detections were not showing all violations in the frontend table. For example:

**Redactions in message:**
```
Cédula: {CedulaColombia}
Email: {EMAIL}
Teléfono: {PHONE}{TelefonoLatam}
Ubicación País: {ADDRESS}
Provincia: {ADDRESS}
Ciudad: {ADDRESS}
Dirección: {ADDRESS}
Código Postal: {ADDRESS}
```

**But table only showed 2 entries:**
- EMAIL (ANONYMIZED)
- AGE (NONE)

**Expected:** Should show all detected PII types (CedulaColombia, EMAIL, PHONE, TelefonoLatam, multiple ADDRESS entries)

## Root Cause

In `agents/shared/guardrail_monitoring_hook.py`, the `_log_intervention` method had a bug where violations from different policy types were being collected but not properly added to the intervention data.

### Before (Buggy Code):

```python
for assessment in assessments:
    # Topic Policy violations
    if "topicPolicy" in assessment:
        violations = self._log_topic_violations(assessment["topicPolicy"], source)
        # ❌ BUG: violations variable gets overwritten by next policy type
    
    # Content Policy violations
    if "contentPolicy" in assessment:
        violations = self._log_content_violations(assessment["contentPolicy"], source)
        # ❌ BUG: violations variable gets overwritten again
    
    # Sensitive Information violations
    if "sensitiveInformationPolicy" in assessment:
        violations = self._log_pii_violations(assessment["sensitiveInformationPolicy"], source)
        # ❌ BUG: violations variable gets overwritten again
    
    # Contextual Grounding violations
    if "contextualGroundingPolicy" in assessment:
        violations = self._log_grounding_violations(assessment["contextualGroundingPolicy"], source)
    
    # ❌ BUG: Only the LAST violations are added (from grounding policy)
    if violations:
        intervention_data["violations"].extend(violations)
```

The problem was that the `violations` variable was being reused for each policy type, so only the last policy type's violations were being added to the intervention data.

## Solution

Fixed the code to immediately extend the violations list after each policy type is processed:

### After (Fixed Code):

```python
for assessment in assessments:
    # Topic Policy violations
    if "topicPolicy" in assessment:
        violations = self._log_topic_violations(assessment["topicPolicy"], source)
        if violations:
            intervention_data["violations"].extend(violations)  # ✅ Add immediately
    
    # Content Policy violations
    if "contentPolicy" in assessment:
        violations = self._log_content_violations(assessment["contentPolicy"], source)
        if violations:
            intervention_data["violations"].extend(violations)  # ✅ Add immediately
    
    # Sensitive Information violations
    if "sensitiveInformationPolicy" in assessment:
        violations = self._log_pii_violations(assessment["sensitiveInformationPolicy"], source)
        if violations:
            intervention_data["violations"].extend(violations)  # ✅ Add immediately
    
    # Contextual Grounding violations
    if "contextualGroundingPolicy" in assessment:
        violations = self._log_grounding_violations(assessment["contextualGroundingPolicy"], source)
        if violations:
            intervention_data["violations"].extend(violations)  # ✅ Add immediately
```

## Impact

Now all guardrail violations will be properly captured and displayed in the frontend table:

- **PII Entity detections** (EMAIL, AGE, etc.)
- **PII Regex detections** (CedulaColombia, TelefonoLatam, HistoriaClinica, etc.)
- **Topic Policy violations** (blocked topics)
- **Content Policy violations** (HATE, INSULTS, VIOLENCE, SEXUAL)
- **Grounding Policy violations** (GROUNDING, RELEVANCE)

Each violation will appear as a separate row in the table with:
- Source (Usuario/Agente)
- Intervention action (Bloqueada/Detectada)
- Type (with icon)
- Detail (specific PII type, topic name, etc.)
- Action (ANONYMIZED, BLOCK, NONE)
- Metrics (confidence, score, threshold)

## Testing

To verify the fix:

1. Deploy the updated agent code
2. Send a message with patient information (name, email, phone, address, etc.)
3. Check the GuardRails tab in the debug panel
4. Verify the table shows ALL detected PII types, not just 1-2
5. Verify the redactions in the message match the violations in the table

### Example Expected Output:

For a message with patient info, you should see violations like:
- EMAIL → ANONYMIZED
- PHONE → ANONYMIZED  
- CedulaColombia → ANONYMIZED
- TelefonoLatam → ANONYMIZED
- ADDRESS (País) → ANONYMIZED
- ADDRESS (Provincia) → ANONYMIZED
- ADDRESS (Ciudad) → ANONYMIZED
- ADDRESS (Dirección) → ANONYMIZED
- ADDRESS (Código Postal) → ANONYMIZED
- AGE → NONE (detected but not anonymized)

Each as a separate row in the table.
