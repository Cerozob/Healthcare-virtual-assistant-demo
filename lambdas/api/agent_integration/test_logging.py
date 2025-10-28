#!/usr/bin/env python3
"""
Test script to demonstrate enhanced logging capabilities for AgentCore integration.
This script can be used to test the logging functionality locally.
"""

import json
import sys
import os
from datetime import datetime

# Add the shared directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from utils import StructuredLogger, create_request_logger, log_performance_metrics, log_aws_api_call


def test_structured_logging():
    """Test the structured logging functionality."""
    print("=== Testing Structured Logging ===")
    
    # Test basic structured logger
    logger = StructuredLogger("test_logger")
    
    logger.info("Application started", 
                component="test_script", 
                version="1.0.0")
    
    logger.debug("Processing request", 
                 user_id="user123", 
                 action="login")
    
    logger.warning("Rate limit approaching", 
                   current_requests=95, 
                   limit=100)
    
    logger.error("Database connection failed", 
                 database="primary", 
                 error_code="CONN_TIMEOUT")
    
    # Test exception logging
    try:
        raise ValueError("Test exception for logging")
    except Exception as e:
        logger.exception("Test exception occurred", exc=e, context="test_function")


def test_request_logger():
    """Test the request-scoped logger."""
    print("\n=== Testing Request Logger ===")
    
    request_logger = create_request_logger("req_12345")
    
    request_logger.info("Request started", 
                       method="POST", 
                       path="/agentcore/chat")
    
    request_logger.debug("Validating request body", 
                        body_size=1024)
    
    request_logger.info("AgentCore invocation started", 
                       session_id="session_abc123", 
                       agentcore_arn="arn:aws:bedrock-agentcore:us-east-1:123456789012:agent-runtime/EXAMPLE")
    
    request_logger.info("Request completed successfully", 
                       duration_ms=1250.5, 
                       status_code=200)


def test_performance_logging():
    """Test performance metrics logging."""
    print("\n=== Testing Performance Logging ===")
    
    # Simulate function execution
    start_time = datetime.now()
    
    # Simulate some work
    import time
    time.sleep(0.1)
    
    end_time = datetime.now()
    duration_ms = (end_time - start_time).total_seconds() * 1000
    
    log_performance_metrics(
        "handle_agentcore_chat",
        duration_ms,
        payload_size_bytes=2048,
        response_size_bytes=1536,
        session_id="session_test123"
    )


def test_aws_api_logging():
    """Test AWS API call logging."""
    print("\n=== Testing AWS API Call Logging ===")
    
    # Simulate successful API call
    log_aws_api_call(
        service="bedrock-agentcore",
        operation="invoke_agent_runtime",
        duration_ms=850.2,
        success=True,
        agentcore_arn="arn:aws:bedrock-agentcore:us-east-1:123456789012:agent-runtime/EXAMPLE",
        session_id="session_test123",
        payload_size=2048
    )
    
    # Simulate failed API call
    log_aws_api_call(
        service="ssm",
        operation="get_parameter",
        duration_ms=125.7,
        success=False,
        parameter_name="/healthcare/agentcore/endpoint-url",
        error_code="ParameterNotFound"
    )


def simulate_agentcore_request():
    """Simulate a complete AgentCore request with logging."""
    print("\n=== Simulating Complete AgentCore Request ===")
    
    request_logger = create_request_logger("req_simulation_001")
    
    # Request start
    request_logger.info("AgentCore chat request received",
                       method="POST",
                       path="/agentcore/chat",
                       source_ip="192.168.1.100",
                       user_agent="HealthcareApp/1.0")
    
    # SSM parameter retrieval
    ssm_start = datetime.now()
    time.sleep(0.05)  # Simulate SSM call
    ssm_duration = (datetime.now() - ssm_start).total_seconds() * 1000
    
    log_aws_api_call(
        service="ssm",
        operation="get_parameter",
        duration_ms=ssm_duration,
        success=True,
        parameter_name="/healthcare/agentcore/endpoint-url"
    )
    
    request_logger.info("Retrieved AgentCore ARN successfully",
                       agentcore_arn="arn:aws:bedrock-agentcore:us-east-1:123456789012:agent-runtime/HEALTHCARE",
                       ssm_duration_ms=round(ssm_duration, 2))
    
    # Request processing
    request_logger.debug("Processing message",
                        message_length=156,
                        session_id="agentcore_session_abc123def456")
    
    # AgentCore invocation
    agentcore_start = datetime.now()
    time.sleep(0.2)  # Simulate AgentCore call
    agentcore_duration = (datetime.now() - agentcore_start).total_seconds() * 1000
    
    log_aws_api_call(
        service="bedrock-agentcore",
        operation="invoke_agent_runtime",
        duration_ms=agentcore_duration,
        success=True,
        agentcore_arn="arn:aws:bedrock-agentcore:us-east-1:123456789012:agent-runtime/HEALTHCARE",
        session_id="agentcore_session_abc123def456",
        payload_size=512
    )
    
    request_logger.info("AgentCore invocation completed successfully",
                       agentcore_duration_ms=round(agentcore_duration, 2),
                       response_size_bytes=1024)
    
    # Request completion
    total_duration = ssm_duration + agentcore_duration + 50  # Add some processing overhead
    
    request_logger.info("Chat request completed successfully",
                       total_duration_ms=round(total_duration, 2),
                       status_code=200,
                       response_length=245)


if __name__ == "__main__":
    import time
    
    print("Enhanced Logging Test for AgentCore Integration")
    print("=" * 50)
    
    test_structured_logging()
    test_request_logger()
    test_performance_logging()
    test_aws_api_logging()
    simulate_agentcore_request()
    
    print("\n" + "=" * 50)
    print("Logging test completed!")
    print("\nKey features demonstrated:")
    print("- Structured JSON logging with consistent format")
    print("- Request-scoped logging with request IDs")
    print("- Performance metrics tracking")
    print("- AWS API call monitoring")
    print("- Exception handling with stack traces")
    print("- Contextual information for debugging")
