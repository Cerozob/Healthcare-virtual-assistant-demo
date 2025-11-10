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

        # Create AgentCore MCP client wrapper for semantic tool discovery
        logger.info(
            f"🔍 Creating MCP client for appointment request: {request[:100]}...")
        logger.info(f"🌐 Gateway URL: {config.mcp_gateway_url}")
        logger.info(f"🌍 AWS Region: {config.aws_region}")
        
        # Create AgentCore MCP client wrapper for semantic tool discovery
        agentcore_client = create_agentcore_mcp_client(
            gateway_url=config.mcp_gateway_url,
            aws_region=config.aws_region
        )
        
        # Use semantic search to find only the tools needed for appointment scheduling
        # This reduces token usage significantly by avoiding loading all 6 Lambda APIs
        logger.info("🔍 Using semantic search to find appointment scheduling tools...")
        
        # Create a focused semantic query for appointment scheduling tools
        # This will match against tool names and descriptions in AgentCore Gateway
        # Note: Includes basic patient lookup for the scheduling workflow
        semantic_query = """
        Appointment scheduling and medical resource management tools:
        - Appointment and reservation CRUD operations (create, read, update, delete appointments)
        - Check appointment availability and time slots
        - Doctor and medical staff information, schedules, and availability
        - Medical exam types and information for scheduling
        - Basic patient lookup by name or ID (for identifying patient_id during scheduling)
        
        DO NOT include: advanced patient search, medical files, document analysis, patient medical history
        """
        
        try:
            scheduling_tools = agentcore_client.get_semantic_tools(
                semantic_query,
                "appointment_scheduling"
            )
            logger.info(f"✅ Semantic search found {len(scheduling_tools)} tools for appointment scheduling")
            
            # Log which tools were found
            for i, tool in enumerate(scheduling_tools, 1):
                tool_name = getattr(tool, 'tool_name', 'Unknown')
                tool_desc = getattr(tool, 'description', 'No description')[:100]
                logger.info(f"   {i}. {tool_name}: {tool_desc}")
            
        except Exception as semantic_error:
            logger.error(f"❌ Semantic search failed: {semantic_error}")
            logger.error("This is critical - cannot proceed without semantic tool discovery")
            raise ValueError(f"Failed to discover appointment scheduling tools: {semantic_error}")
        
        # Get MCP client for context management
        mcp_client = agentcore_client.get_mcp_client()
        
        # Use MCP client within context manager (CRITICAL for proper session management)
        with mcp_client:
            logger.info("🔗 MCP client session started")

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
