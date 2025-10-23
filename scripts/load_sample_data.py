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
import time
import argparse
from pathlib import Path
from typing import Dict, Any, List


def get_data_loader_function_name() -> str:
    """Get the data loader function name from CloudFormation outputs."""
    try:
        cf = boto3.client('cloudformation')
        
        # Try to find the backend stack
        stacks = cf.list_stacks(StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE'])
        backend_stack_name = None
        
        for stack in stacks['StackSummaries']:
            if 'backend' in stack['StackName'].lower() or 'healthcare' in stack['StackName'].lower():
                backend_stack_name = stack['StackName']
                break
        
        if not backend_stack_name:
            raise Exception("Could not find backend stack")
        
        # Get stack outputs
        response = cf.describe_stacks(StackName=backend_stack_name)
        stack = response['Stacks'][0]
        
        for output in stack.get('Outputs', []):
            if output['OutputKey'] == 'DataLoaderFunctionName':
                return output['OutputValue']
        
        raise Exception("DataLoaderFunctionName output not found in stack")
        
    except Exception as e:
        print(f"Error getting function name from CloudFormation: {e}")
        print("Trying fallback function name...")
        return "healthcare-data-loader"  # Fallback


def invoke_data_loader(function_name: str) -> Dict[str, Any]:
    """Invoke the data loader Lambda function."""
    lambda_client = boto3.client('lambda')
    
    print(f"Invoking data loader function: {function_name}")
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',  # Synchronous invocation
            Payload=json.dumps({})
        )
        
        # Parse response
        payload = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            print("✅ Data loading completed successfully!")
            
            if 'body' in payload:
                body = json.loads(payload['body'])
                if 'patients_loaded' in body:
                    print(f"📊 Patients loaded: {body['patients_loaded']}")
            
            return payload
        else:
            print(f"❌ Function returned error status: {response['StatusCode']}")
            print(f"Response: {payload}")
            return payload
            
    except Exception as e:
        print(f"❌ Error invoking function: {e}")
        return {'error': str(e)}


def get_raw_bucket_name() -> str:
    """Get the raw bucket name from SSM parameter."""
    try:
        ssm = boto3.client('ssm')
        response = ssm.get_parameter(Name='/healthcare/document-workflow/raw-bucket')
        return response['Parameter']['Value']
    except Exception as e:
        print(f"Could not get raw bucket from SSM: {e}")
        # Fallback to default naming convention
        region = boto3.Session().region_name
        return f"ab2-cerozob-rawdata-{region}"


def find_sample_documents() -> List[Dict[str, str]]:
    """Find all sample documents in the local directory."""
    sample_dir = Path("apps/SampleFileGeneration/output")
    
    if not sample_dir.exists():
        print(f"⚠️  Sample data directory not found: {sample_dir}")
        return []
    
    documents = []
    
    # Find all PDF and image files
    for patient_dir in sample_dir.iterdir():
        if patient_dir.is_dir() and patient_dir.name != '.intermediate':
            patient_id = patient_dir.name
            
            for file_path in patient_dir.iterdir():
                if file_path.is_file():
                    filename = file_path.name
                    
                    # Skip profile JSON files (handled by Lambda)
                    if filename.endswith('_profile.json'):
                        continue
                    
                    # Include PDFs and images
                    if filename.endswith(('.pdf', '.png', '.jpg', '.jpeg')):
                        documents.append({
                            'local_path': str(file_path),
                            'patient_id': patient_id,
                            'filename': filename,
                            's3_key': f"patients/{patient_id}/{filename}"
                        })
    
    return documents


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
            print(f"❌ [{i}/{len(documents)}] Failed to upload {doc['filename']}: {e}")
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
    
    # Check if sample data bucket exists
    try:
        s3 = boto3.client('s3')
        region = boto3.Session().region_name
        bucket_name = f"ab2-cerozob-sampledata-{region}"
        
        s3.head_bucket(Bucket=bucket_name)
        print(f"✅ Sample data bucket found: {bucket_name}")
    except Exception as e:
        print(f"❌ Sample data bucket not accessible: {e}")
        return False
    
    # Check if raw bucket exists
    try:
        raw_bucket = get_raw_bucket_name()
        s3.head_bucket(Bucket=raw_bucket)
        print(f"✅ Raw bucket accessible: {raw_bucket}")
    except Exception as e:
        print(f"❌ Raw bucket not accessible: {e}")
        print("   Please ensure the document workflow stack has been deployed.")
        return False
    
    # Check if sample documents exist
    documents = find_sample_documents()
    if documents:
        print(f"✅ Found {len(documents)} sample documents to upload")
    else:
        print("⚠️  No sample documents found (this is optional)")
    
    return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Load sample healthcare data and documents')
    parser.add_argument('--skip-documents', action='store_true', 
                       help='Skip document upload (only load database data)')
    parser.add_argument('--documents-only', action='store_true',
                       help='Only upload documents (skip database loading)')
    args = parser.parse_args()
    
    print("🚀 Healthcare Sample Data & Document Loader")
    print("=" * 55)
    
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please ensure:")
        print("1. AWS credentials are configured")
        print("2. The backend and document workflow stacks are deployed")
        print("3. You're running this from the project root directory")
        sys.exit(1)
    
    # Step 1: Load patient data via Lambda (unless documents-only)
    if not args.documents_only:
        print("\n📊 Step 1: Loading patient data into database...")
        
        try:
            function_name = get_data_loader_function_name()
            print(f"📋 Found data loader function: {function_name}")
        except Exception as e:
            print(f"❌ Could not find data loader function: {e}")
            sys.exit(1)
        
        # Invoke the Lambda function
        result = invoke_data_loader(function_name)
        
        if 'error' in result:
            print(f"\n❌ Data loading failed: {result['error']}")
            sys.exit(1)
        
        print("✅ Patient data loaded successfully!")
    
    # Step 2: Upload documents to raw bucket (unless skip-documents)
    if not args.skip_documents:
        print("\n📄 Step 2: Uploading sample documents...")
        
        documents = find_sample_documents()
        if not documents:
            print("⚠️  No sample documents found to upload")
            print("   This is optional - you can upload documents manually later")
        else:
            try:
                raw_bucket = get_raw_bucket_name()
                uploaded_count = upload_documents_to_s3(raw_bucket, documents)
                
                if uploaded_count > 0:
                    print(f"✅ Successfully uploaded {uploaded_count}/{len(documents)} documents")
                else:
                    print("❌ No documents were uploaded successfully")
                    
            except Exception as e:
                print(f"❌ Document upload failed: {e}")
                print("   You can upload documents manually using the upload script")
    else:
        print("\n📄 Step 2: Skipping document upload (--skip-documents flag)")
        documents = []
    
    print("\n🎉 Sample data loading completed!")
    print("\n📋 Summary:")
    if not args.documents_only:
        print("✅ Patient profiles loaded into database")
        print("✅ Sample medics and exams loaded")
    if not args.skip_documents and documents:
        print("✅ Sample documents uploaded to raw bucket")
        print("🔄 Document workflow will automatically process uploaded files")
    
    print("\n🚀 Next steps:")
    if not args.documents_only:
        print("1. Check the database for loaded patient data")
        print("2. Test the API endpoints with the sample data")
        print("3. Use the frontend to interact with the loaded data")
    if not args.skip_documents and documents:
        print("4. Monitor document processing in CloudWatch logs")
        print("5. Check the processed bucket for extracted document data")
    
    if args.skip_documents:
        print("\n💡 To upload documents later, run:")
        print("   python scripts/load_sample_data.py --documents-only")


if __name__ == "__main__":
    main()
