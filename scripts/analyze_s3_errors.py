#!/usr/bin/env python3
"""
Script to analyze S3 errors using the deployed Lambda function.
"""

import boto3
import json
import sys
from datetime import datetime

def main():
    """
    Invoke the S3 error analysis Lambda function and display results.
    """
    try:
        # Initialize Lambda client
        lambda_client = boto3.client('lambda')
        
        # Function name from the CDK stack
        function_name = 'healthcare-s3-error-analysis'
        
        print(f"Invoking S3 error analysis function: {function_name}")
        print("=" * 60)
        
        # Invoke the Lambda function
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'source': 'manual_analysis',
                'timestamp': datetime.utcnow().isoformat()
            })
        )
        
        # Parse the response
        payload = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            print("✅ Analysis completed successfully!")
            print()
            
            # Parse the body if it's a string
            if isinstance(payload.get('body'), str):
                results = json.loads(payload['body'])
            else:
                results = payload.get('body', payload)
            
            # Display summary
            summary = results.get('summary', {})
            print("📊 SUMMARY:")
            print(f"   Total Signature Errors: {summary.get('total_signature_errors', 0)}")
            print(f"   Total Errors: {summary.get('total_errors', 0)}")
            print(f"   Total Requests: {summary.get('total_requests', 0)}")
            print(f"   Error Rate: {summary.get('error_rate', 0):.2f}%")
            print(f"   Signature Error Rate: {summary.get('signature_error_rate', 0):.2f}%")
            print()
            
            # Display recommendations
            recommendations = summary.get('recommendations', [])
            if recommendations:
                print("💡 RECOMMENDATIONS:")
                for i, rec in enumerate(recommendations, 1):
                    print(f"   {i}. {rec}")
                print()
            
            # Display access log analysis
            access_analysis = results.get('access_log_analysis', {})
            if access_analysis.get('status') == 'analyzed':
                print("📋 ACCESS LOG ANALYSIS:")
                print(f"   Status: {access_analysis.get('status')}")
                print(f"   Total Requests: {access_analysis.get('total_requests', 0)}")
                print(f"   Total Errors: {access_analysis.get('total_errors', 0)}")
                print(f"   Signature Errors: {access_analysis.get('signature_errors', 0)}")
                
                # Show recent errors
                errors = access_analysis.get('errors', [])
                if errors:
                    print(f"   Recent Errors ({len(errors)} shown):")
                    for error in errors[:5]:  # Show first 5
                        print(f"     - {error.get('timestamp', 'N/A')} | "
                              f"{error.get('http_status', 'N/A')} | "
                              f"{error.get('error_code', 'N/A')} | "
                              f"{error.get('operation', 'N/A')}")
                print()
            
            # Display CloudTrail analysis
            cloudtrail_analysis = results.get('cloudtrail_analysis', {})
            if cloudtrail_analysis.get('status') == 'analyzed':
                print("☁️ CLOUDTRAIL ANALYSIS:")
                print(f"   Status: {cloudtrail_analysis.get('status')}")
                print(f"   Total Errors: {cloudtrail_analysis.get('total_errors', 0)}")
                print(f"   Signature Errors: {cloudtrail_analysis.get('signature_errors', 0)}")
                
                # Show recent errors
                errors = cloudtrail_analysis.get('errors', [])
                if errors:
                    print(f"   Recent Errors ({len(errors)} shown):")
                    for error in errors[:5]:  # Show first 5
                        print(f"     - {error.get('@timestamp', 'N/A')} | "
                              f"{error.get('eventName', 'N/A')} | "
                              f"{error.get('errorCode', 'N/A')}")
                print()
            
            # Display full results if verbose
            if len(sys.argv) > 1 and sys.argv[1] == '--verbose':
                print("🔍 FULL RESULTS:")
                print(json.dumps(results, indent=2, default=str))
        
        else:
            print(f"❌ Analysis failed with status code: {response['StatusCode']}")
            print(f"Error: {payload}")
            
    except Exception as e:
        print(f"❌ Error running S3 error analysis: {str(e)}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
