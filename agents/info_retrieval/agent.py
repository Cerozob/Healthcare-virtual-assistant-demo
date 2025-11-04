"""
Information Retrieval Agent using Strands "Agents as Tools" pattern.
Handles patient information queries, patient lookup, and medical document searches.
"""

from typing import Dict, Any, Optional, List

from strands import Agent, tool
from strands.models import BedrockModel

from shared.config import get_agent_config, get_model_config
from shared.utils import get_logger
from shared.prompts import get_prompt
from shared.mcp_client import create_agentcore_mcp_client

logger = get_logger(__name__)



# Strands "Agents as Tools" implementation
@tool
async def information_retrieval_agent(query: str) -> str:
    """
    Process and respond to information retrieval queries using healthcare APIs.

    This agent specializes in:
    - Patient information searches
    - Medical document retrieval from healthcare APIs
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

        # Create MCP client for AgentCore Gateway with semantic tool discovery
        logger.info(f"🔍 Creating MCP client for query: {query[:100]}...")
        logger.info(f"🌐 Gateway URL: {config.mcp_gateway_url}")
        logger.info(f"🌍 AWS Region: {config.aws_region}")
                
        agentcore_client = create_agentcore_mcp_client(
            gateway_url=config.mcp_gateway_url,
            aws_region=config.aws_region
        )
        
        # Use semantic search to get relevant tools for the query
        logger.info("🔍 Using semantic search to discover relevant tools...")
        
        # Create a semantic search query that includes patient lookup context
        semantic_query = f"""
        Information retrieval and patient search query: {query}
        
        Need tools for: patient information lookup, patient search by name/email/phone/cedula, 
        medical records retrieval, patient data access, healthcare information queries.
        
        Specifically need patient lookup capabilities for comprehensive patient identification.
        """
        
        try:
            info_retrieval_tools = agentcore_client.get_semantic_tools(
                semantic_query, 
                "information_retrieval"
            )
            logger.info(f"🔍 Semantic search found {len(info_retrieval_tools)} relevant tools")
            
        except Exception as semantic_error:
            logger.warning(f"⚠️ Semantic search failed: {semantic_error}")
            logger.info("🔄 Falling back to all available tools...")
            
            # Fallback: get all tools if semantic search fails
            mcp_client = agentcore_client.get_mcp_client()
            with mcp_client:
                info_retrieval_tools = mcp_client.list_tools_sync()
                logger.info(f"🔍 Fallback: using all {len(info_retrieval_tools)} available tools")
            
        # Create specialized agent with semantically discovered tools
        logger.info("� Creating infoirmation retrieval agent...")
        logger.info(f"📋 Model ID: {model_config.model_id}")
        logger.info(f"� Model Tempermature: {model_config.temperature}")
        
        # Log discovered tools for debugging
        logger.info(f"🔧 Available tools for agent:")
        for i, tool in enumerate(info_retrieval_tools, 1):
            tool_name = getattr(tool, 'tool_name', 'Unknown')
            tool_desc = getattr(tool, 'description', 'No description')[:100]
            logger.info(f"   {i}. {tool_name}: {tool_desc}")
        
        # Create agent with MCP client context management
        mcp_client = agentcore_client.get_mcp_client()
        
        with mcp_client:
            info_agent = Agent(
                system_prompt=system_prompt,
                tools=info_retrieval_tools,
                model=BedrockModel(
                    model_id=model_config.model_id,
                    temperature=model_config.temperature
                )
            )
            
            logger.info(f"🤖 Agent created with {len(info_agent.tool_names)} tools: {info_agent.tool_names}")
            
            # Process the query within the MCP context
            logger.info(f"🔄 Processing query with agent...")
            logger.info(f"� Query: l{query}")
            
            try:
                response = info_agent(query)
                logger.info(f"✅ Agent response received (length: {len(str(response))})")
                logger.info(f"📤 Response preview: {str(response)[:200]}...")
                return str(response)
            except Exception as agent_error:
                logger.error(f"❌ Agent processing failed: {agent_error}")
                logger.error(f"🔍 Error type: {type(agent_error).__name__}")
                import traceback
                logger.error(f"🔍 Full traceback: {traceback.format_exc()}")
                
                # Provide specific error handling for tool invocation failures
                error_message = str(agent_error).lower()
                if "tool" in error_message and ("not found" in error_message or "unavailable" in error_message):
                    return "Lo siento, algunas herramientas de búsqueda de pacientes no están disponibles en este momento. Por favor, intenta nuevamente o contacta al soporte técnico."
                elif "timeout" in error_message or "connection" in error_message:
                    return "Lo siento, hay un problema de conectividad con el sistema de información médica. Por favor, intenta nuevamente en unos momentos."
                elif "permission" in error_message or "access" in error_message:
                    return "Lo siento, no tengo permisos suficientes para acceder a la información solicitada. Por favor, contacta al administrador del sistema."
                elif "rate" in error_message or "limit" in error_message:
                    return "Lo siento, el sistema está experimentando alta demanda. Por favor, intenta nuevamente en unos momentos."
                else:
                    return f"Lo siento, estoy experimentando un problema técnico con la conexión a las APIs del sistema de salud. Error: {str(agent_error)}"

    except Exception as e:
        logger.error(f"Error in information retrieval agent: {str(e)}")
        import traceback
        logger.error(f"🔍 Full traceback: {traceback.format_exc()}")
        return f"Lo siento, estoy experimentando un problema técnico con la conexión a las APIs del sistema de salud. Error: {str(e)}"


# Note: Tool implementations are now dynamically discovered via semantic search
# The AgentCore Gateway provides the actual tool implementations


# Export the tool function
__all__ = ["information_retrieval_agent"]
