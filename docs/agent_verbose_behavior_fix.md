# Agent Verbose Behavior Fix

## Issue
When looking up a patient by cédula, the agent announces what it's going to do instead of just doing it:

**Current behavior:**
```
Usuario: "Busca al paciente con cédula 12345678"
Agente: "Entendido. Permíteme buscar la información de este paciente en el sistema para poder asistirte mejor."
```

**Expected behavior:**
```
Usuario: "Busca al paciente con cédula 12345678"
Agente: "He encontrado al paciente Juan Pérez (cédula 12345678). Aquí está su información: [detalles del paciente]"
```

## Root Cause
The agent prompts were instructing the agents to be helpful and explain their actions, but they were being TOO helpful. The LLM was interpreting this as "announce what you're going to do before doing it", which creates a poor user experience with unnecessary latency.

## Solution

### Changes to `agents/prompts/healthcare.md`

Added explicit instruction to NOT announce actions:

```markdown
## REGLA CRÍTICA: NO ANUNCIAR ACCIONES
- **NUNCA** digas "voy a buscar", "permíteme buscar", "déjame consultar", etc.
- **EJECUTA** las herramientas y agentes INMEDIATAMENTE sin anunciar
- **RESPONDE** directamente con los resultados obtenidos
- **EJEMPLO INCORRECTO**: "Permíteme buscar la información de este paciente en el sistema"
- **EJEMPLO CORRECTO**: "He encontrado al paciente Juan Pérez (cédula 12345678). Aquí está su información..."
```

### Changes to `agents/prompts/information_retrieval.md`

Added similar instruction:

```markdown
## REGLA CRÍTICA: EJECUTAR, NO ANUNCIAR
- **NO** digas "voy a buscar", "permíteme buscar", "déjame consultar"
- **EJECUTA** las herramientas INMEDIATAMENTE y responde con los resultados
- **EJEMPLO INCORRECTO**: "Voy a buscar al paciente en el sistema"
- **EJEMPLO CORRECTO**: "Encontré al paciente Juan Pérez (ID: 12345). Aquí está su información..."
```

## Why This Works

LLMs are very sensitive to explicit instructions. By adding a "REGLA CRÍTICA" (CRITICAL RULE) section with clear examples of what NOT to do and what TO do, the agent will:

1. **Understand the expectation** - The rule is explicit and unambiguous
2. **See concrete examples** - The INCORRECTO/CORRECTO examples show exactly what behavior to avoid/follow
3. **Prioritize execution** - The instruction to execute IMMEDIATELY reinforces the desired behavior

## Testing

After deploying the updated prompts, test with:

1. **Patient lookup by cédula**:
   ```
   "Busca al paciente con cédula 12345678"
   ```
   Expected: Direct response with patient info, no announcement

2. **Patient lookup by name**:
   ```
   "¿Quién es Juan Pérez?"
   ```
   Expected: Direct response with patient info, no "voy a buscar"

3. **File listing**:
   ```
   "¿Qué archivos tiene el paciente María García?"
   ```
   Expected: Direct list of files, no "permíteme consultar"

## Deployment

The prompt files are loaded at agent initialization, so you need to restart the agent service:

### Option 1: Redeploy Agent (Recommended)
```bash
cd infrastructure
cdk deploy AWSomeBuilder2-AssistantStack --require-approval never
```

### Option 2: Restart Agent Container (if using containers)
```bash
# Restart the agent service
docker restart healthcare-agent
```

### Option 3: Wait for Next Invocation (if using Lambda)
The next cold start will load the new prompts automatically.

## Verification

Check CloudWatch logs for the agent to verify:

1. **Tool calls happen immediately** - No "voy a buscar" messages before tool calls
2. **Responses include results** - Agent returns actual data, not promises to search
3. **Reduced latency** - Fewer round trips mean faster responses

## Related Issues

This fix also improves:
- **User experience** - More direct, professional responses
- **Latency** - Fewer unnecessary LLM calls
- **Token usage** - Less verbose responses = fewer tokens

## Rollback

If this causes issues, revert the prompt changes:

```bash
git checkout HEAD~1 agents/prompts/healthcare.md agents/prompts/information_retrieval.md
cdk deploy AWSomeBuilder2-AssistantStack --require-approval never
```

## Additional Notes

- This is a common issue with conversational AI - being "too helpful"
- The fix uses explicit negative examples (what NOT to do) which are very effective with LLMs
- Consider adding similar rules to other agent prompts if they exhibit verbose behavior
