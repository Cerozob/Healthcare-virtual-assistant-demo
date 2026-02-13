import json
import boto3
import logging
import os
import uuid
from typing import Dict, List, Any, Optional

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Lambda function to load sample data from S3 into the database
    and upload PDFs/images to the raw bucket for document workflow processing.
    
    This function can be invoked manually or triggered after database initialization.
    
    Event parameters:
    - UPDATE_EXISTING_PATIENTS: 'true'/'false' to control whether to update existing patients
    """
    try:
        logger.info("Starting data loading process")
        
        # Get configuration from environment variables
        sample_bucket = os.environ.get('SAMPLE_DATA_BUCKET')
        cluster_arn = os.environ.get('DATABASE_CLUSTER_ARN')
        secret_arn = os.environ.get('DATABASE_SECRET_ARN')
        database_name = os.environ.get('DATABASE_NAME', 'healthcare')
        
        if not all([sample_bucket, cluster_arn, secret_arn]):
            raise ValueError("Missing required environment variables")
        
        # Initialize AWS clients
        rds_data = boto3.client('rds-data')
        s3 = boto3.client('s3')
        ssm = boto3.client('ssm')
        
        # Load and process sample data (JSON profiles only) using UPSERT
        patients_loaded = load_and_process_sample_data(
            s3, rds_data, sample_bucket, 
            cluster_arn, secret_arn, database_name
        )
        
        logger.info(f"Data loading completed successfully. Processed {patients_loaded} patients.")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Data loading completed successfully',
                'patients_loaded': patients_loaded
            })
        }
        
    except Exception as e:
        logger.error(f"Error in data loading: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }


def load_and_process_sample_data(s3, rds_data, sample_bucket: str, 
                               cluster_arn: str, secret_arn: str, database_name: str) -> int:
    """Load sample patient profiles from S3 and insert into database. 
    Modified to load only the FIRST patient for easier debugging."""
    
    logger.info(f"Loading sample data from bucket: {sample_bucket} (DEBUG MODE: single patient only)")
    
    # List all objects in the sample data bucket
    response = s3.list_objects_v2(Bucket=sample_bucket, Prefix='output/')
    
    if 'Contents' not in response:
        logger.warning("No sample data found in S3 bucket")
        return 0
    
    total_objects = len(response['Contents'])
    logger.info(f"Found {total_objects} objects in S3 bucket")
    
    patients_processed = 0
    
    # Find JSON profile files only (PDFs and images are excluded from S3 deployment)
    patient_profiles = []
    
    for obj in response['Contents']:
        key = obj['Key']
        logger.debug(f"Processing object: {key}")
        
        # Skip directories and non-relevant files
        if key.endswith('/') or '.DS_Store' in key:
            continue
            
        # Only process JSON profile files
        if key.endswith('_profile.json'):
            patient_profiles.append(key)
    
    logger.info(f"Found {len(patient_profiles)} patient profiles available")
    
    # DEBUG MODE: Only process the FIRST patient for easier debugging
    if patient_profiles:
        profile_key = patient_profiles[0]  # Take only the first patient
        logger.info(f"DEBUG MODE: Processing only first patient: {profile_key}")
        
        try:
            # Load patient profile
            profile_data = load_patient_profile(s3, sample_bucket, profile_key)
            if profile_data:
                # Upsert patient in database
                upsert_patient_to_database(
                    rds_data, cluster_arn, secret_arn, database_name, profile_data
                )
                
                patients_processed = 1
                patient_name = profile_data.get('personal_info', {}).get('nombre_completo', 'Unknown')
                patient_id = profile_data.get('patient_id', 'Unknown')
                logger.info(f"Successfully processed single patient for debugging: {patient_name} (ID: {patient_id})")
                
        except Exception as e:
            logger.error(f"Failed to process patient profile {profile_key}: {e}")
    else:
        logger.warning("No patient profiles found to process")
    
    # Also load basic sample data (medics and exams) if not already present
    try:
        insert_sample_medics(rds_data, cluster_arn, secret_arn, database_name)
        insert_sample_exams(rds_data, cluster_arn, secret_arn, database_name)
        logger.info("Sample medics and exams loaded successfully")
    except Exception as e:
        logger.warning(f"Failed to load sample medics/exams: {e}")
    
    return patients_processed


def load_patient_profile(s3, bucket: str, key: str) -> Optional[Dict[str, Any]]:
    """Load and parse patient profile JSON from S3."""
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        profile_data = json.loads(response['Body'].read())
        logger.debug(f"Loaded profile from {key}")
        return profile_data
    except Exception as e:
        logger.error(f"Failed to load profile {key}: {e}")
        return None


def upsert_patient_to_database(rds_data, cluster_arn: str, secret_arn: str, 
                             database_name: str, profile: Dict[str, Any]):
    """Upsert patient data using PostgreSQL's INSERT ... ON CONFLICT ... DO UPDATE."""
    
    patient_data = convert_patient_profile_to_db_format(profile)
    
    # Use PostgreSQL UPSERT with ON CONFLICT
    upsert_sql = """
    INSERT INTO patients (
        patient_id, first_name, last_name, full_name, email, cedula, date_of_birth, phone,
        age, gender, document_type, document_number,
        address, medical_history, lab_results, source_scan, created_at, updated_at
    ) VALUES (
        :patient_id, :first_name, :last_name, :full_name, :email, :cedula, :date_of_birth::date, :phone,
        :age, :gender, :document_type, :document_number,
        :address::jsonb, :medical_history::jsonb, :lab_results::jsonb, :source_scan,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    )
    ON CONFLICT (patient_id) 
    DO UPDATE SET
        first_name = EXCLUDED.first_name,
        last_name = EXCLUDED.last_name,
        full_name = EXCLUDED.full_name,
        email = EXCLUDED.email,
        cedula = COALESCE(EXCLUDED.cedula, patients.cedula),
        date_of_birth = EXCLUDED.date_of_birth,
        phone = EXCLUDED.phone,
        age = EXCLUDED.age,
        gender = EXCLUDED.gender,
        document_type = EXCLUDED.document_type,
        document_number = EXCLUDED.document_number,
        address = EXCLUDED.address,
        medical_history = EXCLUDED.medical_history,
        lab_results = EXCLUDED.lab_results,
        source_scan = EXCLUDED.source_scan,
        updated_at = CURRENT_TIMESTAMP
    """
    
    parameters = []
    for key, value in patient_data.items():
        if value is None:
            param_value = {'isNull': True}
        elif key == 'date_of_birth' and value is not None:
            param_value = {'stringValue': str(value)}
        elif key == 'age' and value is not None:
            param_value = {'longValue': int(value)}
        else:
            param_value = {'stringValue': str(value) if value is not None else None}
        
        parameters.append({'name': key, 'value': param_value})
    
    try:
        rds_data.execute_statement(
            resourceArn=cluster_arn,
            secretArn=secret_arn,
            database=database_name,
            sql=upsert_sql,
            parameters=parameters
        )
        
        cedula_info = f" (cedula: {patient_data.get('cedula', 'None')})" if patient_data.get('cedula') else " (no cedula)"
        logger.info(f"Upserted patient: {patient_data['full_name']}{cedula_info}")
        
    except Exception as e:
        if "duplicate key value violates unique constraint" in str(e).lower():
            if "cedula" in str(e).lower():
                logger.warning(f"Cedula conflict for patient {patient_data['full_name']}: {patient_data.get('cedula', 'None')} - trying without cedula")
                # Retry without cedula
                upsert_sql_no_cedula = """
                INSERT INTO patients (
                    patient_id, first_name, last_name, full_name, email, date_of_birth, phone,
                    age, gender, document_type, document_number,
                    address, medical_history, lab_results, source_scan, created_at, updated_at
                ) VALUES (
                    :patient_id, :first_name, :last_name, :full_name, :email, :date_of_birth::date, :phone,
                    :age, :gender, :document_type, :document_number,
                    :address::jsonb, :medical_history::jsonb, :lab_results::jsonb, :source_scan,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                ON CONFLICT (patient_id) 
                DO UPDATE SET
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    full_name = EXCLUDED.full_name,
                    email = EXCLUDED.email,
                    date_of_birth = EXCLUDED.date_of_birth,
                    phone = EXCLUDED.phone,
                    age = EXCLUDED.age,
                    gender = EXCLUDED.gender,
                    document_type = EXCLUDED.document_type,
                    document_number = EXCLUDED.document_number,
                    address = EXCLUDED.address,
                    medical_history = EXCLUDED.medical_history,
                    lab_results = EXCLUDED.lab_results,
                    source_scan = EXCLUDED.source_scan,
                    updated_at = CURRENT_TIMESTAMP
                """
                
                # Remove cedula from parameters
                params_no_cedula = [p for p in parameters if p['name'] != 'cedula']
                
                rds_data.execute_statement(
                    resourceArn=cluster_arn,
                    secretArn=secret_arn,
                    database=database_name,
                    sql=upsert_sql_no_cedula,
                    parameters=params_no_cedula
                )
                
                logger.info(f"Upserted patient without cedula: {patient_data['full_name']}")
            else:
                logger.warning(f"Duplicate key conflict for patient {patient_data['full_name']} - {e}")
        else:
            logger.error(f"Failed to upsert patient {patient_data['full_name']}: {e}")
            raise


