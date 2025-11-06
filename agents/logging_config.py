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


class StructuredCloudWatchFormatter(logging.Formatter):
    """
    Structured formatter for CloudWatch logs with better context.
    """

    def format(self, record):
        # Add structured context to log records
        if not hasattr(record, 'component'):
            # Determine component from logger name
            if record.name.startswith('healthcare_agent'):
                record.component = 'HEALTHCARE_AGENT'
            elif record.name.startswith('info_retrieval'):
                record.component = 'INFO_RETRIEVAL'
            elif record.name.startswith('appointment_scheduling'):
                record.component = 'APPOINTMENT_SCHEDULING'
            elif record.name.startswith('shared'):
                record.component = 'SHARED_UTILS'
            elif record.name.startswith('strands'):
                record.component = 'STRANDS_FRAMEWORK'
            elif record.name.startswith('bedrock_agentcore'):
                record.component = 'AGENTCORE_RUNTIME'
            elif record.name.startswith('uvicorn'):
                record.component = 'HTTP_SERVER'
            elif record.name == '__main__':
                record.component = 'MAIN_HANDLER'
            else:
                record.component = record.name.upper().replace('.', '_')

        # Format with structured information
        formatted = f"{self.formatTime(record)} | {record.levelname:<8} | {record.component:<20} | {record.getMessage()}"

        # Add exception info if present
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"

        return formatted


def create_agentcore_formatter() -> logging.Formatter:
    """Create a formatter optimized for AgentCore CloudWatch logs."""
    return StructuredCloudWatchFormatter(datefmt='%Y-%m-%d %H:%M:%S')


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

    # Framework loggers to configure with meaningful names
    framework_loggers = [
        # HTTP Server logs
        ("uvicorn", log_level_value),
        ("uvicorn.access", "WARNING"),
        ("uvicorn.error", log_level_value),
        ("fastapi", log_level_value),

        # Agent framework logs
        ("strands", log_level_value),
        ("strands.agent", log_level_value),
        ("strands.models", log_level_value),
        ("strands.session", log_level_value),

        # Application-specific loggers
        ("healthcare_agent", log_level_value),
        ("info_retrieval", log_level_value),
        ("appointment_scheduling", log_level_value),
        ("shared", log_level_value),
        ("mcp", log_level_value),

        # AgentCore runtime
        ("bedrock_agentcore", log_level_value),
        ("bedrock_agentcore.memory", log_level_value),
        ("bedrock_agentcore.app", log_level_value),

        # Reduce noise from AWS SDKs
        ("boto3", logging.WARNING),
        ("botocore", logging.WARNING),
        ("urllib3", logging.WARNING),
        ("s3transfer", logging.WARNING),
    ]

    for logger_name, level in framework_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        logger.propagate = True  # Allow propagation to root logger

        # Clear any existing handlers to prevent duplicates
        logger.handlers.clear()

        # Ensure logger is not disabled
        logger.disabled = False

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

    # Configure Strands framework logging level (set to DEBUG for more verbose output)
    strands_log_level = "DEBUG"
    strands_level_value = logging.DEBUG

    strands_loggers = [
        "strands.agent",
        "strands.agent.agent",
        "strands.telemetry",
        "strands.telemetry.metrics",
        "strands.session",
        "strands.models"
    ]

    for logger_name in strands_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(strands_level_value)
        logger.propagate = True

    # Log configuration info
    root_logger.info("🔧 AgentCore logging configuration complete")
    root_logger.info(f"   • Log Level: {log_level}")
    root_logger.info(f"   • Output: stdout (AgentCore compatible)")
    root_logger.info(
        f"   • Unbuffered: {os.getenv('PYTHONUNBUFFERED', 'not set')}")
    root_logger.info(
        f"   • Strands framework logging: {strands_log_level} level")


    return root_logger


if __name__ == "__main__":
    # Test the logging configuration
    setup_agentcore_logging()
    print("🎉 Logging configuration test completed successfully!")
