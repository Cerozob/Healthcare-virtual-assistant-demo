# AI-Driven Patient Identification System

## Overview

The Healthcare Agent uses advanced AI agents to identify patients from natural language conversations without any manual parsing or regex. The system supports three primary identification methods and showcases sophisticated AI agent functionality.

## Identification Methods

### 1. Internal UUID (Highest Priority)
- **Format**: System-generated unique identifiers
- **Example**: `1d621da0-f89e-4691-8f56-5022bb20dcca`
- **Use Cases**: Direct system references, API calls, internal workflows
- **Confidence**: Always high when detected

### 2. Cédula/National ID (High Priority)
- **Format**: National identification numbers (various formats)
- **Examples**: `12345678`, `1.234.567-8`, `V-12345678`
- **Use Cases**: Official patient identification, registration
- **Confidence**: High to medium based on context

### 3. Full Name (Medium Priority)
- **Format**: Complete patient names (first + last name)
- **Examples**: `Juan Pérez Gómez`, `María Elena Rodríguez`
- **Use Cases**: Conversational references, appointment scheduling
- **Confidence**: Medium to low based on context clarity

## AI Agent Architecture

### Patient Identification Agent
Specialized AI agent that analyzes conversation text to extract patient identifiers:

```python
# Analyzes natural language for patient references
patient_identification = patient_identification_agent.structured_output(
    output_model=PatientIdentification,
    prompt=identification_prompt
)
```

**Capabilities:**
- Contextual understanding of patient references
- Confidence assessment based on clarity and explicitness
- Multi-identifier extraction from single conversations
- Distinction between speaker and patient being discussed

### Patient Lookup Agent
Specialized AI agent for database queries and patient matching:

```python
# Performs intelligent database lookups
lookup_result = patient_lookup_agent.structured_output(
    output_model=PatientLookupResult,
    prompt=lookup_prompt
)
```

**Capabilities:**
- Multi-strategy database searching
- Fuzzy name matching for variations
- Confidence scoring for matches
- Multiple match detection and handling

## Identification Process

### Step 1: AI Conversation Analysis
```
Input: "Necesito revisar los resultados del paciente Juan Pérez, cédula 12345678"

AI Analysis:
- Detects patient reference: "paciente Juan Pérez"
- Extracts cédula: "12345678"
- Extracts full name: "Juan Pérez"
- Assesses confidence: "high" (explicit identifiers)
- Determines primary identifier: "cedula"
```

### Step 2: Structured Extraction
```python
PatientIdentification(
    internal_id=None,
    cedula="12345678",
    full_name="Juan Pérez",
    has_patient_info=True,
    identification_confidence="high",
    primary_identifier_type="cedula",
    context_clues="Explicit patient reference with cédula number"
)
```

### Step 3: File Organization ID Generation
```python
# AI determines best ID for file organization
file_organization_id = "12345678"  # Cleaned cédula (highest priority available)
```

## Confidence Levels

### High Confidence
- Explicit patient references with clear identifiers
- Direct UUID mentions
- Complete cédula with patient name
- Unambiguous context

**Examples:**
- `"Patient Juan Pérez Gómez, cédula 12345678"`
- `"Review file for patient ID 1d621da0-f89e-4691-8f56-5022bb20dcca"`
- `"María Elena Rodríguez needs an appointment"`

### Medium Confidence
- Partial identifiers with context
- Informal patient references
- Names without additional identifiers

**Examples:**
- `"Juan's test results are ready"`
- `"The patient with cédula ending in 5678"`
- `"Check María's previous visits"`

### Low Confidence
- Ambiguous references
- Potential speaker confusion
- Incomplete information

**Examples:**
- `"My test results"` (could be the speaker)
- `"The patient"` (no specific identifier)
- `"Someone named Juan called"`

## Integration with Multimodal Uploads

### File Organization Strategy
1. **UUID-based**: `s3://bucket/1d621da0-f89e-4691-8f56-5022bb20dcca/`
2. **Cédula-based**: `s3://bucket/12345678/`
3. **Name-based**: `s3://bucket/juan_perez/`
4. **Fallback**: `s3://bucket/unknown_patient/`

