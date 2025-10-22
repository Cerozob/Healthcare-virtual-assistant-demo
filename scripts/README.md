# Database Scripts

This directory contains scripts for managing the healthcare database.

## Database Initialization

Database initialization and sample data population is now handled automatically during stack deployment via the `lambdas/db_initialization/handler.py` Lambda function.

### What Happens During Stack Deployment

1. **Creates all database tables** from the schema in `lambdas/shared/schema.sql`
2. **Creates indexes** for optimal performance
3. **Loads sample patient data** from SampleFileGeneration output (if available in S3)
4. **Inserts sample medics and exams** for testing
5. **Creates Bedrock Knowledge Base table** with vector support

### Sample Data Sources

- **Patients**: Dynamically loaded from S3 bucket containing SampleFileGeneration output
- **Medics**: Hardcoded sample data (3 doctors with different specializations)
- **Exams**: Hardcoded sample data (4 common medical exams)

### Database Schema

The initialization uses the schema defined in `lambdas/shared/schema.sql` which includes:

- **patients**: Extended with JSONB fields for medical_history, lab_results, and address
- **medics**: Standard medical professional information  
- **exams**: Medical examination types and procedures
- **reservations**: Appointment scheduling
- **chat_sessions** and **chat_messages**: Chat functionality
- **processed_documents**: Document workflow results
- **ab2_knowledge_base**: Bedrock Knowledge Base with vector support

### Data Format Conversion

Patient data is automatically converted from SampleFileGeneration `PatientProfile` format:

```json
{
  "patient_id": "uuid",
  "personal_info": {
    "nombre_completo": "Full Name",
    "primer_nombre": "First", 
    "primer_apellido": "Last",
    "fecha_nacimiento": "DD/MM/YYYY",
    "email": "email@example.com"
  },
  "medical_history": { /* complex medical data */ },
  "lab_results": [ /* lab test results */ ]
}
```

To database format with proper field mapping and JSONB storage for complex data.

### Error Handling

- Skips existing records (based on unique constraints)
- Continues processing if individual records fail
- Logs all operations for debugging
- Falls back to basic sample data if S3 data unavailable
- Does not fail stack deployment if sample data population fails

### Monitoring

Check CloudWatch logs for the `healthcare-db-initialization` Lambda function to monitor the initialization process.

### Manual Database Re-initialization

If you need to re-run the database initialization (e.g., after schema changes), you can:

1. **Update the stack** - This will trigger the database initialization Lambda
2. **Check CloudWatch logs** - Monitor the `healthcare-db-initialization` function logs
3. **Verify tables** - Use the API endpoints to verify the database is populated correctly

The initialization process is idempotent - it will skip existing tables and data, so it's safe to run multiple times.
