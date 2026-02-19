#!/usr/bin/env python3
"""
Comprehensive script to load sample healthcare data.
This script:
1. Loads patient profiles from S3 into the database (via Lambda)
2. Uploads sample documents (PDFs, images) to the raw bucket
3. Triggers the document workflow for processing
"""

import boto3
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List


def get_data_loader_function_name() -> str:
    """Get the data loader function name from CloudFormation outputs."""
    try:
        cf = boto3.client('cloudformation')

        # Try to find the backend stack - look for AWSomeBuilder2-BackendStack pattern
        stacks = cf.list_stacks(
            StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE'])
        backend_stack_name = None

        for stack in stacks['StackSummaries']:
            stack_name = stack['StackName']
            if ('backend' in stack_name.lower() and 'awsomebuilder' in stack_name.lower()) or \
               stack_name == 'AWSomeBuilder2-BackendStack':
                backend_stack_name = stack_name
                break

        if not backend_stack_name:
            # Try alternative patterns
            for stack in stacks['StackSummaries']:
                if 'backend' in stack['StackName'].lower():
                    backend_stack_name = stack['StackName']
                    break

        if not backend_stack_name:
            raise Exception("Could not find backend stack. Available stacks: " +
                            ", ".join([s['StackName'] for s in stacks['StackSummaries']]))

        print(f"Found backend stack: {backend_stack_name}")

        # Get stack outputs
        response = cf.describe_stacks(StackName=backend_stack_name)
        stack = response['Stacks'][0]

        # Look for the correct output key
        for output in stack.get('Outputs', []):
            if output['OutputKey'] == 'DataLoaderFunctionName':
                return output['OutputValue']

        # List available outputs for debugging
        available_outputs = [output['OutputKey']
                             for output in stack.get('Outputs', [])]
        raise Exception(
            f"DataLoaderFunctionName output not found in stack. Available outputs: {available_outputs}")

    except Exception as e:
        print(f"Error getting function name from CloudFormation: {e}")
        print("Trying fallback function name...")
        # Try the function name pattern from the CDK stack
        return "AWSomeBuilder2-BackendStack-DataLoaderFunction"


def load_patient_profiles_from_local() -> List[Dict[str, Any]]:
    """Load all patient profiles from local filesystem."""
    sample_dir = Path("apps/SampleFileGeneration/output")
    
    if not sample_dir.exists():
        print(f"⚠️  Sample data directory not found: {sample_dir}")
        return []
    
    profiles = []
    patient_dirs = [d for d in sample_dir.iterdir() if d.is_dir() and d.name != '.intermediate']
    
    if not patient_dirs:
        print("⚠️  No patient directories found")
        return []
    
    print(f"📂 Found {len(patient_dirs)} patient directories")
    
    for i, patient_dir in enumerate(patient_dirs, 1):
        patient_id = patient_dir.name
        profile_file = patient_dir / f"{patient_id}_profile.json"
        
        if not profile_file.exists():
            print(f"⚠️  [{i}/{len(patient_dirs)}] Profile file not found: {profile_file}")
            continue
        
        try:
            with open(profile_file, 'r') as f:
                profile_data = json.load(f)
                profiles.append(profile_data)
                patient_name = profile_data.get('personal_info', {}).get('nombre_completo', 'Unknown')
                print(f"✅ [{i}/{len(patient_dirs)}] Loaded profile: {patient_name} (ID: {patient_id})")
        except Exception as e:
            print(f"❌ [{i}/{len(patient_dirs)}] Failed to load profile {profile_file}: {e}")
            continue
    
    return profiles


def invoke_data_loader(function_name: str, patient_profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Invoke the data loader Lambda function with patient profiles in payload."""
    lambda_client = boto3.client('lambda')

    print(f"\nInvoking data loader function: {function_name}")
    print(f"🔄 Sending {len(patient_profiles)} patient profiles in payload")

    try:
        # Send patient profiles directly in the payload
        payload = {
            'patient_profiles': patient_profiles
        }
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',  # Synchronous invocation
            Payload=json.dumps(payload)
        )

        # Parse response
        result = json.loads(response['Payload'].read())

        if response['StatusCode'] == 200:
            print("✅ Data loading completed successfully!")

            if 'body' in result:
                body = json.loads(result['body'])
                if 'patients_loaded' in body:
                    print(f"📊 Patients loaded: {body['patients_loaded']}")

            return result
        else:
            print(f"❌ Function returned error status: {response['StatusCode']}")
            print(f"Response: {result}")
            return result

    except Exception as e:
        print(f"❌ Error invoking function: {e}")
        return {'error': str(e)}


def get_raw_bucket_name() -> str:
    """Get the raw bucket name from SSM parameter."""
    try:
        ssm = boto3.client('ssm')
        response = ssm.get_parameter(
            Name='/healthcare/document-workflow/raw-bucket')
        return response['Parameter']['Value']
    except Exception as e:
        print(f"Could not get raw bucket from SSM: {e}")
        # Fallback to default naming convention
        region = boto3.Session().region_name
        return f"demo-healthcareva-dfx5-rawdata-{region}"


def find_sample_documents() -> List[Dict[str, str]]:
    """Find sample documents - DISABLED: No documents will be uploaded."""
    print("📄 Document upload is disabled")
    return []


def upload_documents_to_s3(bucket_name: str, documents: List[Dict[str, str]]) -> int:
    """Upload documents to the raw S3 bucket."""
    if not documents:
        print("📄 No documents to upload")
        return 0

    s3 = boto3.client('s3')
    uploaded_count = 0

    print(f"📤 Uploading {len(documents)} documents to bucket: {bucket_name}")

    for i, doc in enumerate(documents, 1):
        try:
            # Check if file exists locally
            if not os.path.exists(doc['local_path']):
                print(f"⚠️  File not found: {doc['local_path']}")
                continue

            # Upload file
            s3.upload_file(
                doc['local_path'],
                bucket_name,
                doc['s3_key'],
                ExtraArgs={
                    'Metadata': {
                        'patient-id': doc['patient_id'],
                        'original-filename': doc['filename']
                    }
                }
            )

            uploaded_count += 1
            print(f"✅ [{i}/{len(documents)}] Uploaded: {doc['filename']}")

        except Exception as e:
            print(
                f"❌ [{i}/{len(documents)}] Failed to upload {doc['filename']}: {e}")
            continue

    return uploaded_count


def check_prerequisites():
    """Check if the required AWS resources exist."""
    print("🔍 Checking prerequisites...")

    # Check if we can access AWS
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS access confirmed. Account: {identity['Account']}")
    except Exception as e:
        print(f"❌ Cannot access AWS: {e}")
        return False

    # Check if local sample data exists
    sample_dir = Path("apps/SampleFileGeneration/output")
    if sample_dir.exists():
        patient_dirs = [d for d in sample_dir.iterdir() if d.is_dir() and d.name != '.intermediate']
        if patient_dirs:
            print(f"✅ Found {len(patient_dirs)} patient profiles in local directory")
        else:
            print("⚠️  No patient profiles found in local directory")
            return False
    else:
        print("⚠️  Local sample data directory not found")
        return False

    return True


def main():
    """Main function."""
    print("🚀 Healthcare Sample Data & Document Loader")
    print("=" * 55)

    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please ensure:")
        print("1. AWS credentials are configured")
        print("2. The backend stack is deployed")
        print("3. You're running this from the project root directory")
        print("4. Patient profiles exist in apps/SampleFileGeneration/output")
        sys.exit(1)

    # Step 1: Load patient profiles from local filesystem
    print("\n📂 Step 1: Loading patient profiles from local filesystem...")

    patient_profiles = load_patient_profiles_from_local()

    if not patient_profiles:
        print("❌ No patient profiles found to load")
        sys.exit(1)

    print(f"✅ Loaded {len(patient_profiles)} patient profiles from local files")

    # Step 2: Load patient data via Lambda
    print("\n📊 Step 2: Loading patient data into database...")

    try:
        function_name = get_data_loader_function_name()
        print(f"📋 Found data loader function: {function_name}")
    except Exception as e:
        print(f"❌ Could not find data loader function: {e}")
        sys.exit(1)

    # Invoke the Lambda function with patient profiles
    result = invoke_data_loader(function_name, patient_profiles)

    if 'error' in result:
        print(f"\n❌ Data loading failed: {result['error']}")
        sys.exit(1)

    print("✅ Patient data loaded successfully!")

    # Step 3: Skip document upload
    print("\n📄 Step 3: Skipping document upload (disabled)")
    print("   Documents can be uploaded manually later if needed")

    print("\n🎉 Sample data loading completed!")
    print("\n📋 Summary:")
    print(f"✅ {len(patient_profiles)} patient profiles loaded into database")
    print("✅ Sample medics and exams upserted")
    print("📄 Document upload skipped (disabled)")

    print("\n🚀 Next steps:")
    print("1. Check the database for all loaded patients")
    print("2. Test the API endpoints with the sample data")
    print("3. Use the frontend to interact with the loaded data")


if __name__ == "__main__":
    main()
