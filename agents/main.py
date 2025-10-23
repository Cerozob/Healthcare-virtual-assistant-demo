"""
Main entry point for Strands Agents Healthcare Assistant.
AgentCore Runtime deployment configuration with streaming support.
"""

import os
import asyncio
import logging
from typing import Dict, Any, AsyncGenerator
from datetime import datetime

# Bedrock AgentCore imports (will be available when framework is installed)
try:
    from bedrock_agentcore.runtime import BedrockAgentCoreApp
    from bedrock_agentcore.models import InvocationRequest, InvocationResponse
except ImportError:
    # Placeholder for development
    class BedrockAgentCoreApp:
        def __init__(self):
            pass
        
        def entrypoint(self, func):
            return func
        
        def run(self, *args, **kwargs):
            pass

# FastAPI imports for health endpoints
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
except ImportError:
    # Placeholder for development
    class FastAPI:
        def __init__(self):
            pass
        
        def get(self, path):
            def decorator(func):
                return func
            return decorator

from .shared.config import get_agent_config
from .shared.utils import get_logger, sanitize_for_logging
from .shared.context import ContextManager
from .shared.guardrails import guardrails_manager, validate_guardrails_setup
from .orchestrator.agent import orchestrator_invocation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = get_logger(__name__)

# Initialize AgentCore application
app = BedrockAgentCoreApp()

# Initialize FastAPI for health endpoints
health_app = FastAPI(title="Healthcare Assistant Agent", version="1.0.0")


