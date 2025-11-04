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
from shared.mcp_client import get_appointment_tools, get_semantic_tools, create_agentcore_mcp_client

logger = get_logger(__name__)


def _filter_tools_for_scheduling(all_tools: list, request: str) -> list:
    """
    Filter MCP tools semantically for appointment scheduling tasks.

    Args:
        all_tools: All available MCP tools
        request: The scheduling request

    Returns:
        List of tools relevant for appointment scheduling
    """
    scheduling_keywords = [
        'appointment', 'schedule', 'book', 'reserve', 'calendar', 'availability',
        'slot', 'time', 'date', 'cancel', 'modify', 'reschedule', 'doctor',
        'medic', 'staff', 'resource', 'room', 'clinic'
    ]

    patient_keywords = [
        'patient', 'cedula', 'name', 'id'  # Basic patient info for scheduling
    ]

    filtered_tools = []

    for tool in all_tools:
        tool_name = getattr(tool, 'tool_name', '').lower()
        tool_description = getattr(tool, 'description', '').lower()

        # Include tools that match scheduling or basic patient keywords
        is_scheduling_tool = any(keyword in tool_name or keyword in tool_description
                                 for keyword in scheduling_keywords + patient_keywords)

        if is_scheduling_tool:
            filtered_tools.append(tool)
            logger.info(
                f"   ✅ Included scheduling tool: {getattr(tool, 'tool_name', 'Unknown')}")
        else:
            logger.debug(
                f"   ❌ Excluded tool: {getattr(tool, 'tool_name', 'Unknown')}")

    return filtered_tools


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

        # Create MCP client for AgentCore Gateway
        logger.info(
            f"🔍 Creating MCP client for appointment request: {request[:100]}...")
        logger.info(f"🌐 Gateway URL: {config.mcp_gateway_url}")
        logger.info(f"🌍 AWS Region: {config.aws_region}")

        mcp_client = create_agentcore_mcp_client(
            gateway_url=config.mcp_gateway_url,
            aws_region=config.aws_region
        ).get_mcp_client()

        # Use MCP client within context manager (CRITICAL for proper session management)
        with mcp_client:
            logger.info("🔗 MCP client session started")

            # Get ALL tools from MCP gateway
            all_tools = mcp_client.list_tools_sync()
            logger.info(
                f"📋 Retrieved {len(all_tools)} total tools from MCP gateway")

            # Filter tools semantically for appointment scheduling tasks
            scheduling_tools = _filter_tools_for_scheduling(all_tools, request)
            logger.info(
                f"📅 Filtered to {len(scheduling_tools)} relevant tools for scheduling")

            # Create specialized agent with filtered MCP tools
            logger.info("🤖 Creating appointment scheduling agent...")
            logger.info(f"📋 Model ID: {model_config.model_id}")

            scheduling_agent = Agent(
                system_prompt=system_prompt,
                tools=scheduling_tools,
                model=BedrockModel(
                    model_id=model_config.model_id,
                    temperature=model_config.temperature
                )
            )

            logger.info(
                f"🤖 Agent created with tools: {scheduling_agent.tool_names}")

            # Process the request within the MCP context
            logger.info(f"🔄 Processing request with agent...")
            logger.info(f"📝 Request: {request}")

            try:
                response = scheduling_agent(request)
                logger.info(
                    f"✅ Agent response received (length: {len(str(response))})")
                logger.info(f"📤 Response preview: {str(response)[:200]}...")
                return str(response)
            except Exception as agent_error:
                logger.error(f"❌ Agent processing failed: {agent_error}")
                logger.error(f"🔍 Error type: {type(agent_error).__name__}")
                import traceback
                logger.error(f"🔍 Full traceback: {traceback.format_exc()}")
                raise agent_error

    except Exception as e:
        logger.error(f"Error in appointment scheduling agent: {str(e)}")
        import traceback
        logger.error(f"🔍 Full traceback: {traceback.format_exc()}")
        return f"Lo siento, estoy experimentando un problema técnico con la conexión a las APIs del sistema de salud. Error: {str(e)}"


# Note: Tool implementations are now dynamically discovered via semantic search
# The AgentCore Gateway provides the actual tool implementations


# Export the tool function
__all__ = ["appointment_scheduling_agent"]
