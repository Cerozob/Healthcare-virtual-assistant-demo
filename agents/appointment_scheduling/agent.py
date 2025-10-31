"""
Appointment Scheduling Agent using Strands "Agents as Tools" pattern.
Specialized agent for managing appointment-related operations.
"""

from typing import Dict, Any, Optional

from strands import Agent, tool
from strands.models import BedrockModel
from shared.config import get_agent_config, get_model_config
from shared.utils import get_logger
from shared.prompts import get_prompt
from shared.mcp_client import get_appointment_tools, get_semantic_tools

logger = get_logger(__name__)


# Strands "Agents as Tools" implementation
@tool
async def appointment_scheduling_agent(request: str) -> str:
    """
    Handle appointment scheduling and management requests.
    
    This agent specializes in:
    - Scheduling new medical appointments
    - Checking availability of doctors and time slots
    - Managing existing appointments (view, cancel, modify)
    - Coordinating medical resources
    
    Args:
        request: Appointment scheduling request with patient and scheduling details
        
    Returns:
        str: Scheduling response with confirmation or available alternatives
    """
    try:
        logger.info("Appointment scheduling agent processing request")
        
        # Get configuration
        config = get_agent_config()
        model_config = get_model_config()
        
        # Load system prompt from file
        system_prompt = get_prompt("appointment_scheduling")
        
        # Use semantic search to find relevant tools for appointment scheduling
        search_query = """
        Appointment scheduling and management tools. Tools for booking medical appointments,
        checking doctor availability, managing reservations, scheduling with medical professionals,
        finding available time slots, and managing medical appointments calendar.
        """
        
        # Get dynamically discovered tools using unified MCP client with semantic search
        dynamic_tools = get_semantic_tools(
            gateway_url=config.mcp_gateway_url,
            aws_region=config.aws_region,
            search_query=search_query,
            agent_type="appointment"
        )
        
        # Create specialized agent with dynamically discovered tools (no guardrails - only orchestrator has them)
        scheduling_agent = Agent(
            system_prompt=system_prompt,
            tools=dynamic_tools,
            model=BedrockModel(
                model_id=model_config.model_id
            )
        )
        
        logger.info(f"🤖 current tools for scheduling agent: {scheduling_agent.tool_names}")

        # Process the request
        response = scheduling_agent(request)
        return str(response)
        
    except Exception as e:
        logger.error(f"Error in appointment scheduling agent: {str(e)}")
        return f"❌ Error en agente de citas: {str(e)}"


# Note: Tool implementations are now dynamically discovered via semantic search
# The AgentCore Gateway provides the actual tool implementations


# Export the tool function
__all__ = ["appointment_scheduling_agent"]