@app.entrypoint
async def healthcare_assistant_entrypoint(
    invocation_request: Dict[str, Any]
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Main AgentCore entrypoint for healthcare assistant with streaming support.
    
    Args:
        invocation_request: AgentCore invocation request
        
    Yields:
        Dict[str, Any]: Streaming response events
    """
    try:
        logger.info("Healthcare assistant invocation started")
        
        # Extract request data
        prompt = invocation_request.get("prompt", "")
        session_id = invocation_request.get("sessionId", "")
        invocation_state = invocation_request.get("invocationState", {})
        
        # Log sanitized request info
        sanitized_request = sanitize_for_logging({
            "prompt_length": len(prompt),
            "session_id": session_id,
            "has_invocation_state": bool(invocation_state)
        })
        logger.info(f"Processing request: {sanitized_request}")
        
        # Prepare payload for orchestrator
        payload = {
            "prompt": prompt,
            "session_context": invocation_state.get("session_context", {}),
            "multimodal_inputs": invocation_request.get("multimodalInputs", []),
            "session_id": session_id
        }
        
        # Stream response from orchestrator
        response_count = 0
        async for event in orchestrator_invocation(payload):
            response_count += 1
            
            # Add AgentCore-specific metadata
            event["invocation_metadata"] = {
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "response_sequence": response_count
            }
            
            # Update invocation state if context update
            if event.get("type") == "context_update":
                session_context = event.get("metadata", {}).get("session_context")
                if session_context:
                    invocation_state["session_context"] = session_context
                    event["invocation_state"] = invocation_state
            
            yield event
        
        logger.info(f"Healthcare assistant invocation completed. Responses: {response_count}")
        
    except Exception as e:
        logger.error(f"Error in healthcare assistant entrypoint: {str(e)}")
        
        yield {
            "type": "error",
            "content": f"Error del sistema de asistente médico: {str(e)}",
            "metadata": {
                "error": str(e),
                "error_type": "entrypoint_error"
            },
            "invocation_metadata": {
                "session_id": invocation_request.get("sessionId", ""),
                "timestamp": datetime.utcnow().isoformat(),
                "error": True
            }
        }


@health_app.get("/ping")
async def health_check() -> JSONResponse:
    """
    Health check endpoint required by AgentCore.
    
    Returns:
        JSONResponse: Health status
    """
    try:
        # Verify configuration
        config = get_agent_config()
        
        # Get guardrails status
        guardrails_status = guardrails_manager.validate_guardrails_configuration()
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "healthcare-assistant",
            "version": "1.0.0",
            "configuration": {
                "model_configured": bool(config.model_id),
                "knowledge_base_configured": bool(config.knowledge_base_id),
                "api_endpoint_configured": bool(config.healthcare_api_endpoint),
                "database_configured": bool(config.database_cluster_arn),
                "guardrails_configured": guardrails_status.get('guardrails_configured', False),
                "pii_protection_enabled": True  # Always enabled (local + guardrails)
            },
            "security": {
                "guardrails_enabled": guardrails_status.get('guardrails_configured', False),
                "local_pii_filtering": True,
                "no_pii_logging_policy": True
            }
        }
        
        return JSONResponse(content=health_status, status_code=200)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        
        error_status = {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "healthcare-assistant",
            "error": str(e)
        }
        
        return JSONResponse(content=error_status, status_code=503)


@health_app.get("/invocations")
async def invocations_endpoint() -> JSONResponse:
    """
    Invocations endpoint information for AgentCore.
    
    Returns:
        JSONResponse: Endpoint information
    """
    return JSONResponse(content={
        "endpoint": "/invocations",
        "method": "POST",
        "streaming": True,
        "capabilities": [
            "patient_information_retrieval",
            "appointment_scheduling",
            "knowledge_base_search",
            "document_processing",
            "spanish_language_support",
            "multimodal_input"
        ],
        "supported_languages": ["es-LATAM", "es-ES", "en-US"],
        "agent_type": "healthcare_assistant"
    })


def setup_error_handlers():
    """Set up global error handlers for the application."""
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        """Global exception handler."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Allow keyboard interrupt to pass through
            return
        
        logger.error(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
    
    import sys
    sys.excepthook = handle_exception


def validate_environment():
    """Validate required environment variables and configuration."""
    try:
        config = get_agent_config()
        
        required_configs = [
            ("MODEL_ID", config.model_id),
            ("KNOWLEDGE_BASE_ID", config.knowledge_base_id),
            ("HEALTHCARE_API_ENDPOINT", config.healthcare_api_endpoint),
            ("DATABASE_CLUSTER_ARN", config.database_cluster_arn),
            ("DATABASE_SECRET_ARN", config.database_secret_arn)
        ]
        
        missing_configs = []
        for config_name, config_value in required_configs:
            if not config_value:
                missing_configs.append(config_name)
        
        if missing_configs:
            logger.warning(f"Missing configuration: {', '.join(missing_configs)}")
            logger.warning("Some features may not work properly")
        else:
            logger.info("All required configuration validated successfully")
        
        # Validate Bedrock Guardrails configuration
        guardrails_validation = validate_guardrails_setup()
        if guardrails_validation.get('guardrails_configured'):
            logger.info("Bedrock Guardrails configured and validated")
        else:
            logger.warning("Bedrock Guardrails not configured - using local PII filtering only")
            logger.warning("For production deployment, configure Bedrock Guardrails for enhanced PII/PHI protection")
            
    except Exception as e:
        logger.error(f"Configuration validation failed: {str(e)}")
        raise


def main():
    """Main function to run the healthcare assistant agent."""
    try:
        logger.info("Starting Healthcare Assistant Agent")
        
        # Setup error handlers
        setup_error_handlers()
        
        # Validate environment
        validate_environment()
        
        # Log startup information
        logger.info("Healthcare Assistant Agent configured successfully")
        logger.info("Capabilities: Patient info, Appointments, Knowledge base, Documents")
        logger.info("Language: Spanish (LATAM) with English support")
        logger.info("Streaming: Enabled")
        
        # Run AgentCore application
        app.run(
            host="0.0.0.0",
            port=8080,
            health_app=health_app
        )
        
    except Exception as e:
        logger.error(f"Failed to start Healthcare Assistant Agent: {str(e)}")
        raise


if __name__ == "__main__":
    main()
