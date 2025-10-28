"""
S3 Error Analysis Lambda Function
Analyzes S3 access logs and CloudTrail logs to identify signature errors and other issues.
"""

import json
import boto3
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
logs_client = boto3.client('logs')

def lambda_handler(event, context):
    """
    Main Lambda handler for S3 error analysis.
    Can be triggered manually or by CloudWatch Events.
    """
    try:
        logger.info("Starting S3 error analysis")
        
        # Get environment variables
        access_logs_bucket = os.environ['ACCESS_LOGS_BUCKET']
        cloudtrail_log_group = os.environ['CLOUDTRAIL_LOG_GROUP']
        raw_bucket_name = os.environ['RAW_BUCKET_NAME']
        processed_bucket_name = os.environ['PROCESSED_BUCKET_NAME']
        
        # Analyze access logs for the last hour
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        results = {
            'analysis_period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'access_log_analysis': analyze_access_logs(access_logs_bucket, start_time, end_time),
            'cloudtrail_analysis': analyze_cloudtrail_logs(cloudtrail_log_group, start_time, end_time),
            'summary': {}
        }
        
        # Generate summary
        results['summary'] = generate_summary(results)
        
        logger.info(f"Error analysis completed: {json.dumps(results, indent=2)}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(results, default=str)
        }
        
    except Exception as e:
        logger.error(f"Error in S3 error analysis: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def analyze_access_logs(bucket_name: str, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
    """
    Analyze S3 access logs for errors and patterns.
    """
    try:
        logger.info(f"Analyzing access logs in bucket: {bucket_name}")
        
        # List objects in the access logs bucket
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix='raw-bucket-access-logs/'
        )
        
        if 'Contents' not in response:
            logger.info("No access logs found")
            return {'status': 'no_logs_found', 'errors': [], 'requests': 0}
        
        errors = []
        total_requests = 0
        signature_errors = 0
        
        # Process each log file
        for obj in response['Contents']:
            if obj['LastModified'] < start_time or obj['LastModified'] > end_time:
                continue
                
            try:
                # Download and parse log file
                log_content = s3_client.get_object(Bucket=bucket_name, Key=obj['Key'])
                log_text = log_content['Body'].read().decode('utf-8')
                
                # Parse S3 access log format
                log_entries = parse_access_log_entries(log_text)
                total_requests += len(log_entries)
                
                # Look for errors
                for entry in log_entries:
                    if entry.get('http_status', '').startswith('4') or entry.get('http_status', '').startswith('5'):
                        errors.append({
                            'timestamp': entry.get('timestamp'),
                            'remote_ip': entry.get('remote_ip'),
                            'operation': entry.get('operation'),
                            'key': entry.get('key'),
                            'http_status': entry.get('http_status'),
                            'error_code': entry.get('error_code'),
                            'request_id': entry.get('request_id'),
                            'user_agent': entry.get('user_agent')
                        })
                        
                        if 'SignatureDoesNotMatch' in entry.get('error_code', ''):
                            signature_errors += 1
                            
            except Exception as e:
                logger.warning(f"Error processing log file {obj['Key']}: {str(e)}")
                continue
        
        return {
            'status': 'analyzed',
            'total_requests': total_requests,
            'total_errors': len(errors),
            'signature_errors': signature_errors,
            'errors': errors[:10],  # Return first 10 errors
            'error_patterns': analyze_error_patterns(errors)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing access logs: {str(e)}")
        return {'status': 'error', 'message': str(e)}

def parse_access_log_entries(log_text: str) -> List[Dict[str, str]]:
    """
    Parse S3 access log entries.
    S3 access log format: https://docs.aws.amazon.com/AmazonS3/latest/userguide/LogFormat.html
    """
    entries = []
    
    for line in log_text.strip().split('\n'):
        if not line.strip():
            continue
            
        # S3 access log regex pattern (simplified)
        # This is a basic parser - in production you might want a more robust one
        parts = line.split(' ')
        if len(parts) >= 10:
            entry = {
                'bucket_owner': parts[0] if parts[0] != '-' else None,
                'bucket': parts[1] if parts[1] != '-' else None,
                'timestamp': parts[2] + ' ' + parts[3] if len(parts) > 3 else None,
                'remote_ip': parts[4] if len(parts) > 4 and parts[4] != '-' else None,
                'requester': parts[5] if len(parts) > 5 and parts[5] != '-' else None,
                'request_id': parts[6] if len(parts) > 6 and parts[6] != '-' else None,
                'operation': parts[7] if len(parts) > 7 and parts[7] != '-' else None,
                'key': parts[8] if len(parts) > 8 and parts[8] != '-' else None,
                'http_status': parts[9] if len(parts) > 9 and parts[9] != '-' else None,
                'error_code': parts[10] if len(parts) > 10 and parts[10] != '-' else None,
                'user_agent': ' '.join(parts[15:]) if len(parts) > 15 else None
            }
            entries.append(entry)
    
    return entries

def analyze_cloudtrail_logs(log_group_name: str, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
    """
    Analyze CloudTrail logs for S3 API errors.
    """
    try:
        logger.info(f"Analyzing CloudTrail logs in log group: {log_group_name}")
        
        # Convert to milliseconds for CloudWatch Logs
        start_time_ms = int(start_time.timestamp() * 1000)
        end_time_ms = int(end_time.timestamp() * 1000)
        
        # Query CloudWatch Logs for errors
        query = '''
        fields @timestamp, eventName, errorCode, errorMessage, sourceIPAddress, userAgent, requestParameters
        | filter eventName like /Put/ or eventName like /Get/ or eventName like /Delete/
        | filter errorCode exists
        | sort @timestamp desc
        | limit 100
        '''
        
        response = logs_client.start_query(
            logGroupName=log_group_name,
            startTime=start_time_ms,
            endTime=end_time_ms,
            queryString=query
        )
        
        query_id = response['queryId']
        
        # Wait for query to complete
        import time
        max_wait = 30  # seconds
        wait_time = 0
        
        while wait_time < max_wait:
            result = logs_client.get_query_results(queryId=query_id)
            if result['status'] == 'Complete':
                break
            time.sleep(1)
            wait_time += 1
        
        if result['status'] != 'Complete':
            return {'status': 'query_timeout', 'errors': []}
        
        # Process results
        errors = []
        signature_errors = 0
        
        for row in result.get('results', []):
            error_entry = {}
            for field in row:
                error_entry[field['field']] = field['value']
            
            errors.append(error_entry)
            
            if 'SignatureDoesNotMatch' in error_entry.get('errorCode', ''):
                signature_errors += 1
        
        return {
            'status': 'analyzed',
            'total_errors': len(errors),
            'signature_errors': signature_errors,
            'errors': errors,
            'query_statistics': result.get('statistics', {})
        }
        
    except Exception as e:
        logger.error(f"Error analyzing CloudTrail logs: {str(e)}")
        return {'status': 'error', 'message': str(e)}

def analyze_error_patterns(errors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze patterns in the errors to identify common issues.
    """
    patterns = {
        'by_error_code': {},
        'by_operation': {},
        'by_user_agent': {},
        'by_ip': {},
        'signature_error_details': []
    }
    
    for error in errors:
        # Count by error code
        error_code = error.get('error_code', 'Unknown')
        patterns['by_error_code'][error_code] = patterns['by_error_code'].get(error_code, 0) + 1
        
        # Count by operation
        operation = error.get('operation', 'Unknown')
        patterns['by_operation'][operation] = patterns['by_operation'].get(operation, 0) + 1
        
        # Count by user agent
        user_agent = error.get('user_agent', 'Unknown')[:50]  # Truncate for readability
        patterns['by_user_agent'][user_agent] = patterns['by_user_agent'].get(user_agent, 0) + 1
        
        # Count by IP
        ip = error.get('remote_ip', 'Unknown')
        patterns['by_ip'][ip] = patterns['by_ip'].get(ip, 0) + 1
        
        # Collect signature error details
        if 'SignatureDoesNotMatch' in error_code:
            patterns['signature_error_details'].append({
                'timestamp': error.get('timestamp'),
                'operation': error.get('operation'),
                'key': error.get('key'),
                'user_agent': error.get('user_agent'),
                'request_id': error.get('request_id')
            })
    
    return patterns

def generate_summary(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a summary of the analysis results.
    """
    access_log_analysis = results.get('access_log_analysis', {})
    cloudtrail_analysis = results.get('cloudtrail_analysis', {})
    
    total_signature_errors = (
        access_log_analysis.get('signature_errors', 0) + 
        cloudtrail_analysis.get('signature_errors', 0)
    )
    
    total_errors = (
        access_log_analysis.get('total_errors', 0) + 
        cloudtrail_analysis.get('total_errors', 0)
    )
    
    summary = {
        'total_signature_errors': total_signature_errors,
        'total_errors': total_errors,
        'total_requests': access_log_analysis.get('total_requests', 0),
        'error_rate': (total_errors / max(access_log_analysis.get('total_requests', 1), 1)) * 100,
        'signature_error_rate': (total_signature_errors / max(total_errors, 1)) * 100 if total_errors > 0 else 0,
        'recommendations': []
    }
    
    # Generate recommendations
    if total_signature_errors > 0:
        summary['recommendations'].append(
            "SignatureDoesNotMatch errors detected. Check AWS credentials, clock synchronization, and request signing process."
        )
    
    if summary['error_rate'] > 10:
        summary['recommendations'].append(
            f"High error rate detected ({summary['error_rate']:.1f}%). Review application logic and error handling."
        )
    
    return summary
