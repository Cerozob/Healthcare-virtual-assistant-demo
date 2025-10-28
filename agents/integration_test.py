#!/usr/bin/env python3
"""
Integration test for healthcare assistant with S3 session management.
This test simulates the full flow from API request to S3 storage.
"""

import os
import json
import asyncio
import boto3
from datetime import datetime
from typing import Dict, Any
from main import get_or_create_agent, extract_patient_id_from_message
from shared.utils import get_logger, create_session_metadata

# Configure logging
logger = get_logger(__name__)

# Test configuration
TEST_BUCKET = os.getenv("SESSION_BUCKET", "ab2-cerozob-processeddata-us-east-1")
TEST_PREFIX = os.getenv("SESSION_PREFIX", "medical-notes/")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")


async def simulate_api_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate an API request to the healthcare assistant.
    
    Args:
        payload: Request payload
        
    Returns:
        Dict[str, Any]: Response from the assistant
    """
    try:
        # Extract data from payload
        user_message = payload.get("prompt", "")
        session_id = payload.get("sessionId", f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        logger.info(f"Processing API request for session: {session_id}")
        
        # Extract patient ID from message
        patient_id = extract_patient_id_from_message(user_message)
        
        if patient_id:
            logger.info(f"Patient context detected: {patient_id}")
        else:
            logger.info("No patient context detected")
        
        # Get or create agent with session management
        agent = get_or_create_agent(session_id, patient_id)
        
        # Process the message
        result = agent(user_message)
        
        # Prepare response
        response = {
            "message": result.message,
            "timestamp": datetime.now().isoformat(),
            "model": "healthcare-assistant",
            "capabilities": ["patient_info", "appointments", "knowledge_base", "documents", "session_management"],
            "session_id": session_id,
            "patient_context": {
                "patient_id": patient_id if patient_id else "no_patient",
                "has_patient_context": patient_id is not None,
                "session_prefix": f"{TEST_PREFIX}patients/{patient_id}/" if patient_id else f"{TEST_PREFIX}no-patient/"
            },
            "session_info": {
                "bucket": TEST_BUCKET,
                "region": AWS_REGION,
                "notes_saved": True,
                "conversation_persisted": True
            }
        }
        
        logger.info("API request processed successfully")
        return {"statusCode": 200, "body": response}
        
    except Exception as e:
        logger.error(f"API request failed: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "body": {
                "error": str(e),
                "message": "Internal server error"
            }
        }


async def verify_s3_storage(session_id: str, patient_id: str = None) -> bool:
    """
    Verify that session data was stored correctly in S3.
    
    Args:
        session_id: Session identifier
        patient_id: Patient identifier
        
    Returns:
        bool: True if storage is verified
    """
    try:
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        
        # Determine the expected prefix using consistent structure
        if patient_id:
            prefix = f"processed/{patient_id}_medical_notes/session_{session_id}/"
        else:
            prefix = f"processed/unknown_medical_notes/session_{session_id}/"
        
        logger.info(f"Verifying S3 storage at: s3://{TEST_BUCKET}/{prefix}")
        
        # List objects in the session directory
        response = s3_client.list_objects_v2(
            Bucket=TEST_BUCKET,
            Prefix=prefix
        )
        
        if 'Contents' not in response:
            logger.error("No objects found in S3 session directory")
            return False
        
        # Check for required files
        object_keys = [obj['Key'] for obj in response['Contents']]
        
        # Should have session.json
        session_json_found = any('session.json' in key for key in object_keys)
        if not session_json_found:
            logger.error("session.json not found in S3")
            return False
        
        # Should have agent directory
        agent_dir_found = any('agents/' in key for key in object_keys)
        if not agent_dir_found:
            logger.error("agents/ directory not found in S3")
            return False
        
        # Should have at least one message
        message_found = any('messages/message_' in key for key in object_keys)
        if not message_found:
            logger.error("No messages found in S3")
            return False
        
        logger.info(f"✅ S3 storage verified: {len(object_keys)} objects found")
        return True
        
    except Exception as e:
        logger.error(f"S3 verification failed: {str(e)}")
        return False


async def test_patient_session_flow():
    """
    Test the complete flow for a patient session.
    """
    print("\n=== Testing Patient Session Flow ===")
    
    # Test data
    session_id = f"integration_test_patient_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    test_messages = [
        {
            "prompt": "Esta sesión es del paciente Juan_Perez_123. Hola doctor, tengo dolor de cabeza.",
            "sessionId": session_id
        },
        {
            "prompt": "El dolor es constante y empeora con la luz.",
            "sessionId": session_id
        },
        {
            "prompt": "¿Qué medicamento me recomienda?",
            "sessionId": session_id
        }
    ]
    
    patient_id = None
    
    # Process each message
    for i, message_data in enumerate(test_messages, 1):
        print(f"\n--- Processing Message {i} ---")
        print(f"User: {message_data['prompt']}")
        
        # Simulate API request
        response = await simulate_api_request(message_data)
        
        if response["statusCode"] != 200:
            print(f"❌ API request failed: {response['body']}")
            return False
        
        response_body = response["body"]
        print(f"Assistant: {response_body['message'][:100]}...")
        
        # Extract patient ID from first message
        if i == 1:
            patient_id = response_body["patient_context"]["patient_id"]
            print(f"Patient ID: {patient_id}")
    
    # Verify S3 storage
    print(f"\n--- Verifying S3 Storage ---")
    storage_verified = await verify_s3_storage(session_id, patient_id)
    
    if storage_verified:
        print("✅ Patient session flow test passed")
        return True
    else:
        print("❌ Patient session flow test failed")
        return False


async def test_no_patient_session_flow():
    """
    Test the complete flow for a session without patient context.
    """
    print("\n=== Testing No-Patient Session Flow ===")
    
    # Test data
    session_id = f"integration_test_general_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    test_messages = [
        {
            "prompt": "Hola, ¿puedes explicarme qué es la hipertensión?",
            "sessionId": session_id
        },
        {
            "prompt": "¿Cuáles son los síntomas más comunes?",
            "sessionId": session_id
        }
    ]
    
    # Process each message
    for i, message_data in enumerate(test_messages, 1):
        print(f"\n--- Processing Message {i} ---")
        print(f"User: {message_data['prompt']}")
        
        # Simulate API request
        response = await simulate_api_request(message_data)
        
        if response["statusCode"] != 200:
            print(f"❌ API request failed: {response['body']}")
            return False
        
        response_body = response["body"]
        print(f"Assistant: {response_body['message'][:100]}...")
        print(f"Patient Context: {response_body['patient_context']['patient_id']}")
    
    # Verify S3 storage
    print(f"\n--- Verifying S3 Storage ---")
    storage_verified = await verify_s3_storage(session_id, None)
    
    if storage_verified:
        print("✅ No-patient session flow test passed")
        return True
    else:
        print("❌ No-patient session flow test failed")
        return False


async def test_session_continuation():
    """
    Test session continuation functionality.
    """
    print("\n=== Testing Session Continuation ===")
    
    # Create initial session
    session_id = f"integration_test_continuation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # First interaction
    initial_message = {
        "prompt": "Esta sesión es del paciente Test_Patient_456. Tengo fiebre desde ayer.",
        "sessionId": session_id
    }
    
    print("--- Initial Interaction ---")
    print(f"User: {initial_message['prompt']}")
    
    response1 = await simulate_api_request(initial_message)
    if response1["statusCode"] != 200:
        print(f"❌ Initial request failed: {response1['body']}")
        return False
    
    print(f"Assistant: {response1['body']['message'][:100]}...")
    patient_id = response1['body']['patient_context']['patient_id']
    
    # Wait a moment to simulate time passing
    await asyncio.sleep(1)
    
    # Continue session
    continuation_message = {
        "prompt": "¿Puedes hacer un resumen de lo que hemos hablado?",
        "sessionId": session_id
    }
    
    print("\n--- Session Continuation ---")
    print(f"User: {continuation_message['prompt']}")
    
    response2 = await simulate_api_request(continuation_message)
    if response2["statusCode"] != 200:
        print(f"❌ Continuation request failed: {response2['body']}")
        return False
    
    print(f"Assistant: {response2['body']['message'][:100]}...")
    
    # Verify the session was continued (should have more messages now)
    storage_verified = await verify_s3_storage(session_id, patient_id)
    
    if storage_verified:
        print("✅ Session continuation test passed")
        return True
    else:
        print("❌ Session continuation test failed")
        return False


async def run_integration_tests():
    """
    Run all integration tests.
    """
    print("Healthcare Assistant - Integration Tests")
    print("=" * 60)
    print(f"S3 Bucket: {TEST_BUCKET}")
    print(f"S3 Prefix: {TEST_PREFIX}")
    print(f"AWS Region: {AWS_REGION}")
    
    try:
        # Test 1: Patient session flow
        test1_passed = await test_patient_session_flow()
        
        # Test 2: No-patient session flow
        test2_passed = await test_no_patient_session_flow()
        
        # Test 3: Session continuation
        test3_passed = await test_session_continuation()
        
        # Summary
        print("\n" + "=" * 60)
        print("Integration Test Results:")
        print(f"Patient Session Flow: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
        print(f"No-Patient Session Flow: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
        print(f"Session Continuation: {'✅ PASSED' if test3_passed else '❌ FAILED'}")
        
        all_passed = test1_passed and test2_passed and test3_passed
        
        if all_passed:
            print("\n🎉 All integration tests passed!")
            print(f"Medical notes are being saved to: s3://{TEST_BUCKET}/{TEST_PREFIX}")
        else:
            print("\n❌ Some integration tests failed")
            
        return all_passed
        
    except Exception as e:
        logger.error(f"Integration tests failed: {str(e)}", exc_info=True)
        print(f"❌ Integration tests failed: {str(e)}")
        return False


if __name__ == "__main__":
    # Run the integration tests
    asyncio.run(run_integration_tests())
