import json
import boto3
import logging
import uuid
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def wait_for_database_ready(rds_data, cluster_arn: str, secret_arn: str, database_name: str, max_retries: int = 10):
    """Wait for database to be ready after auto-pause resume."""
    for attempt in range(max_retries):
        try:
            # Simple query to test database readiness
            rds_data.execute_statement(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database=database_name,
                sql="SELECT 1;"
            )
            logger.info(f"Database ready after {attempt + 1} attempts")
            return
        except Exception as e:
            if "DatabaseResumingException" in str(e) or "resuming after being auto-paused" in str(e):
                wait_time = min(5 + (attempt * 2), 30)  # Exponential backoff, max 30s
                logger.info(f"Database resuming, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                raise e
    
    raise Exception("Database did not become ready after maximum retries")


def lambda_handler(event, context):
    try:
        request_type = event['RequestType']

        if request_type == 'Create' or request_type == 'Update':
            # Get database connection details from event
            secret_arn = event['ResourceProperties']['SecretArn']
            cluster_arn = event['ResourceProperties']['ClusterArn']
            database_name = event['ResourceProperties']['DatabaseName']
            table_name = event['ResourceProperties']['TableName']

            # Use RDS Data API
            rds_data = boto3.client('rds-data')

            # Enable pgvector extension with retry logic
            try:
                wait_for_database_ready(rds_data, cluster_arn, secret_arn, database_name)
                rds_data.execute_statement(
                    resourceArn=cluster_arn,
                    secretArn=secret_arn,
                    database=database_name,
                    sql="CREATE EXTENSION IF NOT EXISTS vector;"
                )
                logger.info("pgvector extension enabled")
            except Exception as e:
                logger.warning(f"pgvector extension may already exist: {e}")

            # Create all healthcare system tables
            create_healthcare_tables(
                rds_data, cluster_arn, secret_arn, database_name)

            # Create Bedrock integration schema and user following AWS blog post requirements
            # https://aws.amazon.com/blogs/database/build-generative-ai-applications-with-amazon-aurora-and-amazon-bedrock-knowledge-bases/
            try:
                # Create bedrock_integration schema
                rds_data.execute_statement(
                    resourceArn=cluster_arn,
                    secretArn=secret_arn,
                    database=database_name,
                    sql="CREATE SCHEMA IF NOT EXISTS bedrock_integration;"
                )
                logger.info("Created bedrock_integration schema")

                # Create bedrock_user role
                rds_data.execute_statement(
                    resourceArn=cluster_arn,
                    secretArn=secret_arn,
                    database=database_name,
                    sql="CREATE ROLE bedrock_user LOGIN;"
                )
                logger.info("Created bedrock_user role")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info("Bedrock schema and user already exist")
                else:
                    logger.warning(f"Failed to create bedrock schema/user: {e}")

            try:
                # Set password for bedrock_user using the dedicated secret
                bedrock_secret_arn = os.environ.get('BEDROCK_USER_SECRET_ARN')
                if bedrock_secret_arn:
                    # Get the password from the bedrock user secret
                    secretsmanager = boto3.client('secretsmanager')
                    bedrock_secret_response = secretsmanager.get_secret_value(SecretId=bedrock_secret_arn)
                    bedrock_secret_data = json.loads(bedrock_secret_response['SecretString'])
                    bedrock_password = bedrock_secret_data['password']
                    
                    rds_data.execute_statement(
                        resourceArn=cluster_arn,
                        secretArn=secret_arn,
                        database=database_name,
                        sql=f"ALTER USER bedrock_user PASSWORD '{bedrock_password}';"
                    )
                    logger.info("Set password for bedrock_user using dedicated secret")
                else:
                    logger.warning("BEDROCK_USER_SECRET_ARN not provided, skipping password setup")
            except Exception as e:
                logger.warning(f"Failed to set bedrock_user password: {e}")

            try:
                # Grant permissions to bedrock_user
                rds_data.execute_statement(
                    resourceArn=cluster_arn,
                    secretArn=secret_arn,
                    database=database_name,
                    sql="GRANT ALL ON SCHEMA bedrock_integration TO bedrock_user;"
                )
                logger.info("Granted permissions to bedrock_user")
                
                # Also ensure the main database user has vector extension permissions
                rds_data.execute_statement(
                    resourceArn=cluster_arn,
                    secretArn=secret_arn,
                    database=database_name,
                    sql="GRANT USAGE ON SCHEMA public TO bedrock_user;"
                )
                logger.info("Granted public schema usage to bedrock_user")
            except Exception as e:
                logger.warning(f"Failed to grant permissions: {e}")

            # Create the knowledge base table following AWS documentation structure
            # https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-setup.html
            try:
                create_table_sql = f'''
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                    embedding vector(1024),
                    chunks text,
                    metadata json,
                    custom_metadata jsonb
                );
                '''

                rds_data.execute_statement(
                    resourceArn=cluster_arn,
                    secretArn=secret_arn,
                    database=database_name,
                    sql=create_table_sql
                )
                logger.info(f"Knowledge base table {table_name} created successfully with AWS blog post structure")
            except Exception as e:
                if "type \"vector\" does not exist" in str(e):
                    logger.error(f"Vector extension not available. Knowledge base table creation failed: {e}")
                    # This will cause the knowledge base creation to fail, which is expected
                    raise
                else:
                    logger.warning(f"Knowledge base table creation failed: {e}")

            # Create required indexes as per AWS documentation
            # 1. HNSW index for vector similarity search (required)
            try:
                vector_index_sql = f"CREATE INDEX IF NOT EXISTS {table_name}_embedding_hnsw_idx ON {table_name} USING hnsw (embedding vector_cosine_ops);"

                rds_data.execute_statement(
                    resourceArn=cluster_arn,
                    secretArn=secret_arn,
                    database=database_name,
                    sql=vector_index_sql
                )
                logger.info("HNSW vector index created (required)")
            except Exception as e:
                logger.warning(f"Failed to create vector index: {e}")

            # 2. GIN index for text search (required)
            try:
                text_index_sql = f"CREATE INDEX IF NOT EXISTS {table_name}_chunks_gin_idx ON {table_name} USING gin (to_tsvector('simple', chunks));"

                rds_data.execute_statement(
                    resourceArn=cluster_arn,
                    secretArn=secret_arn,
                    database=database_name,
                    sql=text_index_sql
                )
                logger.info("GIN text index created (required)")
            except Exception as e:
                logger.warning(f"Failed to create text index: {e}")

            # 3. GIN index for custom metadata (optional but recommended)
            try:
                metadata_index_sql = f"CREATE INDEX IF NOT EXISTS {table_name}_custom_metadata_gin_idx ON {table_name} USING gin (custom_metadata);"

                rds_data.execute_statement(
                    resourceArn=cluster_arn,
                    secretArn=secret_arn,
                    database=database_name,
                    sql=metadata_index_sql
                )
                logger.info("GIN custom metadata index created (optional)")
            except Exception as e:
                logger.warning(f"Failed to create custom metadata index: {e}")

            # Populate with sample data
            populate_sample_data(rds_data, cluster_arn,
                                 secret_arn, database_name)

            logger.info(
                f"Successfully initialized database with tables, indexes, and sample data")

            return {
                'Status': 'SUCCESS',
                'PhysicalResourceId': f'{table_name}-initialization',
                'Data': {'TableName': table_name}
            }

        elif request_type == 'Delete':
            # Optionally clean up the table on stack deletion
            logger.info("Delete request - no action needed")
            return {
                'Status': 'SUCCESS',
                'PhysicalResourceId': event.get('PhysicalResourceId', 'default')
            }

    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return {
            'Status': 'FAILED',
            'Reason': str(e),
            'PhysicalResourceId': event.get('PhysicalResourceId', 'default')
        }


def create_healthcare_tables(rds_data, cluster_arn: str, secret_arn: str, database_name: str):
    """Create all healthcare system tables by reading and parsing the schema.sql file."""

    try:
        # Read the schema.sql file from the shared module
        schema_content = None

        # Try different possible paths for the schema file in Lambda environment
        possible_paths = [
            "/var/task/shared/schema.sql",    # Lambda function package
            "shared/schema.sql",              # Relative path
            "/opt/python/shared/schema.sql"   # Lambda layer (if used)
        ]

        for path in possible_paths:
            try:
                with open(path, 'r') as f:
                    schema_content = f.read()
                logger.info(f"Successfully read schema from: {path}")
                break
            except FileNotFoundError:
                logger.debug(f"Schema file not found at: {path}")
                continue

        if not schema_content:
            logger.error(
                "Could not find schema.sql file in any expected location")
            raise FileNotFoundError("schema.sql not found")

        # Parse the schema content into individual SQL statements
        statements = parse_sql_statements(schema_content)

        logger.info(f"Parsed {len(statements)} SQL statements from schema.sql")

        # Separate CREATE TABLE and CREATE INDEX statements
        table_statements = []
        index_statements = []
        
        for statement in statements:
            if not statement.strip() or statement.strip().startswith('--'):
                continue
            
            statement_upper = statement.strip().upper()
            if statement_upper.startswith('CREATE TABLE'):
                table_statements.append(statement)
            elif statement_upper.startswith('CREATE INDEX'):
                index_statements.append(statement)
            else:
                table_statements.append(statement)  # Other statements like extensions
        
        # Execute table creation first
        executed_count = 0
        logger.info(f"Creating {len(table_statements)} tables...")
        
        for i, statement in enumerate(table_statements, 1):
            try:
                logger.debug(f"Executing table statement {i}: {statement[:100]}...")
                
                rds_data.execute_statement(
                    resourceArn=cluster_arn,
                    secretArn=secret_arn,
                    database=database_name,
                    sql=statement
                )
                
                executed_count += 1
                logger.info(f"Successfully executed table statement {i}")
                
            except Exception as e:
                error_msg = str(e).lower()
                if any(phrase in error_msg for phrase in ["already exists", "duplicate"]):
                    logger.info(f"Table statement {i} - object already exists, skipping")
                elif "type \"vector\" does not exist" in error_msg:
                    logger.warning(f"Vector type not available, skipping knowledge base table")
                else:
                    logger.error(f"Failed to execute table statement {i}: {e}")
                    logger.error(f"Statement was: {statement}")
                    # Continue with other statements
                    continue
        
        # Execute index creation after tables
        logger.info(f"Creating {len(index_statements)} indexes...")
        
        for i, statement in enumerate(index_statements, 1):
            try:
                logger.debug(f"Executing index statement {i}: {statement[:100]}...")
                
                rds_data.execute_statement(
                    resourceArn=cluster_arn,
                    secretArn=secret_arn,
                    database=database_name,
                    sql=statement
                )
                
                executed_count += 1
                logger.info(f"Successfully executed index statement {i}")
                
            except Exception as e:
                error_msg = str(e).lower()
                if any(phrase in error_msg for phrase in ["already exists", "duplicate"]):
                    logger.info(f"Index statement {i} - object already exists, skipping")
                elif "does not exist" in error_msg:
                    logger.warning(f"Index statement {i} - table doesn't exist yet, skipping")
                else:
                    logger.error(f"Failed to execute index statement {i}: {e}")
                    logger.error(f"Statement was: {statement}")
                    # Continue with other statements
                    continue

        logger.info(
            f"Healthcare tables creation completed - executed {executed_count} statements")

    except Exception as e:
        logger.error(f"Failed to create healthcare tables: {e}")
        raise


def parse_sql_statements(sql_content: str) -> list:
    """Parse SQL content into individual executable statements."""

    statements = []
    current_statement = []
    in_comment_block = False

    for line in sql_content.split('\n'):
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Handle multi-line comments
        if line.startswith('/*'):
            in_comment_block = True
            continue
        if line.endswith('*/'):
            in_comment_block = False
            continue
        if in_comment_block:
            continue

        # Skip single-line comments
        if line.startswith('--'):
            continue

        # Add line to current statement
        current_statement.append(line)

        # If line ends with semicolon, it's the end of a statement
        if line.endswith(';'):
            statement = ' '.join(current_statement)
            if statement.strip():
                statements.append(statement)
            current_statement = []

    # Handle any remaining statement without semicolon
    if current_statement:
        statement = ' '.join(current_statement)
        if statement.strip():
            statements.append(statement)

    return statements


def populate_sample_data(rds_data, cluster_arn: str, secret_arn: str, database_name: str):
    """Populate database with sample data."""

    try:
        # Load sample patients from S3 if available
        sample_patients = load_sample_patients_from_s3()

        # If no S3 data, create basic sample patients
        if not sample_patients:
            sample_patients = create_basic_sample_patients()

        # Insert sample patients
        insert_sample_patients(rds_data, cluster_arn,
                               secret_arn, database_name, sample_patients)

        # Insert sample medics and exams
        insert_sample_medics(rds_data, cluster_arn, secret_arn, database_name)
        insert_sample_exams(rds_data, cluster_arn, secret_arn, database_name)

        logger.info("Sample data population completed")

    except Exception as e:
        logger.error(f"Failed to populate sample data: {e}")
        # Don't fail the entire initialization if sample data fails
        logger.warning("Continuing without sample data")


def load_sample_patients_from_s3() -> List[Dict[str, Any]]:
    """Load sample patient data from S3 bucket if available."""

    try:
        # Try to find sample data in S3
        s3 = boto3.client('s3')

        # Look for a bucket with sample data (this would be configured in the stack)
        sample_bucket = os.environ.get('SAMPLE_DATA_BUCKET')
        if not sample_bucket:
            logger.info("No sample data bucket configured")
            return []

        # List objects in the sample data bucket
        response = s3.list_objects_v2(Bucket=sample_bucket, Prefix='output/')

        patients = []
        for obj in response.get('Contents', []):
            if obj['Key'].endswith('_profile.json'):
                try:
                    # Download and parse the profile
                    profile_response = s3.get_object(
                        Bucket=sample_bucket, Key=obj['Key'])
                    profile_data = json.loads(profile_response['Body'].read())
                    patients.append(profile_data)
                    logger.info(
                        f"Loaded patient profile from S3: {obj['Key']}")
                except Exception as e:
                    logger.warning(f"Failed to load profile {obj['Key']}: {e}")

        logger.info(f"Loaded {len(patients)} patient profiles from S3")
        return patients

    except Exception as e:
        logger.warning(f"Failed to load sample data from S3: {e}")
        return []


def create_basic_sample_patients() -> List[Dict[str, Any]]:
    """Create basic sample patient data if no S3 data is available."""

    return [
        {
            'patient_id': str(uuid.uuid4()),
            'personal_info': {
                'nombre_completo': 'Juan Carlos Pérez García',
                'primer_nombre': 'Juan Carlos',
                'primer_apellido': 'Pérez',
                'segundo_apellido': 'García',
                'fecha_nacimiento': '15/03/1985',
                'edad': 39,
                'sexo': 'M',
                'tipo_documento': 'DNI',
                'numero_documento': '12345678A',
                'direccion': {
                    'street': 'Calle Mayor 123',
                    'city': 'Madrid',
                    'province': 'Madrid',
                    'postal_code': '28001',
                    'country': 'España'
                },
                'telefono': '+34-600-123-456',
                'email': 'juan.perez@email.com'
            },
            'medical_history': {
                'conditions': [
                    {
                        'descripcion': 'Hipertensión arterial',
                        'fecha_diagnostico': '10/01/2020',
                        'estado': 'activo'
                    }
                ],
                'medications': [
                    {
                        'nombre': 'Enalapril',
                        'dosis': '10mg',
                        'frecuencia': '1 vez al día',
                        'fecha_inicio': '10/01/2020',
                        'activo': True
                    }
                ]
            },
            'lab_results': []
        },
        {
            'patient_id': str(uuid.uuid4()),
            'personal_info': {
                'nombre_completo': 'María Elena Rodríguez López',
                'primer_nombre': 'María Elena',
                'primer_apellido': 'Rodríguez',
                'segundo_apellido': 'López',
                'fecha_nacimiento': '22/07/1990',
                'edad': 34,
                'sexo': 'F',
                'tipo_documento': 'DNI',
                'numero_documento': '87654321B',
                'direccion': {
                    'street': 'Avenida de la Paz 456',
                    'city': 'Barcelona',
                    'province': 'Barcelona',
                    'postal_code': '08001',
                    'country': 'España'
                },
                'telefono': '+34-600-654-321',
                'email': 'maria.rodriguez@email.com'
            },
            'medical_history': {
                'conditions': [],
                'medications': []
            },
            'lab_results': []
        }
    ]


def convert_patient_profile_to_db_format(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Convert PatientProfile format to database format."""

    personal_info = profile.get('personal_info', {})

    # Parse date of birth
    fecha_nacimiento = personal_info.get('fecha_nacimiento', '')
    date_of_birth = None
    if fecha_nacimiento:
        try:
            # Convert from DD/MM/YYYY to YYYY-MM-DD
            day, month, year = fecha_nacimiento.split('/')
            date_of_birth = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except:
            logger.warning(
                f"Could not parse date of birth: {fecha_nacimiento}")

    return {
        'patient_id': profile.get('patient_id', str(uuid.uuid4())),
        'first_name': personal_info.get('primer_nombre', ''),
        'last_name': f"{personal_info.get('primer_apellido', '')} {personal_info.get('segundo_apellido', '')}".strip(),
        'full_name': personal_info.get('nombre_completo', ''),
        'email': personal_info.get('email', ''),
        'phone': personal_info.get('telefono', ''),
        'date_of_birth': date_of_birth,
        'age': personal_info.get('edad'),
        'gender': personal_info.get('sexo'),
        'document_type': personal_info.get('tipo_documento'),
        'document_number': personal_info.get('numero_documento'),
        'address': json.dumps(personal_info.get('direccion', {})),
        'medical_history': json.dumps(profile.get('medical_history', {})),
        'lab_results': json.dumps(profile.get('lab_results', [])),
        'source_scan': profile.get('source_scan')
    }


def insert_sample_patients(rds_data, cluster_arn: str, secret_arn: str, database_name: str, patients: List[Dict[str, Any]]):
    """Insert sample patients into the database."""

    for i, profile in enumerate(patients, 1):
        try:
            patient_data = convert_patient_profile_to_db_format(profile)

            # Check if patient already exists
            check_response = rds_data.execute_statement(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database=database_name,
                sql="SELECT COUNT(*) as count FROM patients WHERE patient_id = :patient_id",
                parameters=[{'name': 'patient_id', 'value': {
                    'stringValue': patient_data['patient_id']}}]
            )

            if check_response['records'][0][0].get('longValue', 0) > 0:
                logger.info(f"Patient {i} already exists, skipping")
                continue

            # Insert patient
            insert_sql = """
            INSERT INTO patients (
                patient_id, first_name, last_name, full_name, email, phone,
                date_of_birth, age, gender, document_type, document_number,
                address, medical_history, lab_results, source_scan
            ) VALUES (
                :patient_id, :first_name, :last_name, :full_name, :email, :phone,
                :date_of_birth, :age, :gender, :document_type, :document_number,
                :address::jsonb, :medical_history::jsonb, :lab_results::jsonb, :source_scan
            )
            """

            parameters = []
            for key, value in patient_data.items():
                param_value = {'stringValue': str(
                    value) if value is not None else None}
                if value is None:
                    param_value = {'isNull': True}
                elif key == 'age' and value is not None:
                    param_value = {'longValue': int(value)}

                parameters.append({'name': key, 'value': param_value})

            rds_data.execute_statement(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database=database_name,
                sql=insert_sql,
                parameters=parameters
            )

            logger.info(f"Inserted patient {i}: {patient_data['full_name']}")

        except Exception as e:
            logger.error(f"Failed to insert patient {i}: {e}")


def insert_sample_medics(rds_data, cluster_arn: str, secret_arn: str, database_name: str):
    """Insert sample medics data."""

    sample_medics = [
        {
            'medic_id': str(uuid.uuid4()),
            'first_name': 'Dr. Sarah',
            'last_name': 'Wilson',
            'full_name': 'Dr. Sarah Wilson',
            'email': 'sarah.wilson@hospital.com',
            'phone': '+1-555-0101',
            'specialization': 'Cardiology',
            'license_number': 'MD-001-2024',
            'department': 'Cardiology'
        },
        {
            'medic_id': str(uuid.uuid4()),
            'first_name': 'Dr. Michael',
            'last_name': 'Brown',
            'full_name': 'Dr. Michael Brown',
            'email': 'michael.brown@hospital.com',
            'phone': '+1-555-0102',
            'specialization': 'Radiology',
            'license_number': 'MD-002-2024',
            'department': 'Radiology'
        },
        {
            'medic_id': str(uuid.uuid4()),
            'first_name': 'Dr. Emily',
            'last_name': 'Davis',
            'full_name': 'Dr. Emily Davis',
            'email': 'emily.davis@hospital.com',
            'phone': '+1-555-0103',
            'specialization': 'General Medicine',
            'license_number': 'MD-003-2024',
            'department': 'General Medicine'
        }
    ]

    for medic in sample_medics:
        try:
            # Check if medic already exists
            check_response = rds_data.execute_statement(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database=database_name,
                sql="SELECT COUNT(*) as count FROM medics WHERE email = :email",
                parameters=[{'name': 'email', 'value': {
                    'stringValue': medic['email']}}]
            )

            if check_response['records'][0][0].get('longValue', 0) > 0:
                logger.info(
                    f"Medic already exists, skipping: {medic['email']}")
                continue

            # Insert medic
            insert_sql = """
            INSERT INTO medics (
                medic_id, first_name, last_name, full_name, email, phone,
                specialization, license_number, department
            ) VALUES (
                :medic_id, :first_name, :last_name, :full_name, :email, :phone,
                :specialization, :license_number, :department
            )
            """

            parameters = []
            for key, value in medic.items():
                parameters.append(
                    {'name': key, 'value': {'stringValue': value}})

            rds_data.execute_statement(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database=database_name,
                sql=insert_sql,
                parameters=parameters
            )

            logger.info(f"Inserted medic: {medic['full_name']}")

        except Exception as e:
            logger.error(f"Failed to insert medic {medic['full_name']}: {e}")


def insert_sample_exams(rds_data, cluster_arn: str, secret_arn: str, database_name: str):
    """Insert sample exams data."""

    sample_exams = [
        {
            'exam_id': str(uuid.uuid4()),
            'exam_name': 'Chest X-Ray',
            'exam_type': 'Radiology',
            'description': 'Standard chest radiography examination',
            'duration_minutes': 15,
            'preparation_instructions': 'Remove all metal objects from chest area'
        },
        {
            'exam_id': str(uuid.uuid4()),
            'exam_name': 'ECG',
            'exam_type': 'Cardiology',
            'description': 'Electrocardiogram to assess heart rhythm',
            'duration_minutes': 20,
            'preparation_instructions': 'Avoid caffeine 2 hours before exam'
        },
        {
            'exam_id': str(uuid.uuid4()),
            'exam_name': 'Blood Test - Complete Panel',
            'exam_type': 'Laboratory',
            'description': 'Complete blood count and basic metabolic panel',
            'duration_minutes': 10,
            'preparation_instructions': 'Fasting for 8-12 hours required'
        },
        {
            'exam_id': str(uuid.uuid4()),
            'exam_name': 'Physical Examination',
            'exam_type': 'General Medicine',
            'description': 'Comprehensive physical examination',
            'duration_minutes': 30,
            'preparation_instructions': 'Bring list of current medications'
        }
    ]

    for exam in sample_exams:
        try:
            # Check if exam already exists
            check_response = rds_data.execute_statement(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database=database_name,
                sql="SELECT COUNT(*) as count FROM exams WHERE exam_name = :exam_name",
                parameters=[{'name': 'exam_name', 'value': {
                    'stringValue': exam['exam_name']}}]
            )

            if check_response['records'][0][0].get('longValue', 0) > 0:
                logger.info(
                    f"Exam already exists, skipping: {exam['exam_name']}")
                continue

            # Insert exam
            insert_sql = """
            INSERT INTO exams (
                exam_id, exam_name, exam_type, description, duration_minutes, preparation_instructions
            ) VALUES (
                :exam_id, :exam_name, :exam_type, :description, :duration_minutes, :preparation_instructions
            )
            """

            parameters = []
            for key, value in exam.items():
                if key == 'duration_minutes':
                    parameters.append(
                        {'name': key, 'value': {'longValue': value}})
                else:
                    parameters.append(
                        {'name': key, 'value': {'stringValue': str(value)}})

            rds_data.execute_statement(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database=database_name,
                sql=insert_sql,
                parameters=parameters
            )

            logger.info(f"Inserted exam: {exam['exam_name']}")

        except Exception as e:
            logger.error(f"Failed to insert exam {exam['exam_name']}: {e}")
