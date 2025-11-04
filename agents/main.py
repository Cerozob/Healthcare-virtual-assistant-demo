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
logger = get_logger(__name__)

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
async def agent_invocation(payload):
    """
    Main entrypoint for agent invocations with Strands multimodal support.
    Expects Strands format: {content: [...], sessionId?}
    Returns StructuredOutput format for frontend.
    """
    logger.info(f"🎯 Agent invocation: {list(payload.keys())}")

    # Extract fields from Strands-compatible format
    content_blocks = payload.get("content", [])
    session_id = payload.get("sessionId", f"healthcare_session_{uuid4()}")

    logger.info(f"📝 Session: {session_id}")
    logger.info(f"📦 Content blocks: {len(content_blocks)}")

    # Log content block details
    for i, block in enumerate(content_blocks):
        block_type = list(block.keys())[0] if block else "unknown"
        if block_type == "text":
            text_preview = block["text"][:50] + \
                "..." if len(block["text"]) > 50 else block["text"]
            logger.info(f"   {i+1}. Text: {text_preview}")
        elif block_type == "image":
            image_format = block["image"].get("format", "unknown")
            logger.info(f"   {i+1}. Image: {image_format} format")
        elif block_type == "document":
            doc_name = block["document"].get("name", "unknown")
            doc_format = block["document"].get("format", "unknown")
            logger.info(f"   {i+1}. Document: {doc_name} ({doc_format})")

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

        logger.info("✅ Agent processing completed")
        return result

    except Exception as e:
        logger.error(f"❌ Agent processing failed: {e}")
        import traceback
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")

        return create_error_response(
            session_id,
            type(e).__name__,
            f"Agent processing failed: {str(e)}",
            {"traceback": traceback.format_exc()}
        )

    logger.info(f"🎯 === AGENT INVOCATION END ===")


@app.ping
def health_check():

    # For now, always return healthy
    # In the future, we could check if background tasks are running
    return PingStatus.HEALTHY


if __name__ == "__main__":
    logger.info("🚀 Starting Healthcare Assistant Agent")
    logger.info("🌐 Server will start on http://0.0.0.0:8080")
    logger.info("📍 Endpoints available:")
    logger.info("   - GET  /ping")
    logger.info("   - POST /invocations")

    # Run the AgentCore app
    app.run()
