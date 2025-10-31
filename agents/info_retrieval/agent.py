"""
Information Retrieval Agent using Strands "Agents as Tools" pattern.
Handles patient information queries and medical document searches using Bedrock Knowledge Base.
"""

from typing import Dict, Any, Optional

from strands import Agent, tool
from strands.models import BedrockModel

from shared.config import get_agent_config, get_model_config
from shared.utils import get_logger
from shared.prompts import get_prompt
from shared.mcp_client import get_patient_info_tools

logger = get_logger(__name__)


# Strands "Agents as Tools" implementation
@tool
async def information_retrieval_agent(query: str) -> str:
    """
    Process and respond to information retrieval queries using Bedrock Knowledge Base.

    This agent specializes in:
    - Patient information searches
    - Medical document retrieval from Bedrock Knowledge Base
    - Healthcare data queries

    Args:
        query: Information query requiring patient data or medical knowledge

    Returns:
        str: Detailed information response with sources when available
    """
    try:
        logger.debug(
            f"Information retrieval agent processing query: {query[:100]}...")
        logger.info("Information retrieval agent processing query")

        # Get configuration
        config = get_agent_config()
        model_config = get_model_config()

        # Load system prompt from file
        system_prompt = get_prompt("information_retrieval")

        # Get patient information tools using unified MCP client with semantic search
        dynamic_tools = get_patient_info_tools(
            gateway_url=config.mcp_gateway_url,
            aws_region=config.aws_region
        )
        
        # Create specialized agent with dynamically discovered tools (no guardrails - only orchestrator has them)
        info_agent = Agent(
            system_prompt=system_prompt,
            tools=dynamic_tools,
            model=BedrockModel(
                model_id=model_config.model_id
            )
        )
        logger.info(
            f"🤖 current tools for info retrieval agent: {info_agent.tool_names}")
        # Process the query
        response = info_agent(query)
        return str(response)

    except Exception as e:
        logger.error(f"Error in information retrieval agent: {str(e)}")
        return f"❌ Error en agente de información: {str(e)}"


# Note: Tool implementations are now dynamically discovered via semantic search
# The AgentCore Gateway provides the actual tool implementations


# Export the tool function
__all__ = ["information_retrieval_agent"]
