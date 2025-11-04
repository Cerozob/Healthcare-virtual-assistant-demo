# Patient Context Synchronization

## Overview

The patient context synchronization system automatically detects and manages patient information from agent responses, ensuring secure and accurate patient identification throughout the healthcare chat interface.

## Architecture

### Enhanced PatientContext

The `PatientContext` has been enhanced with:

- **`syncPatientFromResponse()`**: Intelligent patient context synchronization
- **`lastSyncedPatientId`**: Tracking of last synchronized patient
- **Security checks**: Automatic detection of patient changes
- **Automatic patient fetching**: Retrieves complete patient data from API

### Patient Sync Hook (`usePatientSync`)

A specialized hook that provides:

- **Intelligent sync handling**: Processes patient context from agent responses
- **Security management**: Handles patient changes with session isolation
- **User notifications**: Provides feedback through the notification system
- **Error handling**: Graceful handling of sync failures

### Backend Enhancement

The backend agent has been enhanced to:

- **Extract patient context**: Analyzes agent responses for patient information
- **Multiple identification sources**: Supports various patient identification methods
- **Structured output**: Provides consistent patient context format

## Patient Identification Sources

### 1. Conversation Analysis
- Extracts patient information from natural language
- Patterns: "Paciente: [Name] (ID: [ID])"
- Use case: Direct patient mentions in conversation

### 2. File Analysis
- Identifies patients from uploaded medical documents
- Analyzes file metadata and S3 key structure
- Use case: Medical records, lab results, images

### 3. Document Metadata
- Extracts patient info from document properties
- Processes structured data within files
- Use case: PDF metadata, DICOM headers

### 4. Cedula Extraction
- Identifies patients by national ID (cedula)
- Patterns: "Cédula: [number]", "Documento: [number]"
- Use case: Identity document processing

### 5. Name Matching
- Matches patient names against database
- Fuzzy matching for name variations
- Use case: Partial name mentions

## Security Features

### Patient Change Detection
- Automatically detects when a different patient is mentioned
- Triggers security protocols to protect patient privacy
- Starts new session to isolate patient data

### Session Isolation
- Each patient gets a separate chat session
- Previous chat history is cleared when patient changes
- Prevents data leakage between patients

### Privacy Protection
- Clear warnings when patient context changes
- User notifications about security measures
- Audit trail of patient context changes

## Usage Examples

### Basic Patient Sync

```typescript
import { usePatientSync } from '../hooks/usePatientSync';

const { handlePatientContextSync } = usePatientSync({
  onPatientDetected: (patient) => {
    console.log('Patient detected:', patient);
  },
  onPatientChanged: (oldPatient, newPatient) => {
    console.log('Patient changed for security');
  }
});

// In chat response handler
if (response.patientContext) {
  await handlePatientContextSync(
    response.patientContext,
    (message) => addChatMessage(message),
    () => clearChatHistory()
  );
}
```

### Manual Patient Context Processing

```typescript
import { usePatientContext } from '../contexts/PatientContext';

const { syncPatientFromResponse } = usePatientContext();

const result = await syncPatientFromResponse({
  patientId: '[PATIENT_ID]',
  patientName: '[PATIENT_NAME]',
  contextChanged: true,
  identificationSource: 'conversation'
});

if (result.patientUpdated) {
  console.log('Patient updated:', result.patient);
}
```

## Patient Context Response Format

```typescript
interface PatientContext {
  patientId: string;           // Unique patient identifier
  patientName: string;         // Patient full name
  contextChanged: boolean;     // Whether context changed
  identificationSource: string; // How patient was identified
}
```

### Identification Sources

- `conversation`: Extracted from natural language
- `file_analysis`: Identified from uploaded files
- `document_metadata`: Found in document properties
- `cedula_extraction`: Extracted from national ID
- `name_matching`: Matched by name patterns

## User Experience

### Automatic Detection
1. User uploads medical document or mentions patient
2. Agent analyzes content and identifies patient
3. System automatically updates patient context
4. User receives notification about patient detection

### Security Scenarios
1. Different patient detected in conversation
2. System immediately starts new session
3. Previous chat history is cleared
4. User receives security warning
5. New patient context is established

### Error Handling
1. Patient identification fails
2. System shows error notification
3. User can manually select patient
4. Fallback patient object created if needed

## Notifications

### Success Notifications
- "Paciente detectado: [Name] identificado automáticamente"
- Auto-hide after 4 seconds
- Green success indicator

### Security Warnings
- "Cambio de paciente detectado - Nueva sesión iniciada"
- Requires user acknowledgment
- Yellow warning indicator

### Error Notifications
- "Error de sincronización - Seleccione paciente manualmente"
- Provides action button for manual selection
- Red error indicator

## Testing

### Real Database Testing

The system uses actual patient data from the database for all testing:

- **Patient Selection**: Uses real patients from the database via patient selector
- **Patient Detection**: Tests with actual patient IDs and names from database
- **Context Sync**: Verifies sync functionality with real patient records
- **File Processing**: Tests file uploads with existing patient data

### Testing Scenarios

1. **Patient Selection**: Choose real patients from database via patient selector
2. **Conversation Detection**: Mention actual patient names/IDs in conversation
3. **File-based Detection**: Upload files with real patient metadata
4. **Security Testing**: Switch between different real patients
5. **Context Preservation**: Verify real patient context is maintained

## Best Practices

### Implementation
- Always use the `usePatientSync` hook for patient context handling
- Provide user feedback through notifications
- Handle errors gracefully with fallback options
- Test all identification scenarios thoroughly

### Security
- Never mix patient data between sessions
- Always clear chat history when patient changes
- Provide clear warnings about security measures
- Maintain audit trail of patient context changes

### User Experience
- Provide immediate feedback on patient detection
- Use clear, non-technical language in notifications
- Offer manual patient selection as fallback
- Show patient information prominently in UI

## Troubleshooting

### Common Issues

1. **Patient not detected**: Check agent response format
2. **Wrong patient identified**: Verify identification patterns
3. **Sync errors**: Check network connectivity and API availability
4. **Session issues**: Verify session ID consistency

### Debug Tools

- **Patient Sync Test**: Test component for verification
- **Debug Panel**: Shows patient context data
- **Console Logs**: Detailed sync operation logs
- **Network Tab**: API request/response inspection

## Future Enhancements

- **Machine Learning**: Improve patient identification accuracy
- **Fuzzy Matching**: Better name matching algorithms
- **Multi-language Support**: Support for different languages
- **Audit Logging**: Comprehensive patient access logging
- **Batch Processing**: Handle multiple patients in single conversation
