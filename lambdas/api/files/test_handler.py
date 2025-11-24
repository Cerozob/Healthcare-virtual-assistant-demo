"""
Test script for files Lambda handler to verify request format handling.
Run with: python -m pytest lambdas/api/files/test_handler.py -v
"""

import json
import sys
sys.path.append('lambdas')

from api.files.handler import lambda_handler


def test_agentcore_direct_event():
    """Test AgentCore Gateway direct event format."""
    event = {
        "action": "list",
        "patient_id": "test-patient-123",
        "file_type": "medical-history"
    }
    
    result = lambda_handler(event, None)
    
    assert result['statusCode'] == 200
    print("✅ AgentCore direct event format works")


def test_agentcore_body_wrapped():
    """Test AgentCore Gateway body-wrapped format."""
    event = {
        "body": json.dumps({
            "action": "list",
            "patient_id": "test-patient-123"
        })
    }
    
    result = lambda_handler(event, None)
    
    assert result['statusCode'] == 200
    print("✅ AgentCore body-wrapped format works")


def test_http_api_gateway():
    """Test HTTP API Gateway format."""
    event = {
        "httpMethod": "GET",
        "path": "/files",
        "queryStringParameters": {
            "patient_id": "test-patient-123"
        }
    }
    
    result = lambda_handler(event, None)
    
    assert result['statusCode'] == 200
    print("✅ HTTP API Gateway format works")


def test_invalid_request():
    """Test invalid request format."""
    event = {
        "invalid": "request"
    }
    
    result = lambda_handler(event, None)
    
    assert result['statusCode'] == 400
    assert 'Invalid request format' in json.loads(result['body'])['error']
    print("✅ Invalid request handling works")


if __name__ == "__main__":
    print("Testing files Lambda handler request formats...\n")
    
    try:
        test_agentcore_direct_event()
        test_agentcore_body_wrapped()
        test_http_api_gateway()
        test_invalid_request()
        
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