def convert_patient_profile_to_db_format(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Convert PatientProfile format to database format (updated for current schema)."""
    
    personal_info = profile.get('personal_info', {})
    
    # Parse full name into first_name and last_name
    full_name = personal_info.get('nombre_completo', '')
    first_name = ''
    last_name = ''
    
    if full_name:
        name_parts = full_name.split()
        if len(name_parts) >= 2:
            first_name = name_parts[0]
            last_name = ' '.join(name_parts[1:])
        elif len(name_parts) == 1:
            first_name = name_parts[0]
            last_name = ''
    
    # Parse date of birth
    fecha_nacimiento = personal_info.get('fecha_nacimiento', '')
    date_of_birth = None
    if fecha_nacimiento:
        try:
            # Convert from DD/MM/YYYY to YYYY-MM-DD
            if '/' in fecha_nacimiento:
                day, month, year = fecha_nacimiento.split('/')
                date_of_birth = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            elif '-' in fecha_nacimiento and len(fecha_nacimiento) == 10:
                # Already in YYYY-MM-DD format
                date_of_birth = fecha_nacimiento
            else:
                logger.warning(f"Unrecognized date format: {fecha_nacimiento}")
        except Exception as e:
            logger.warning(f"Could not parse date of birth '{fecha_nacimiento}': {e}")
    
    # Extract age and gender
    age = personal_info.get('edad')
    gender = personal_info.get('sexo')
    
    # Extract document type and number
    document_type = personal_info.get('tipo_documento', '').strip()
    document_number = personal_info.get('numero_documento', '').strip()
    
    # Extract cedula from document number if document type is cedula/ID
    cedula = None
    cedula_types = ['cedula', 'cédula', 'id', 'dni', 'cc', 'ci', 'rut', 'curp', 'dui']
    
    if document_type.lower() in cedula_types and document_number:
        # Clean the document number (remove any non-alphanumeric characters except hyphens)
        import re
        cedula = re.sub(r'[^\w\-]', '', document_number)
        logger.info(f"Extracted cedula: {cedula} from document type: {document_type}")
    
    # Build enhanced medical history with additional patient info
    enhanced_medical_history = profile.get('medical_history', {})
    
    # Add demographic info to medical history for context
    if age:
        enhanced_medical_history['age'] = age
    if gender:
        enhanced_medical_history['gender'] = gender
    if document_type and document_number:
        enhanced_medical_history['document'] = {
            'type': document_type,
            'number': document_number
        }
    
    return {
        'patient_id': profile.get('patient_id', str(uuid.uuid4())),
        'first_name': first_name,
        'last_name': last_name,
        'full_name': full_name,
        'email': personal_info.get('email', ''),
        'cedula': cedula,
        'phone': personal_info.get('telefono', ''),
        'date_of_birth': date_of_birth,
        'age': age,
        'gender': gender,
        'document_type': document_type,
        'document_number': document_number,
        'address': json.dumps(personal_info.get('direccion', {})),
        'medical_history': json.dumps(enhanced_medical_history),
        'lab_results': json.dumps(profile.get('lab_results', [])),
        'source_scan': profile.get('source_scan')
    }


def insert_sample_medics(rds_data, cluster_arn: str, secret_arn: str, database_name: str):
    """Insert sample medics data."""

    sample_medics = [
        {
            'medic_id': str(uuid.uuid4()),
            'first_name': 'Dr. Sarah Wilson',
            'email': 'sarah.wilson@hospital.com',
            'phone': '+1-555-0101',
            'specialization': 'Cardiology',
            'license_number': 'MD-001-2024',
            'department': 'Cardiology'
        },
        {
            'medic_id': str(uuid.uuid4()),
            'first_name': 'Dr. Michael Brown',
            'email': 'michael.brown@hospital.com',
            'phone': '+1-555-0102',
            'specialization': 'Radiology',
            'license_number': 'MD-002-2024',
            'department': 'Radiology'
        },
        {
            'medic_id': str(uuid.uuid4()),
            'first_name': 'Dr. Emily Davis',
            'email': 'emily.davis@hospital.com',
            'phone': '+1-555-0103',
            'specialization': 'General Medicine',
            'license_number': 'MD-003-2024',
            'department': 'General Medicine'
        }
    ]

    for medic in sample_medics:
        try:
            # Use UPSERT for medics
            upsert_sql = """
            INSERT INTO medics (
                medic_id, first_name, email, phone,
                specialization, license_number, department, created_at, updated_at
            ) VALUES (
                :medic_id, :first_name, :email, :phone,
                :specialization, :license_number, :department, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            ON CONFLICT (email) 
            DO UPDATE SET
                first_name = EXCLUDED.first_name,
                phone = EXCLUDED.phone,
                specialization = EXCLUDED.specialization,
                license_number = EXCLUDED.license_number,
                department = EXCLUDED.department,
                updated_at = CURRENT_TIMESTAMP
            """

            parameters = []
            for key, value in medic.items():
                parameters.append(
                    {'name': key, 'value': {'stringValue': value}})

            rds_data.execute_statement(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database=database_name,
                sql=upsert_sql,
                parameters=parameters
            )

            logger.info(f"Upserted medic: {medic['first_name']}")

        except Exception as e:
            logger.error(f"Failed to insert medic {medic['first_name']}: {e}")


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
            # Use UPSERT for exams
            upsert_sql = """
            INSERT INTO exams (
                exam_id, exam_name, exam_type, description, duration_minutes, preparation_instructions, created_at, updated_at
            ) VALUES (
                :exam_id, :exam_name, :exam_type, :description, :duration_minutes, :preparation_instructions, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            ON CONFLICT (exam_name) 
            DO UPDATE SET
                exam_type = EXCLUDED.exam_type,
                description = EXCLUDED.description,
                duration_minutes = EXCLUDED.duration_minutes,
                preparation_instructions = EXCLUDED.preparation_instructions,
                updated_at = CURRENT_TIMESTAMP
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
                sql=upsert_sql,
                parameters=parameters
            )

            logger.info(f"Upserted exam: {exam['exam_name']}")

        except Exception as e:
            logger.error(f"Failed to insert exam {exam['exam_name']}: {e}")
