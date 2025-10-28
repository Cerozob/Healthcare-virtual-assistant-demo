#!/usr/bin/env python3
"""
Basic functionality test for the healthcare agent.
"""

import os
import sys
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required imports work."""
    try:
        print("Testing imports...")
        
        # Test FastAPI
        from fastapi import FastAPI
        print("✅ FastAPI import successful")
        
        # Test Strands Agents
        from strands import Agent
        print("✅ Strands Agent import successful")
        
        # Test S3 Session Manager
        from strands.session.s3_session_manager import S3SessionManager
        print("✅ S3SessionManager import successful")
        
        # Test AWS SDK
        import boto3
        print("✅ boto3 import successful")
        
        # Test shared utils
        from shared.utils import get_logger
        print("✅ Shared utils import successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during imports: {str(e)}")
        return False


def test_basic_agent_creation():
    """Test basic agent creation without S3 dependencies."""
    try:
        print("\nTesting basic agent creation...")
        
        from strands import Agent
        
        # Create a simple agent without session manager
        agent = Agent(
            system_prompt="You are a test agent.",
            callback_handler=None
        )
        
        print("✅ Basic agent creation successful")
        return True
        
    except Exception as e:
        print(f"❌ Agent creation failed: {str(e)}")
        return False


def test_fastapi_app_creation():
    """Test FastAPI app creation."""
    try:
        print("\nTesting FastAPI app creation...")
        
        from fastapi import FastAPI
        
        app = FastAPI(title="Test App")
        
        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}
        
        print("✅ FastAPI app creation successful")
        return True
        
    except Exception as e:
        print(f"❌ FastAPI app creation failed: {str(e)}")
        return False


def test_environment_variables():
    """Test environment variable access."""
    try:
        print("\nTesting environment variables...")
        
        # Test required environment variables
        s3_bucket = os.getenv("SESSION_BUCKET", "default-bucket")
        aws_region = os.getenv("AWS_REGION", "us-east-1")
        log_level = os.getenv("LOG_LEVEL", "INFO")
        
        print(f"  S3_BUCKET: {s3_bucket}")
        print(f"  AWS_REGION: {aws_region}")
        print(f"  LOG_LEVEL: {log_level}")
        
        print("✅ Environment variables accessible")
        return True
        
    except Exception as e:
        print(f"❌ Environment variable test failed: {str(e)}")
        return False


def main():
    """Run all basic functionality tests."""
    print("🔍 Testing Basic Functionality")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_basic_agent_creation,
        test_fastapi_app_creation,
        test_environment_variables
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {str(e)}")
            results.append(False)
    
    print("\n" + "=" * 50)
    if all(results):
        print("✅ All basic functionality tests passed!")
        return 0
    else:
        print("❌ Some basic functionality tests failed.")
        return 1


if __name__ == "__main__":
    exit(main())
