#!/usr/bin/env python3
"""
Test the exact agent creation as in main.py.
"""

import os
import sys
import traceback

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables
os.environ["SESSION_BUCKET"] = "test-bucket"
os.environ["AWS_REGION"] = "us-east-1"
os.environ["LOG_LEVEL"] = "INFO"

def test_exact_agent():
    """Test creating the exact agent as in main.py."""
    try:
        print("Step 1: Import modules...")
        from strands import Agent
        from shared.utils import get_logger, extract_patient_context, extract_patient_id_from_message
        print("✅ Modules imported successfully")
        
        print("Step 2: Initialize logger...")
        logger = get_logger(__name__)
        print("✅ Logger initialized")
        
        print("Step 3: Define system prompt...")
        HEALTHCARE_SYSTEM_PROMPT = """
You are a healthcare assistant designed to help medical professionals with:
- Patient information management
- Appointment scheduling
- Medical knowledge base queries
- Document processing and analysis

Always respond in Spanish (LATAM) unless specifically requested otherwise.
Maintain professional medical standards and patient confidentiality.
Be helpful, accurate, and professional in all interactions.

When saving notes or information about patients, always include the patient context in your responses.
"""
        print("✅ System prompt defined")
        
        print("Step 4: Create agent with exact parameters...")
        agent = Agent(
            system_prompt=HEALTHCARE_SYSTEM_PROMPT,
            callback_handler=None  # Prevent streaming output pollution
        )
        print("✅ Agent created successfully")
        
        print("Step 5: Set state...")
        agent.state.set("session_context", "no_patient")
        print("✅ State set successfully")
        
        print("Step 6: Test agent call...")
        result = agent("Hello, this is a test")
        print("✅ Agent call successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_exact_agent()
