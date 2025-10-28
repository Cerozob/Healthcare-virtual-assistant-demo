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
        
        # Check if we should update existing patients
        # Priority: event parameter > environment variable > default (true)
        update_existing = True  # Default for cedula repopulation
        if 'UPDATE_EXISTING_PATIENTS' in event:
            update_existing = str(event['UPDATE_EXISTING_PATIENTS']).lower() == 'true'
        elif 'UPDATE_EXISTING_PATIENTS' in os.environ:
            update_existing = os.environ.get('UPDATE_EXISTING_PATIENTS', 'true').lower() == 'true'
        
        logger.info(f"Update existing patients: {update_existing}")
        
        # Load and process sample data (JSON profiles only)
        patients_loaded = load_and_process_sample_data(
            s3, rds_data, sample_bucket, 
            cluster_arn, secret_arn, database_name, update_existing
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
                               cluster_arn: str, secret_arn: str, database_name: str, update_existing: bool = True) -> int:
    """Load sample patient profiles from S3 and insert into database."""
    
    logger.info(f"Loading sample data from bucket: {sample_bucket}")
    
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
    
    logger.info(f"Found {len(patient_profiles)} patient profiles to process")
    
    # Process each patient profile
    for i, profile_key in enumerate(patient_profiles, 1):
        try:
            # Load patient profile
            profile_data = load_patient_profile(s3, sample_bucket, profile_key)
            if not profile_data:
                continue
            
            # Insert or update patient in database
            insert_patient_to_database(
                rds_data, cluster_arn, secret_arn, database_name, profile_data, update_existing
            )
            
            patients_processed += 1
            patient_name = profile_data.get('personal_info', {}).get('nombre_completo', 'Unknown')
            logger.info(f"Successfully processed patient {i}/{len(patient_profiles)}: {patient_name}")
            
        except Exception as e:
            logger.error(f"Failed to process patient profile {profile_key}: {e}")
            # Continue with other patients
            continue
    
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


def insert_patient_to_database(rds_data, cluster_arn: str, secret_arn: str, 
                             database_name: str, profile: Dict[str, Any], update_existing: bool = True):
    """Insert or update patient data in the database."""
    
    patient_data = convert_patient_profile_to_db_format(profile)
    
    # Check if patient already exists
    check_response = rds_data.execute_statement(
        resourceArn=cluster_arn,
        secretArn=secret_arn,
        database=database_name,
        sql="SELECT patient_id FROM patients WHERE patient_id = :patient_id OR email = :email",
        parameters=[
            {'name': 'patient_id', 'value': {'stringValue': patient_data['patient_id']}},
            {'name': 'email', 'value': {'stringValue': patient_data.get('email', '')}}
        ]
    )
    
    existing_records = check_response.get('records', [])
    
    if existing_records:
        if update_existing:
            # Patient exists - update with new data including cedula
            existing_patient_id = existing_records[0][0].get('stringValue')
            logger.info(f"Patient exists, updating with cedula: {patient_data.get('full_name', 'Unknown')}")
            update_patient_in_database(rds_data, cluster_arn, secret_arn, database_name, existing_patient_id, patient_data)
        else:
            logger.info(f"Patient exists, skipping (update_existing=False): {patient_data.get('full_name', 'Unknown')}")
        return
    
    # Insert patient (updated to match current schema)
    insert_sql = """
    INSERT INTO patients (
        patient_id, full_name, email, cedula, date_of_birth, phone,
        address, medical_history, lab_results, source_scan
    ) VALUES (
        :patient_id, :full_name, :email, :cedula, :date_of_birth::date, :phone,
        :address::jsonb, :medical_history::jsonb, :lab_results::jsonb, :source_scan
    )
    """
    
    parameters = []
    for key, value in patient_data.items():
        if value is None:
            param_value = {'isNull': True}
        elif key == 'date_of_birth' and value is not None:
            param_value = {'stringValue': str(value)}
        else:
            param_value = {'stringValue': str(value) if value is not None else None}
        
        parameters.append({'name': key, 'value': param_value})
    
    rds_data.execute_statement(
        resourceArn=cluster_arn,
        secretArn=secret_arn,
        database=database_name,
        sql=insert_sql,
        parameters=parameters
    )
    
    logger.info(f"Inserted patient: {patient_data['full_name']}")


