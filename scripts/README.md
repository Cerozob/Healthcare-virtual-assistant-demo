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

### Schema Migrations

The database initialization Lambda now includes automatic schema migration support:

#### How Migrations Work
- **Automatic**: Migrations run during every stack deployment
- **Safe**: Non-destructive changes that preserve existing data
- **Idempotent**: Can run multiple times without issues
- **Logged**: All migration activities are logged to CloudWatch

#### Current Migrations
1. **Cedula Field Migration**: Adds `cedula VARCHAR(50) UNIQUE` to patients table
   - Adds the field if it doesn't exist
   - Creates index for performance
   - Preserves all existing patient data

#### Testing Migrations
```bash
# Test migration logic locally
python scripts/test_migration.py

# View migration SQL statements
python scripts/add_cedula_field.py --dry-run
```

#### Adding New Migrations
To add new schema migrations:

1. **Update `lambdas/db_initialization/handler.py`**:
   - Add migration logic to `run_schema_migrations()` function
   - Follow the pattern: check if change needed → apply change → log result

2. **Update `lambdas/shared/schema.sql`**:
   - Add new fields/tables to the schema definition
   - This ensures new deployments get the latest schema

3. **Test locally**:
   - Create a test script in `scripts/` directory
   - Verify migration logic before deployment

4. **Deploy**:
   - Run `cdk deploy --all`
   - Monitor CloudWatch logs for migration results

The initialization process is idempotent - it will skip existing tables and data, so it's safe to run multiple times.
