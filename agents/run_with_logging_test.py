#!/usr/bin/env python3
"""
Production-like test runner for the healthcare agent with comprehensive logging.
This script simulates how the agent would run in AgentCore with proper logging.
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

def setup_environment():
    """Setup environment variables for testing."""
    
    # Set logging environment variables
    os.environ['PYTHONUNBUFFERED'] = '1'
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['LOG_LEVEL'] = os.getenv('LOG_LEVEL', 'INFO')
    
    # Set agent configuration
    os.environ['ENVIRONMENT'] = 'test'
    os.environ['AWS_REGION'] = os.getenv('AWS_REGION', 'us-east-1')
    
    # MCP Gateway configuration (optional)
    if not os.getenv('USE_MCP_GATEWAY'):
        os.environ['USE_MCP_GATEWAY'] = 'false'  # Default to local tools for testing
    
    print("🔧 Environment Configuration:", flush=True)
    print(f"   • PYTHONUNBUFFERED: {os.environ.get('PYTHONUNBUFFERED')}", flush=True)
    print(f"   • LOG_LEVEL: {os.environ.get('LOG_LEVEL')}", flush=True)
    print(f"   • USE_MCP_GATEWAY: {os.environ.get('USE_MCP_GATEWAY')}", flush=True)
    print(f"   • AWS_REGION: {os.environ.get('AWS_REGION')}", flush=True)

def test_logging_before_server():
    """Test logging configuration before starting the server."""
    
    print("\n🧪 PRE-SERVER LOGGING TEST", flush=True)
    print("=" * 50, flush=True)
    
    try:
        # Test the logging configuration module
        from logging_config import setup_agentcore_logging
        
        logger = setup_agentcore_logging()
        logger.info("✅ Pre-server logging test successful")
        
        # Test the main module logging
        from main import test_logging
        test_logging()
        
        print("✅ Pre-server logging tests passed", flush=True)
        return True
        
    except Exception as e:
        print(f"❌ Pre-server logging test failed: {e}", flush=True)
        return False

def run_server():
    """Run the FastAPI server with uvicorn."""
    
    print("\n🚀 Starting FastAPI server with uvicorn...", flush=True)
    print("=" * 50, flush=True)
    
    # Uvicorn command with logging configuration
    cmd = [
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--log-level", os.getenv('LOG_LEVEL', 'info').lower(),
        "--access-log",  # Enable access logs
        "--use-colors",  # Enable colored output
        "--loop", "asyncio"
    ]
    
    print(f"Command: {' '.join(cmd)}", flush=True)
    print("=" * 50, flush=True)
    
    try:
        # Start the server
        process = subprocess.Popen(
            cmd,
            stdout=sys.stdout,
            stderr=sys.stdout,
            bufsize=0,  # Unbuffered
            universal_newlines=True
        )
        
        # Wait a bit for server to start
        time.sleep(3)
        
        # Test the server endpoints
        test_server_endpoints()
        
        # Keep server running
        print("\n🎯 Server is running. Press Ctrl+C to stop.", flush=True)
        print("🔗 Test endpoints:", flush=True)
        print("   • http://localhost:8000/ping", flush=True)
        print("   • http://localhost:8000/test-logging", flush=True)
        print("   • http://localhost:8000/docs", flush=True)
        
        # Wait for interrupt
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...", flush=True)
            process.terminate()
            process.wait()
            
    except Exception as e:
        print(f"❌ Server failed to start: {e}", flush=True)
        return False
    
    return True

def test_server_endpoints():
    """Test server endpoints to verify logging."""
    
    print("\n🔍 Testing server endpoints...", flush=True)
    
    try:
        import requests
        import time
        
        # Wait for server to be ready
        time.sleep(2)
        
        # Test ping endpoint
        response = requests.get("http://localhost:8000/ping", timeout=5)
        print(f"✅ Ping endpoint: {response.status_code}", flush=True)
        
        # Test logging endpoint
        response = requests.get("http://localhost:8000/test-logging", timeout=5)
        print(f"✅ Logging test endpoint: {response.status_code}", flush=True)
        
    except Exception as e:
        print(f"⚠️ Endpoint test failed (server may still be starting): {e}", flush=True)

def main():
    """Main test runner."""
    
    print("🏥 Healthcare Agent - Production Logging Test", flush=True)
    print("=" * 60, flush=True)
    
    # Setup environment
    setup_environment()
    
    # Test logging before starting server
    if not test_logging_before_server():
        print("❌ Pre-server tests failed. Exiting.", flush=True)
        sys.exit(1)
    
    # Run the server
    try:
        run_server()
    except KeyboardInterrupt:
        print("\n👋 Test completed.", flush=True)
    except Exception as e:
        print(f"❌ Test failed: {e}", flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
