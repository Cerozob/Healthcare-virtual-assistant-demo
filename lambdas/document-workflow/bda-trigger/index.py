"""
Simplified BDA Trigger Lambda.
Directly invokes Bedrock Data Automation when documents are uploaded to S3.
"""

import json
import logging
import os
from typing import Any, Dict
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Simple BDA trigger that directly calls invoke_data_automation_async
    """
    try:
        # Extract S3 details from event
        bucket, key = extract_s3_details(event)
        
        # Call BDA API directly
        invocation_arn = invoke_bda_processing(bucket, key)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'invocationArn': invocation_arn,
                'status': 'submitted'
            })
        }
    except Exception as e:
        logger.error(f"BDA trigger failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def extract_s3_details(event: Dict[str, Any]) -> tuple[str, str]:
    """
    Extract bucket and key from S3 event (supports both direct S3 and EventBridge)
    """
    # Handle EventBridge S3 events
    if event.get('source') == 'aws.s3':
        detail = event['detail']
        bucket = detail['bucket']['name']
        key = detail['object']['key']
        return bucket, key
    
    # Handle direct S3 notifications
    record = event['Records'][0]
    bucket = record['s3']['bucket']['name']
    key = record['s3']['object']['key']
    return bucket, key

def invoke_bda_processing(bucket: str, key: str) -> str:
    """
    Directly invoke BDA with multiple blueprints
    """
    client = boto3.client('bedrock-data-automation-runtime')
    
    response = client.invoke_data_automation_async(
        inputConfiguration={
            's3Uri': f's3://{bucket}/{key}'
        },
        outputConfiguration={
            's3Uri': f's3://{os.environ["PROCESSED_BUCKET_NAME"]}/processed/{key}'
        },
        dataAutomationConfiguration={
            'dataAutomationProjectArn': os.environ['BDA_PROJECT_ARN'],
            'stage': 'DEVELOPMENT'
        },
        blueprints=[
            {'blueprintArn': os.environ['MEDICAL_RECORD_BLUEPRINT_ARN']},
            {'blueprintArn': os.environ['MEDICAL_IMAGE_BLUEPRINT_ARN']},
            {'blueprintArn': os.environ['MEDICAL_AUDIO_BLUEPRINT_ARN']},
            {'blueprintArn': os.environ['MEDICAL_VIDEO_BLUEPRINT_ARN']}
        ],
        dataAutomationProfileArn=os.environ['BDA_PROFILE_ARN'],

        notificationConfiguration={
            'eventBridgeConfiguration': {
                'eventBridgeEnabled': True
            }
        }
    )
    
    return response['invocationArn']
