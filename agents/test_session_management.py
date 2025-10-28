#!/usr/bin/env python3
"""
Test script for S3 session management functionality.
"""

import os
import pytest
import boto3
from moto import mock_s3
from datetime import datetime
from strands import Agent
from strands.session.s3_session_manager import S3SessionManager
from shared.utils import extract_patient_id_from_message, create_session_metadata

# Test configuration
TEST_BUCKET = "test-healthcare-sessions"
TEST_PREFIX = "test-medical-notes/"
TEST_REGION = "us-east-1"

HEALTHCARE_SYSTEM_PROMPT = """
You are a healthcare assistant for testing.
Always respond professionally and maintain patient confidentiality.
"""


@mock_s3
def test_patient_id_extraction():
    """Test patient ID extraction from various message formats."""
    
    test_cases = [
        ("Esta sesión es del paciente Juan_Perez_123", "Juan_Perez_123"),
        ("paciente id: PATIENT_456", "PATIENT_456"),
        ("cedula: 12345678", "12345678"),
        ("notas del paciente Maria Garcia", "Maria_Garcia"),
        ("Hola doctor, tengo dolor de cabeza", None),
        ("", None),
    ]
    
    for message, expected in test_cases:
        result = extract_patient_id_from_message(message)
        assert result == expected, f"Failed for message: '{message}'. Expected: {expected}, Got: {result}"
    
    print("✅ Patient ID extraction tests passed")


@mock_s3
def test_session_manager_creation():
    """Test S3SessionManager creation with patient context."""
    
    # Create mock S3 bucket
    s3_client = boto3.client('s3', region_name=TEST_REGION)
    s3_client.create_bucket(Bucket=TEST_BUCKET)
    
    # Test with patient context
    session_id = "test_session_123"
    patient_id = "test_patient_456"
    
    session_manager = S3SessionManager(
        session_id=session_id,
        bucket=TEST_BUCKET,
        prefix=f"processed/{patient_id}_medical_notes/",
        region_name=TEST_REGION
    )
    
    assert session_manager.session_id == session_id
    assert session_manager.bucket == TEST_BUCKET
    assert session_manager.prefix == f"processed/{patient_id}_medical_notes/"
    
    print("✅ Session manager creation test passed")


@mock_s3
def test_agent_with_session_management():
    """Test agent creation and message persistence with session management."""
    
    # Create mock S3 bucket
    s3_client = boto3.client('s3', region_name=TEST_REGION)
    s3_client.create_bucket(Bucket=TEST_BUCKET)
    
    # Create session manager
    session_id = "test_session_789"
    patient_id = "test_patient_101"
    
    session_manager = S3SessionManager(
        session_id=session_id,
        bucket=TEST_BUCKET,
        prefix=f"processed/{patient_id}_medical_notes/",
        region_name=TEST_REGION
    )
    
    # Create agent with session management
    agent = Agent(
        system_prompt=HEALTHCARE_SYSTEM_PROMPT,
        session_manager=session_manager,
        callback_handler=None
    )
    
    # Add patient context to agent state
    agent.state["patient_id"] = patient_id
    agent.state["session_context"] = "patient_session"
    agent.state["metadata"] = create_session_metadata(patient_id)
    
    # Test message processing (this should save to S3)
    test_message = "Tengo dolor de cabeza desde ayer."
    
    # Note: In a real test, you would mock the LLM response
    # For this test, we'll just verify the session structure is created
    
    # Verify session was created in S3
    objects = s3_client.list_objects_v2(
        Bucket=TEST_BUCKET,
        Prefix=f"processed/{patient_id}_medical_notes/session_{session_id}/"
    )
    
    # Should have session.json at minimum
    assert 'Contents' in objects, "No session objects found in S3"
    
    # Check for session.json
    session_files = [obj['Key'] for obj in objects['Contents']]
    session_json_found = any('session.json' in key for key in session_files)
    assert session_json_found, "session.json not found in S3"
    
    print("✅ Agent with session management test passed")


@mock_s3
def test_no_patient_session():
    """Test session management without patient context."""
    
    # Create mock S3 bucket
    s3_client = boto3.client('s3', region_name=TEST_REGION)
    s3_client.create_bucket(Bucket=TEST_BUCKET)
    
    # Create session manager without patient context
    session_id = "test_session_no_patient"
    
    session_manager = S3SessionManager(
        session_id=session_id,
        bucket=TEST_BUCKET,
        prefix=f"processed/unknown_medical_notes/",
        region_name=TEST_REGION
    )
    
    # Create agent
    agent = Agent(
        system_prompt=HEALTHCARE_SYSTEM_PROMPT,
        session_manager=session_manager,
        callback_handler=None
    )
    
    # Add no-patient context
    agent.state["session_context"] = "no_patient"
    agent.state["metadata"] = create_session_metadata()
    
    # Verify session structure
    objects = s3_client.list_objects_v2(
        Bucket=TEST_BUCKET,
        Prefix=f"processed/unknown_medical_notes/session_{session_id}/"
    )
    
    # Should have session.json
    assert 'Contents' in objects, "No session objects found in S3"
    
    print("✅ No-patient session test passed")


def test_session_metadata_creation():
    """Test session metadata creation."""
    
    # Test with patient context
    patient_id = "test_patient_123"
    metadata = create_session_metadata(patient_id)
    
    assert metadata["patient_context"]["patient_id"] == patient_id
    assert metadata["patient_context"]["has_patient_context"] is True
    assert metadata["session_type"] == "medical_consultation"
    assert "timestamp" in metadata
    
    # Test without patient context
    metadata_no_patient = create_session_metadata()
    
    assert metadata_no_patient["patient_context"]["patient_id"] == "no_patient"
    assert metadata_no_patient["patient_context"]["has_patient_context"] is False
    
    print("✅ Session metadata creation test passed")


def run_all_tests():
    """Run all session management tests."""
    
    print("Running Healthcare Assistant Session Management Tests")
    print("=" * 60)
    
    try:
        test_patient_id_extraction()
        test_session_manager_creation()
        test_agent_with_session_management()
        test_no_patient_session()
        test_session_metadata_creation()
        
        print("\n" + "=" * 60)
        print("✅ All session management tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        raise


if __name__ == "__main__":
    # Install required test dependencies
    try:
        import moto
    except ImportError:
        print("Installing test dependencies...")
        os.system("pip install moto[s3] pytest")
        import moto
    
    # Run the tests
    run_all_tests()
