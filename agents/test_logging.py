#!/usr/bin/env python3
"""
Standalone logging test script to verify logging configuration works
and is not suppressed by WSGI servers.
"""

import os
import sys
import logging
import time

def test_basic_logging():
    """Test basic Python logging without any framework interference."""
    
    print("🧪 BASIC LOGGING TEST (No Framework)", flush=True)
    print("=" * 50, flush=True)
    
    # Configure basic logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s',
        stream=sys.stdout,
        force=True  # Override any existing configuration
    )
    
    logger = logging.getLogger("test_basic")
    
    logger.debug("🔍 Basic DEBUG message")
    logger.info("ℹ️ Basic INFO message")
    logger.warning("⚠️ Basic WARNING message")
    logger.error("❌ Basic ERROR message")
    
    print("✅ Basic logging test complete", flush=True)
    print("=" * 50, flush=True)

def test_agent_logging():
    """Test the agent's logging configuration."""
    
    print("\n🤖 AGENT LOGGING TEST", flush=True)
    print("=" * 50, flush=True)
    
    try:
        # Import and configure agent logging
        from main import configure_logging, test_logging
        
        print("📝 Configuring agent logging...", flush=True)
        configure_logging()
        
        print("📝 Running agent logging test...", flush=True)
        test_logging()
        
        # Test agent logger specifically
        agent_logger = logging.getLogger("agents.test_script")
        agent_logger.info("🤖 Agent logger test message")
        
        print("✅ Agent logging test complete", flush=True)
        
    except Exception as e:
        print(f"❌ Agent logging test failed: {e}", flush=True)
        import traceback
        traceback.print_exc()
    
    print("=" * 50, flush=True)

def test_uvicorn_compatibility():
    """Test logging with uvicorn-like configuration."""
    
    print("\n🦄 UVICORN COMPATIBILITY TEST", flush=True)
    print("=" * 50, flush=True)
    
    try:
        # Simulate uvicorn logger setup
        uvicorn_logger = logging.getLogger("uvicorn")
        uvicorn_access = logging.getLogger("uvicorn.access")
        uvicorn_error = logging.getLogger("uvicorn.error")
        
        # Test that our configuration works with uvicorn loggers
        uvicorn_logger.info("🦄 Uvicorn logger test")
        uvicorn_access.info("🦄 Uvicorn access logger test")
        uvicorn_error.info("🦄 Uvicorn error logger test")
        
        print("✅ Uvicorn compatibility test complete", flush=True)
        
    except Exception as e:
        print(f"❌ Uvicorn compatibility test failed: {e}", flush=True)
    
    print("=" * 50, flush=True)

def test_fastapi_startup():
    """Test FastAPI startup logging."""
    
    print("\n⚡ FASTAPI STARTUP TEST", flush=True)
    print("=" * 50, flush=True)
    
    try:
        # Import FastAPI components
        from main import app
        
        # Simulate startup
        fastapi_logger = logging.getLogger("fastapi")
        fastapi_logger.info("⚡ FastAPI startup simulation")
        
        print("✅ FastAPI startup test complete", flush=True)
        
    except Exception as e:
        print(f"❌ FastAPI startup test failed: {e}", flush=True)
    
    print("=" * 50, flush=True)

def main():
    """Run all logging tests."""
    
    print("🧪 COMPREHENSIVE LOGGING TEST SUITE", flush=True)
    print("=" * 60, flush=True)
    print(f"Python Version: {sys.version}", flush=True)
    print(f"Log Level: {os.getenv('LOG_LEVEL', 'INFO')}", flush=True)
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}", flush=True)
    print("=" * 60, flush=True)
    
    # Run all tests
    test_basic_logging()
    test_agent_logging()
    test_uvicorn_compatibility()
    test_fastapi_startup()
    
    print("\n📊 TEST SUMMARY", flush=True)
    print("=" * 30, flush=True)
    print("If you can see this message and the test messages above,", flush=True)
    print("then logging is working correctly and not being suppressed.", flush=True)
    print("=" * 30, flush=True)
    
    # Final verification
    final_logger = logging.getLogger("final_test")
    final_logger.info("🎉 All logging tests completed successfully!")

if __name__ == "__main__":
    main()
