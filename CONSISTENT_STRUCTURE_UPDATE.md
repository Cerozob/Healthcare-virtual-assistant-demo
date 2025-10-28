# Session Management - Consistent Structure Update

## Overview

Updated the session management implementation to be consistent with the existing document processing structure used in the extraction lambda. This ensures all patient data follows the same organizational pattern in S3.

## Structure Change

### Previous Structure (Inconsistent)
```
medical-notes/
├── patients/
│   ├── patient_123/
│   │   └── session_xyz/
│   └── patient_456/
│       └── session_abc/
└── no-patient/
    └── session_def/
```

### New Structure (Consistent with Document Processing)
```
processed/
├── patient_123_medical_notes/
│   └── session_xyz/
├── patient_123_document_name/     # Document processing
│   ├── extracted_data.json
│   └── result.html
├── patient_456_medical_notes/
│   └── session_abc/
└── unknown_medical_notes/         # Sessions without patient context
    └── session_def/
```

## Pattern Used

The extraction lambda uses this pattern:
```python
processed_key_prefix = f"processed/{clean_patient_id}_{clean_filename}"
```

Session management now uses the same pattern:
```python
# For patient sessions
prefix = f"processed/{patient_id}_medical_notes/"

# For sessions without patient context
prefix = f"processed/unknown_medical_notes/"
```

## Benefits of Consistent Structure

### 1. **Unified Patient Data Organization**
- All patient data (documents + conversations) in one logical structure
- Easy to find all data related to a specific patient
- Consistent backup and archival policies

### 2. **Simplified Access Patterns**
- Single S3 prefix pattern for all patient data
- Easier IAM policies and access control
- Consistent monitoring and alerting

### 3. **Better Data Management**
- Lifecycle policies can be applied uniformly
- Easier data migration and cleanup
- Consistent metadata and tagging

### 4. **Developer Experience**
- Single pattern to remember and implement
- Consistent across all services
- Easier debugging and troubleshooting

## Files Updated

### Core Implementation
- `agents/main.py` - Updated session manager creation
- `agents/shared/utils.py` - Updated metadata creation
- `infrastructure/stacks/assistant_stack.py` - Updated environment variables

### Examples and Tests
- `agents/session_management_example.py` - Updated all examples
- `agents/test_session_management.py` - Updated test cases
- `agents/integration_test.py` - Updated integration tests
- `agents/demo_session_management.py` - Updated demo script

### Documentation
- `agents/SESSION_MANAGEMENT.md` - Updated structure documentation
- `SESSION_MANAGEMENT_IMPLEMENTATION.md` - Updated implementation guide
- `agents/docker-compose.yml` - Updated environment variables

## Configuration Changes

### Environment Variables
```bash
# Before
SESSION_PREFIX=medical-notes/

# After
SESSION_PREFIX=processed/  # Base prefix, actual: processed/{patient_id}_{data_type}/
```

### S3 Structure Examples
```bash
# Patient session notes
s3://bucket/processed/Juan_Perez_123_medical_notes/session_20241028_143022/

# Patient documents (existing)
s3://bucket/processed/Juan_Perez_123_lab_report/extracted_data.json

# Unknown patient sessions
s3://bucket/processed/unknown_medical_notes/session_20241028_145012/
```

## API Response Changes

### Before
```json
{
  "patient_context": {
    "session_prefix": "medical-notes/patients/Juan_Perez_123/"
  }
}
```

### After
```json
{
  "patient_context": {
    "session_prefix": "processed/Juan_Perez_123_medical_notes/",
    "consistent_with_documents": true
  },
  "session_info": {
    "structure_pattern": "processed/{patient_id}_{data_type}/"
  }
}
```

## Migration Notes

### For Existing Deployments
1. **No Breaking Changes**: New sessions will use the new structure
2. **Existing Sessions**: Will continue to work with old structure
3. **Migration Script**: Can be created to move old sessions if needed

### For New Deployments
- All sessions will automatically use the consistent structure
- No additional configuration required
- Works seamlessly with existing document processing

## Testing

All tests have been updated to use the new consistent structure:

```bash
# Run updated tests
cd agents
python test_session_management.py
python integration_test.py

# Run interactive demo
python demo_session_management.py
```

## Verification

To verify the consistent structure is working:

1. **Check S3 Structure**:
   ```bash
   aws s3 ls s3://ab2-cerozob-processeddata-us-east-1/processed/ --recursive
   ```

2. **Look for Pattern**:
   - Patient documents: `processed/{patient_id}_{document_name}/`
   - Patient sessions: `processed/{patient_id}_medical_notes/`
   - Unknown sessions: `processed/unknown_medical_notes/`

3. **API Response**:
   - Check `patient_context.consistent_with_documents: true`
   - Verify `session_info.structure_pattern` matches document pattern

## Conclusion

The session management now follows the exact same organizational pattern as document processing, ensuring:

- **Consistency**: All patient data follows the same structure
- **Maintainability**: Single pattern to understand and maintain
- **Scalability**: Unified approach scales better
- **Compliance**: Easier to implement data governance policies

This change makes the healthcare assistant's data organization truly unified and consistent across all data types.