### AI-Driven Path Selection
```python
def _determine_file_organization_id(patient_identification):
    # AI logic for optimal file organization
    if patient_identification.internal_id:
        return patient_identification.internal_id  # Most reliable
    elif patient_identification.cedula:
        return clean_cedula(patient_identification.cedula)  # Unique and stable
    elif patient_identification.full_name:
        return name_to_file_safe(patient_identification.full_name)  # Readable
    else:
        return "unknown_patient"  # Safe fallback
```

## Response Format

### Patient Context with AI Data
```json
{
  "patientId": "12345678",
  "patientName": "Juan Pérez",
  "contextChanged": true,
  "identificationSource": "ai_cedula",
  "identificationConfidence": "high",
  "fileOrganizationId": "12345678",
  "aiIdentificationData": {
    "internal_id": null,
    "cedula": "12345678",
    "full_name": "Juan Pérez",
    "identification_confidence": "high",
    "primary_identifier_type": "cedula",
    "context_clues": "Explicit patient reference with cédula number"
  }
}
```

## Testing Examples

### Test 1: UUID Identification
```
Input: "Please review the medical history for patient ID 1d621da0-f89e-4691-8f56-5022bb20dcca"

Expected AI Output:
- primary_identifier_type: "uuid"
- identification_confidence: "high"
- file_organization_id: "1d621da0-f89e-4691-8f56-5022bb20dcca"
```

### Test 2: Cédula Identification
```
Input: "El paciente con cédula 12.345.678 necesita una cita"

Expected AI Output:
- primary_identifier_type: "cedula"
- identification_confidence: "high"
- file_organization_id: "12345678"
```

### Test 3: Name Identification
```
Input: "María Elena Rodríguez llamó para preguntar por sus resultados"

Expected AI Output:
- primary_identifier_type: "full_name"
- identification_confidence: "medium"
- file_organization_id: "maria_elena_rodriguez"
```

### Test 4: Multiple Identifiers
```
Input: "Juan Pérez (cédula 12345678, ID interno abc-123) tiene una cita mañana"

Expected AI Output:
- Extracts all identifiers: cedula, full_name, potential internal_id
- primary_identifier_type: "cedula" (highest confidence available)
- file_organization_id: "12345678"
```

## Example Workflow

### Complete Patient Identification and File Upload
```
User: "Aquí está la radiografía del paciente Juan Pérez, cédula 12345678"
[Includes image attachment]

AI Processing:
1. Identifies patient: Juan Pérez (cédula: 12345678) with high confidence
2. Uploads image to: s3://bucket/12345678/20241103_143022_a1b2c3d4_xray.jpg
3. Stores in AgentCore Memory for future reference
4. Responds with medical analysis of the radiograph

File Organization Result:
- Patient folder: s3://bucket/12345678/
- All files for this patient stored in flat structure
- No file type prefixes for better workflow processing
```

## Benefits of AI-Driven Approach

1. **No Manual Parsing**: Pure AI understanding of natural language
2. **Context Awareness**: Understands conversational nuances
3. **Multi-Language Support**: Works with Spanish and English naturally
4. **Confidence Assessment**: Provides reliability metrics
5. **Flexible Matching**: Handles variations in format and expression
6. **Extensible**: Easy to add new identification methods
7. **Audit Trail**: Complete AI reasoning and confidence data
8. **Flat File Structure**: Optimized for workflow processing without type prefixes

## Error Handling

### Graceful Degradation
- If AI identification fails, falls back to "unknown_patient"
- Partial identifications still provide useful organization
- System continues functioning without patient context

### Logging and Debugging
```
INFO: 🎯 AI identified patient: Juan Pérez (12345678) via cedula
INFO: 🤖 AI Identification: cedula with high confidence
INFO: 📁 Using AI file organization ID: 12345678
```

This AI-driven system showcases advanced agent capabilities while providing robust, reliable patient identification for healthcare workflows.