def update_patient_in_database(rds_data, cluster_arn: str, secret_arn: str, 
                             database_name: str, patient_id: str, patient_data: Dict[str, Any]):
    """Update existing patient with new data including cedula."""
    
    update_sql = """
    UPDATE patients SET
        full_name = :full_name,
        email = :email,
        cedula = :cedula,
        date_of_birth = :date_of_birth::date,
        phone = :phone,
        address = :address::jsonb,
        medical_history = :medical_history::jsonb,
        lab_results = :lab_results::jsonb,
        source_scan = :source_scan,
        updated_at = CURRENT_TIMESTAMP
    WHERE patient_id = :patient_id
    """
    
    parameters = []
    # Add patient_id for WHERE clause
    parameters.append({'name': 'patient_id', 'value': {'stringValue': patient_id}})
    
    # Add all other fields
    for key, value in patient_data.items():
        if key == 'patient_id':
            continue  # Already added above
            
        if value is None:
            param_value = {'isNull': True}
        elif key == 'date_of_birth' and value is not None:
            param_value = {'stringValue': str(value)}
        else:
            param_value = {'stringValue': str(value) if value is not None else None}
        
        parameters.append({'name': key, 'value': param_value})
    
    rds_data.execute_statement(
        resourceArn=cluster_arn,
        secretArn=secret_arn,
        database=database_name,
        sql=update_sql,
        parameters=parameters
    )
    
    logger.info(f"Updated patient: {patient_data['full_name']} (ID: {patient_id})")


def convert_patient_profile_to_db_format(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Convert PatientProfile format to database format (updated for current schema)."""
    
    personal_info = profile.get('personal_info', {})
    
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
    
    # Extract cedula from document number if document type is cedula/ID
    cedula = None
    document_type = personal_info.get('tipo_documento', '').lower()
    document_number = personal_info.get('numero_documento', '')
    
    if document_type in ['cedula', 'cédula', 'id', 'dni', 'cc'] and document_number:
        cedula = document_number
    
    # Build enhanced medical history with additional patient info
    enhanced_medical_history = profile.get('medical_history', {})
    
    # Add demographic info to medical history for context
    if personal_info.get('edad'):
        enhanced_medical_history['age'] = personal_info.get('edad')
    if personal_info.get('sexo'):
        enhanced_medical_history['gender'] = personal_info.get('sexo')
    if document_type and document_number:
        enhanced_medical_history['document'] = {
            'type': document_type,
            'number': document_number
        }
    
    return {
        'patient_id': profile.get('patient_id', str(uuid.uuid4())),
        'full_name': personal_info.get('nombre_completo', ''),
        'email': personal_info.get('email', ''),
        'cedula': cedula,  # New field for national ID
        'phone': personal_info.get('telefono', ''),
        'date_of_birth': date_of_birth,
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
            'full_name': 'Dr. Sarah Wilson',
            'email': 'sarah.wilson@hospital.com',
            'phone': '+1-555-0101',
            'specialization': 'Cardiology',
            'license_number': 'MD-001-2024',
            'department': 'Cardiology'
        },
        {
            'medic_id': str(uuid.uuid4()),
            'full_name': 'Dr. Michael Brown',
            'email': 'michael.brown@hospital.com',
            'phone': '+1-555-0102',
            'specialization': 'Radiology',
            'license_number': 'MD-002-2024',
            'department': 'Radiology'
        },
        {
            'medic_id': str(uuid.uuid4()),
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

            # Insert medic (updated to match current schema)
            insert_sql = """
            INSERT INTO medics (
                medic_id, full_name, email, phone,
                specialization, license_number, department
            ) VALUES (
                :medic_id, :full_name, :email, :phone,
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
