# File Upload Without Patient Selection Feature

## Overview

This feature allows users to attach files to the chat interface even when no patient is currently selected. The AI agent will analyze the file content to identify the patient and ask for confirmation or additional information as needed.

## How It Works

### User Experience

1. **File Attachment**: Users can now drag and drop or select files without first selecting a patient
2. **Agent Analysis**: The AI agent analyzes the file content to identify patient information
3. **Patient Identification**: The agent searches for matching patients in the database
4. **Confirmation**: The agent asks for confirmation or requests additional information
5. **File Assignment**: Once the patient is confirmed, the file is properly assigned and processed

### Technical Implementation

#### Frontend Changes (ChatPage.tsx)

- **Removed Patient Validation**: File uploads no longer require a patient to be selected first
- **Updated File Paths**: Files without patient context are uploaded to `unassigned/{timestamp}/{filename}`
- **Enhanced Metadata**: Files include `requires-patient-identification` metadata flag
- **UI Updates**: Updated placeholder text and dropzone messages to reflect new capability

#### Backend/Agent Changes

- **Enhanced Prompts**: Updated healthcare agent prompts to handle files without patient context
- **Patient Extraction**: Agent analyzes file content to extract patient information (names, IDs, etc.)
- **Database Search**: Agent searches patient database for matches
- **Confirmation Flow**: Agent asks users to confirm patient identity or provide additional information

## File Processing Flow

### With Patient Selected (Existing Flow)
```
User selects patient → Attaches file → File uploaded to patient folder → Agent processes
```

### Without Patient Selected (New Flow)
```
User attaches file → File uploaded to unassigned folder → Agent analyzes content → 
Agent identifies patient → Agent asks for confirmation → File moved to patient folder → Agent processes
```

## File Storage Structure

### With Patient Context
```
s3://bucket/{patient_id}/{filename}
```

### Without Patient Context (Temporary)
```
s3://bucket/unassigned/{timestamp}/{filename}
```

## Agent Behavior Examples

### Successful Patient Identification
```
User: [Attaches lab results file]
Agent: "He analizado el archivo y he identificado que pertenece a María García Rodríguez (Cédula: 12345678). ¿Es correcto? Una vez confirmado, procederé a analizar los resultados de laboratorio."
```

### Multiple Patient Matches
```
User: [Attaches file with common name]
Agent: "He encontrado varios pacientes con el nombre 'Juan Pérez'. ¿Puedes proporcionar la cédula o fecha de nacimiento para identificar al paciente correcto?"
```

### No Patient Information Found
```
User: [Attaches file without patient info]
Agent: "He recibido un archivo médico pero no puedo identificar al paciente. ¿Puedes decirme el nombre completo o cédula del paciente al que pertenece este archivo?"
```

## Security Considerations

### Patient Privacy
- Files are temporarily stored in `unassigned/` folder with restricted access
- Patient identification is required before any medical analysis
- Session isolation prevents cross-patient data leakage

### Data Protection
- All file uploads include metadata for tracking and auditing
- Files are moved to proper patient folders only after confirmation
- Temporary files in `unassigned/` folder have automatic cleanup policies

## Configuration

### Frontend Configuration
No additional configuration required. The feature is enabled by default.

### Agent Configuration
The healthcare agent prompt includes new instructions for handling files without patient context. See `agents/prompts/healthcare.md` for details.

## API Changes

### SendMessageRequest Interface
Added optional `requiresPatientAssignment` field to attachment objects:

```typescript
attachments?: Array<{
  fileName: string;
  fileSize: number;
  fileType: string;
  category: string;
  s3Key: string;
  content?: string;
  mimeType?: string;
  requiresPatientAssignment?: boolean; // NEW FIELD
}>;
```

## Testing

### Manual Testing
1. Open the chat interface without selecting a patient
2. Attach a medical file (PDF, image, etc.)
3. Send a message asking about the file
4. Verify the agent attempts to identify the patient
5. Confirm the agent asks for confirmation or additional information

### Automated Testing
Run the test script:
```bash
python test_file_without_patient.py
```

## Troubleshooting

### Common Issues

#### Agent Doesn't Identify Patient
- **Cause**: File doesn't contain clear patient identification information
- **Solution**: Agent will ask user for patient details

#### File Upload Fails
- **Cause**: S3 permissions or network issues
- **Solution**: Check S3 bucket permissions and network connectivity

#### Patient Search Returns No Results
- **Cause**: Patient not in database or name/ID mismatch
- **Solution**: Agent will ask user to verify patient information or create new patient record

## Future Enhancements

### Planned Improvements
1. **OCR Integration**: Automatic text extraction from images and scanned documents
2. **Smart Matching**: Fuzzy matching for patient names and IDs
3. **Batch Processing**: Handle multiple files for different patients simultaneously
4. **Auto-Assignment**: Automatic file assignment based on high-confidence matches

### Performance Optimizations
1. **Caching**: Cache patient search results for faster lookups
2. **Async Processing**: Background file analysis for large documents
3. **Compression**: Optimize file storage and transfer

## Related Documentation

- [Healthcare Agent Prompts](../agents/prompts/healthcare.md)
- [File Reference Tools](../agents/tools/file_reference.py)
- [Chat Service Implementation](../apps/frontend/src/services/chatService.ts)
- [Patient Context Extraction](../agents/prompts/patient_context_extraction.md)

## Support

For issues or questions about this feature, please:
1. Check the troubleshooting section above
2. Review the agent logs for error details
3. Test with the provided test script
4. Contact the development team with specific error messages and steps to reproduce
