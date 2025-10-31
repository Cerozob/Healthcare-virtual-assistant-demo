"""
Simplified Healthcare Assistant Agent using Strands framework.
FastAPI implementation for AgentCore Runtime deployment.
"""

import logging
import os
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from shared.config import get_agent_config
from healthcare_agent import create_healthcare_agent
from shared.utils import get_logger
from shared.models import PatientInfoResponse, SessionContext
from logging_config import setup_agentcore_logging
import uvicorn

# Initialize logging
setup_agentcore_logging()
logger = get_logger(__name__)


def log_environment_variables():
    """Log all environment variables for debugging."""
    logger.info("=== ENVIRONMENT VARIABLES ===")
    env_vars = dict(os.environ)
    for key, value in sorted(env_vars.items()):
        # Skip AWS credentials for security
        if any(sensitive in key.upper() for sensitive in ["ACCESS_KEY", "SECRET_KEY", "TOKEN", "PASSWORD"]):
            continue
        logger.info(f"{key}={value}")
    logger.info("=== END ENVIRONMENT VARIABLES ===")


# Log environment variables for debugging
log_environment_variables()

# Initialize FastAPI app
app = FastAPI(title="Healthcare Assistant Agent", version="2.0.0")

# Load configuration
config = get_agent_config()


class InvocationRequest(BaseModel):
    prompt: str
    # AgentCore only sends 'prompt' field according to HTTP contract
    # sessionId will be generated if not provided


class PatientContextResponse(BaseModel):
    """Patient context for frontend integration."""
    patient_id: Optional[str] = Field(None, description="Patient ID")
    patient_name: Optional[str] = Field(None, description="Patient name")
    has_patient_context: bool = Field(False, description="Has patient context")
    patient_found: bool = Field(
        False, description="Patient found in interaction")
    patient_data: Optional[Dict[str, Any]] = Field(
        None, description="Patient data")


@app.on_event("startup")
async def startup_event():
    """FastAPI startup event."""
    logger.info("🚀 Healthcare Assistant starting up")
    logger.info(f"Configuration: {config.model_dump()}")

    # Test gateway connection and tool discovery first
    logger.info("🔍 Testing AgentCore Gateway connection and tool discovery...")
    try:
        from shared.mcp_client import test_agentcore_gateway
        
        test_results = test_agentcore_gateway(
            config.mcp_gateway_url,
            config.aws_region
        )
        
        if test_results["connection_successful"]:
            logger.info(f"✅ Gateway connection successful - {test_results['tools_discovered']} tools available")
            if test_results["tool_names"]:
                logger.info(f"🔧 Available tools: {', '.join(test_results['tool_names'])}")
        else:
            logger.error(f"❌ Gateway connection failed: {test_results.get('error_message', 'Unknown error')}")
            
    except Exception as gateway_error:
        logger.warning(f"⚠️ Gateway test failed: {gateway_error}")

    # Test agent creation
    try:
        test_agent = create_healthcare_agent("startup_test")
        logger.info("✅ Agent creation test successful")
    except ValueError as e:
        if "MCP" in str(e):
            logger.error(f"❌ MCP Gateway connection failed: {e}")
            logger.error("🔧 Please check:")
            logger.error("   - MCP_GATEWAY_URL is correctly configured")
            logger.error("   - AWS credentials have execute-api permissions")
            logger.error("   - AgentCore Gateway is deployed and accessible")
            logger.error("   - Network connectivity to the gateway")
        else:
            logger.error(f"❌ Agent creation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Agent creation test failed: {e}")
        raise


@app.post("/invocations")
async def invoke_agent(request: InvocationRequest):
    """Main AgentCore invocation endpoint."""
    start_time = time.time()

    try:
        logger.info("🚀 === HEALTHCARE AGENT INVOCATION ===")

        user_message = request.prompt
        if not user_message:
            raise HTTPException(status_code=400, detail="No prompt provided")

        # Generate session ID (AgentCore doesn't provide sessionId in request)
        session_id = f"healthcare_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"📝 Session: {session_id}")
        logger.info(f"💬 Message: {user_message[:100]}...")

        # Create healthcare agent
        agent_start = time.time()
        try:
            healthcare_agent = create_healthcare_agent(session_id)
            agent_time = (time.time() - agent_start) * 1000
        except ValueError as e:
            if "MCP" in str(e):
                logger.error(
                    f"❌ MCP Gateway connection failed during request: {e}")
                raise HTTPException(
                    status_code=503,
                    detail=f"Healthcare agent unavailable - MCP Gateway connection failed: {str(e)}"
                )
            else:
                raise HTTPException(
                    status_code=500, detail=f"Agent creation failed: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Unexpected agent creation error: {e}")
            raise HTTPException(
                status_code=500, detail=f"Agent creation failed: {str(e)}")

        logger.info(f"🤖 Agent created in {agent_time:.2f}ms")

        # Process the message with structured output
        process_start = time.time()
        response_message, structured_context = healthcare_agent.invoke_with_structured_output(
            user_message)
        process_time = (time.time() - process_start) * 1000

        # Get patient context (fallback to manual if structured output fails)
        patient_context = structured_context or healthcare_agent.get_patient_context()

        total_time = (time.time() - start_time) * 1000

        logger.info(f"✅ Request completed in {total_time:.2f}ms")
        logger.info(f"   • Agent creation: {agent_time:.2f}ms")
        logger.info(f"   • Message processing: {process_time:.2f}ms")
        logger.info(
            f"   • Patient context: {patient_context.get('has_patient_context', False)}")
        logger.info(
            f"   • Session persisted: S3 bucket {config.session_bucket}/chats/ (always persisted)")

        # Return AgentCore-compatible response
        return {
            "response": response_message,
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": "healthcare-assistant-strands",
            "session_id": session_id,
            "patient_context": patient_context,
            "performance": {
                "total_time_ms": total_time,
                "agent_creation_ms": agent_time,
                "processing_ms": process_time
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Invocation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Healthcare agent invocation failed: {str(e)}"
        )


@app.get("/ping")
async def ping():
    """Health check endpoint."""
    logger.info("🏓 Health check")
    return {
        "status": "Healthy",
        "timestamp": int(time.time()),
        "version": "2.0.0",
        "config": {
            "model": config.model_id,
            "knowledge_base": bool(config.knowledge_base_id),
            "mcp_gateway": bool(config.mcp_gateway_url),
            "guardrails": bool(config.guardrail_id)
        }
    }


if __name__ == "__main__":

    logger.info("🚀 Starting Healthcare Assistant Agent")
    logger.info(f"Configuration: {config.model_dump()}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="debug"
    )
