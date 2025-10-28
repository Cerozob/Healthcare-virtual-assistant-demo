"""
Logging configuration module for AgentCore deployment.
This module provides logging configuration that works with WSGI servers
and ensures logs are visible in AgentCore CloudWatch.
"""

import os
import sys
import logging
from typing import Optional

def force_stdout_logging():
    """
    Force all logging output to stdout to prevent WSGI suppression.
    This is critical for AgentCore CloudWatch log visibility.
    """
    # Redirect stderr to stdout to capture all output
    sys.stderr = sys.stdout
    
    # Ensure stdout is unbuffered for immediate log visibility
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(line_buffering=True)
    
    # Set environment variables to force unbuffered output
    os.environ['PYTHONUNBUFFERED'] = '1'
    os.environ['PYTHONIOENCODING'] = 'utf-8'

def create_agentcore_formatter() -> logging.Formatter:
    """Create a formatter optimized for AgentCore CloudWatch logs."""
    return logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def configure_root_logger(log_level: str = "INFO") -> logging.Logger:
    """
    Configure the root logger for AgentCore deployment.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured root logger
    """
    # Force stdout logging first
    force_stdout_logging()
    
    log_level_value = getattr(logging, log_level.upper(), logging.INFO)
    
    # Get root logger and clear any existing configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture everything
    
    # Remove all existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create and configure stdout handler
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    stdout_handler.setLevel(log_level_value)
    stdout_handler.setFormatter(create_agentcore_formatter())
    
    # Add handler to root logger
    root_logger.addHandler(stdout_handler)
    
    return root_logger

def configure_framework_loggers(log_level: str = "INFO"):
    """
    Configure framework-specific loggers (uvicorn, fastapi, etc.)
    to work properly with AgentCore.
    
    Args:
        log_level: Logging level for framework loggers
    """
    log_level_value = getattr(logging, log_level.upper(), logging.INFO)
    
    # Framework loggers to configure
    framework_loggers = [
        ("uvicorn", log_level_value),
        ("uvicorn.access", log_level_value),
        ("uvicorn.error", log_level_value),
        ("fastapi", log_level_value),
        ("strands", log_level_value),
        ("agents", log_level_value),
        ("mcp", log_level_value),
        # Reduce noise from AWS SDKs
        ("boto3", logging.WARNING),
        ("botocore", logging.WARNING),
        ("urllib3", logging.WARNING),
    ]
    
    for logger_name, level in framework_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        logger.propagate = True  # Allow propagation to root logger
        
        # Clear any existing handlers to prevent duplicates
        logger.handlers.clear()
        
        # Ensure logger is not disabled
        logger.disabled = False

def test_logging_configuration():
    """Test that logging configuration is working properly."""
    
    # Test different loggers
    test_loggers = [
        "root",
        "agents",
        "uvicorn", 
        "fastapi",
        "strands"
    ]
    
    print("🧪 LOGGING CONFIGURATION TEST", flush=True)
    print("-" * 40, flush=True)
    
    for logger_name in test_loggers:
        if logger_name == "root":
            logger = logging.getLogger()
        else:
            logger = logging.getLogger(logger_name)
        
        logger.info(f"✅ {logger_name.upper()} logger test - visible in AgentCore")
    
    print("-" * 40, flush=True)
    print("✅ Logging configuration test complete", flush=True)

def setup_agentcore_logging(log_level: Optional[str] = None) -> logging.Logger:
    """
    Complete logging setup for AgentCore deployment.
    
    Args:
        log_level: Optional log level override
        
    Returns:
        Configured root logger
    """
    # Get log level from environment or parameter
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")
    
    # Configure logging
    root_logger = configure_root_logger(log_level)
    configure_framework_loggers(log_level)
    
    # Log configuration info
    root_logger.info("🔧 AgentCore logging configuration complete")
    root_logger.info(f"   • Log Level: {log_level}")
    root_logger.info(f"   • Output: stdout (AgentCore compatible)")
    root_logger.info(f"   • Unbuffered: {os.getenv('PYTHONUNBUFFERED', 'not set')}")
    
    # Test the configuration
    test_logging_configuration()
    
    return root_logger

if __name__ == "__main__":
    # Test the logging configuration
    setup_agentcore_logging()
    print("🎉 Logging configuration test completed successfully!")
