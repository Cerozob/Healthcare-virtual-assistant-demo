#!/usr/bin/env python3
"""
Test the exact FastAPI flow to isolate the issue.
"""

import os
import sys
import traceback
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_fastapi_flow():
    """Test the exact flow that happens in the FastAPI endpoint."""
    try:
        print("Step 1: Set environment variables...")
        os.environ["SESSION_BUCKET"] = "test-bucket"
        os.environ["AWS_REGION"] = "us-east-1"
        os.environ["LOG_LEVEL"] = "INFO"
        print("✅ Environment variables set")
        
        print("Step 2: Import required modules...")
        from strands import Agent
        from shared.utils import get_logger, extract_patient_context
        print("✅ Modules imported successfully")
        
        print("Step 3: Initialize logger...")
        logger = get_logger(__name__)
        print("✅ Logger initialized")
        
        print("Step 4: Simulate request data...")
        user_message = "Hello, this is a test message"
        session_id = f"healthcare_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"✅ Request data: message='{user_message}', session_id='{session_id}'")
        
        print("Step 5: Extract patient ID...")
        # Simulate the extract_patient_id_from_message function
        patient_id = None  # No patient ID in test message
        print(f"✅ Patient ID extracted: {patient_id}")
        
        print("Step 6: Create agent...")
        agent = Agent(
            system_prompt="You are a healthcare assistant.",
            callback_handler=None
        )
        print("✅ Agent created successfully")
        
        print("Step 7: Set agent state...")
        if patient_id:
            agent.state.set("patient_id", patient_id)
            agent.state.set("session_context", "patient_session")
            print(f"Agent initialized with patient context: {patient_id}")
        else:
            agent.state.set("session_context", "no_patient")
            print("Agent initialized without patient context")
        print("✅ Agent state set successfully")
        
        print("Step 8: Process message with agent...")
        result = agent(user_message)
        print("✅ Agent processing successful")
        
        print("Step 9: Prepare response...")
        response = {
            "message": result.message,
            "timestamp": datetime.now().isoformat(),
            "model": "healthcare-assistant",
            "capabilities": ["patient_info", "appointments", "knowledge_base", "documents"],
            "session_id": session_id,
            "patient_context": {
                "patient_id": patient_id if patient_id else "unknown",
                "has_patient_context": patient_id is not None,
            }
        }
        print("✅ Response prepared successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_fastapi_flow()
