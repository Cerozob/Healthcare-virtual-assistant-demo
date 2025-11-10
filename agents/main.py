"""
Healthcare Assistant Agent using Strands framework with proper AgentCore integration.
Follows AWS AgentCore best practices for streaming and long-running operations.
"""

from bedrock_agentcore.runtime import PingStatus
import logging
import os
import sys
from strands import Agent
from bedrock_agentcore import BedrockAgentCoreApp
from uuid import uuid4
from shared.config import get_agent_config
from healthcare_agent import create_healthcare_agent
from shared.utils import get_logger
from shared.schema_validator import validate_request, create_error_response, validate_response
from logging_config import setup_agentcore_logging

# Initialize logging
setup_agentcore_logging()
logger = logging.getLogger("healthcare_agent.main")

# Initialize AgentCore app
app = BedrockAgentCoreApp()

# Load configuration
config = get_agent_config()

# Global healthcare agent instances (session-based)
healthcare_agents = {}


def get_or_create_agent(session_id: str):
    """Get existing agent or create new one for session."""
    if session_id not in healthcare_agents:
        healthcare_agents[session_id] = create_healthcare_agent(session_id)
    return healthcare_agents[session_id]


@app.entrypoint
async def agent_invocation(payload, context):
    """
    Main entrypoint for agent invocations with Strands multimodal support.
    Expects Strands format: {content: [...], sessionId?}
    Returns StructuredOutput format for frontend.
    """
    logger.info(f"🎯 Agent invocation started | payload_keys={list(payload.keys())}")
    agentcore_sessionid= context.session_id
    logger.info(f"full payload: {payload}")

    # Extract fields from Strands-compatible format
    content_blocks = payload.get("content", [])
    session_id = payload.get("sessionId", f"healthcare_session_{uuid4()}")

    logger.info(f"📝 Processing request | session_id={session_id} | content_blocks={len(content_blocks)}")
    logger.info(f"🔑 Session ID received from payload: {session_id}")
    logger.info(f"🔑 AgentCore session ID: {agentcore_sessionid}")
    logger.info(f"🔑 Session ID type: {type(session_id).__name__}")
    
    # Note: The AgentCore SDK runtimeSessionId is managed at the SDK level
    # and should match this session_id for proper session continuity

    # Log content block details with structured format
    for i, block in enumerate(content_blocks):
        block_type = list(block.keys())[0] if block else "unknown"
        if block_type == "text":
            text_preview = block["text"][:50] + \
                "..." if len(block["text"]) > 50 else block["text"]
            logger.info(f"📄 Content block {i+1} | type=text | preview='{text_preview}'")
        elif block_type == "image":
            image_format = block["image"].get("format", "unknown")
            logger.info(f"🖼️ Content block {i+1} | type=image | format={image_format}")
        elif block_type == "document":
            doc_name = block["document"].get("name", "unknown")
            doc_format = block["document"].get("format", "unknown")
            logger.info(f"📋 Content block {i+1} | type=document | name={doc_name} | format={doc_format}")

    # Validate content blocks
    if not content_blocks:
        return create_error_response(
            session_id,
            "INVALID_REQUEST",
            "Content blocks array is required and cannot be empty"
        )

    # Initialize and process with multimodal support
    try:
        agent = get_or_create_agent(session_id)

        # Process message (non-streaming)
        result = agent.process_message(content_blocks)

        logger.info(f"✅ Agent processing completed | session_id={session_id}")
        
        # Verify session ID consistency
        result_session_id = result.get("sessionId")
        if result_session_id != session_id:
            logger.warning(f"⚠️ Session ID mismatch!")
            logger.warning(f"   • Input session_id: {session_id}")
            logger.warning(f"   • Result sessionId: {result_session_id}")
        else:
            logger.info(f"✅ Session ID consistency verified: {session_id}")
        
        return result

    except Exception as e:
        logger.error(f"❌ Agent processing failed | session_id={session_id} | error={str(e)} | error_type={type(e).__name__}")
        import traceback
        logger.debug(f"🔍 Full traceback | session_id={session_id} | traceback={traceback.format_exc()}")

        return create_error_response(
            session_id,
            type(e).__name__,
            f"Agent processing failed: {str(e)}",
            {"traceback": traceback.format_exc()}
        )


@app.ping
def health_check():

    # For now, always return healthy
    # In the future, we could check if background tasks are running
    return PingStatus.HEALTHY


if __name__ == "__main__":
    logger.info("🚀 Healthcare Assistant Agent starting | server=AgentCore | port=8080")
    logger.info("📍 Available endpoints | GET=/ping | POST=/invocations")

    # Run the AgentCore app
    app.run()
