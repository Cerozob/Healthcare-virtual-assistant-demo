# Guardrails Simplification

## Changes Made

### Removed Complex Guardrails Helper
- Deleted `agents/shared/guardrails.py` - complex wrapper around Bedrock Guardrails
- Removed custom compliance manager and PII detection logic
- Eliminated unnecessary abstraction layers

### Updated Agent Configuration
All agents now use Bedrock Guardrails directly through Strands Agent configuration:

```python
Agent(
    system_prompt=system_prompt,
    tools=[...],
    model=BedrockModel(...),
    guardrail_id=config.guardrail_id,
    guardrail_version=config.guardrail_version
)
```

### Simplified Processing
- Removed manual guardrails processing in orchestrator
- Bedrock Guardrails now applied automatically by Strands framework
- No more custom input/output filtering logic

### Configuration
Guardrails are configured via environment variables:
- `GUARDRAIL_ID` - Bedrock Guardrail identifier
- `GUARDRAIL_VERSION` - Version (defaults to "DRAFT")

## Benefits

1. **Reduced Complexity** - Eliminated ~300 lines of custom guardrails code
2. **Better Performance** - No double processing of content
3. **Managed Service** - Relies on AWS managed Bedrock Guardrails
4. **Simplified Maintenance** - Less custom code to maintain
5. **Framework Integration** - Uses Strands built-in guardrails support

## Migration Notes

- All PII/PHI protection is now handled by Bedrock Guardrails
- No changes needed to existing prompts or tools
- Health check endpoints updated to reflect managed guardrails
- Configuration validation simplified
