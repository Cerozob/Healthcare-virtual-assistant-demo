"""
Unified MCP Client for AgentCore Gateway.
Provides a centralized way to connect to AgentCore Gateway and discover tools with semantic search.
"""

from httpx_auth_awssigv4 import SigV4Auth
import logging
from typing import List, Optional, Dict, Any
import boto3
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from urllib.parse import urlparse
import asyncio
import json
import time
import random
from threading import Lock

from .utils import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Simple rate limiter for AgentCore Gateway (5 TPS limit).
    """
    
    def __init__(self, max_calls_per_second: float = 2.0):  # Use 2 TPS to be very conservative
        self.max_calls_per_second = max_calls_per_second
        self.min_interval = 1.0 / max_calls_per_second
        self.last_call_time = 0.0
        self.lock = Lock()
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limits with jitter."""
        with self.lock:
            current_time = time.time()
            time_since_last_call = current_time - self.last_call_time
            
            if time_since_last_call < self.min_interval:
                sleep_time = self.min_interval - time_since_last_call
                # Add jitter to prevent thundering herd
                jitter = random.uniform(0, 0.1)  # 0-100ms jitter
                total_sleep = sleep_time + jitter
                logger.debug(f"⏳ Rate limiting: waiting {total_sleep:.2f}s (base: {sleep_time:.2f}s, jitter: {jitter:.2f}s)")
                time.sleep(total_sleep)
            
            self.last_call_time = time.time()


# Global rate limiter instance
_rate_limiter = RateLimiter(max_calls_per_second=2.0)


class AgentCoreMCPClient:
    """
    Unified MCP client for connecting to AgentCore Gateway.
    Handles authentication, connection, and tool discovery for all agents.
    """

    def __init__(self, gateway_url: str, aws_region: str):
        """
        Initialize the AgentCore MCP client.

        Args:
            gateway_url: AgentCore Gateway MCP endpoint URL
            aws_region: AWS region for SigV4 authentication
        """
        self.gateway_url = gateway_url
        self.aws_region = aws_region
        self._mcp_client = None

        logger.info(f"🔧 Initializing AgentCore MCP Client")
        logger.info(f"   Gateway URL: {gateway_url}")
        logger.info(f"   AWS Region: {aws_region}")

    def create_streamable_http_transport(self):
        """
        Create a streamable HTTP transport with AWS SigV4 authentication.

        Returns:
            Configured streamable HTTP client for AgentCore Gateway
        """
        logger.info(
            f"🔐 Creating HTTPX-based transport for {self.gateway_url}")
        logger.info(f"   AWS Region: {self.aws_region}")

        # fetch temporary credentials from AWS STS service
        credentials = boto3.Session().get_credentials()

        # creating a callable for httpx library
        auth = SigV4Auth(
            access_key=credentials.access_key,
            secret_key=credentials.secret_key,
            token=credentials.token,
            service="bedrock-agentcore",
            region=self.aws_region
        )

        logger.info("✅ Created AWS SigV4 authentication")

        # Create streamable HTTP client with SigV4 authentication
        streamable_client = streamablehttp_client(
            self.gateway_url,
            auth=auth,
        )

        logger.info(
            "✅ Created streamable HTTP transport with SigV4 authentication")

        return streamable_client

    def get_mcp_client(self) -> MCPClient:
        """
        Get or create the MCP client for AgentCore Gateway.

        Returns:
            MCPClient configured for AgentCore Gateway with SigV4 authentication
        """
        if self._mcp_client is None:
            try:
                logger.info("🔗 Creating MCP client for AgentCore Gateway")
                
                # Add rate limiting before client creation
                _rate_limiter.wait_if_needed()

                # Create MCP client with AgentCore Gateway
                # The gateway will expose tools from all targets with proper naming:
                # - healthcare-patients-api__patients_api
                # - healthcare-medics-api__medics_api
                # - healthcare-exams-api__exams_api
                # - healthcare-reservations-api__reservations_api
                # - healthcare-files-api__files_api
                self._mcp_client = MCPClient(
                    transport_callable=lambda: self.create_streamable_http_transport()
                )

                logger.info("✅ MCP client created successfully")
                logger.info(
                    "   Gateway will expose tools from all targets with naming: ${target_name}__${tool_name}")

            except Exception as e:
                logger.error(f"❌ Failed to create MCP client: {e}")
                raise ValueError(
                    f"AgentCore MCP Gateway connection failed: {e}")
        return self._mcp_client

    def get_semantic_tools(self, search_query: str, agent_type: str = "healthcare") -> List:
        """
        Get tools using semantic search with AgentCore Gateway's built-in search.

        Args:
            search_query: Natural language description of desired tools
            agent_type: Type of agent requesting tools

        Returns:
            List of actual tool objects from the MCP client
        """
        logger.info(f"🔍 === SEMANTIC TOOL DISCOVERY START ===")
        logger.info(f"🎯 Agent type: {agent_type}")
        logger.info(f"🔍 Search query: {search_query[:100]}...")
        logger.info(f"🌐 Gateway URL: {self.gateway_url}")
        logger.info(f"🌍 AWS Region: {self.aws_region}")

        try:
            logger.info("🔗 Getting MCP client...")
            mcp_client = self.get_mcp_client()
            logger.info("✅ MCP client obtained successfully")

            with mcp_client:
                # Perform semantic search to understand what tools are available
                # This helps the gateway understand the context for better tool selection
                logger.info("🔍 Attempting semantic search...")
                try:
                    _rate_limiter.wait_if_needed()  # Rate limit before semantic search
                    logger.info("⏳ Rate limiting complete, calling semantic search...")
                    
                    search_result = mcp_client.call_tool_sync(
                        tool_use_id=f"semantic-search-{hash(search_query)}",
                        name="x_amz_bedrock_agentcore_search",
                        arguments={"query": search_query}
                    )
                    logger.info("✅ Semantic search completed successfully")
                    logger.info(f"🔍 Search result type: {type(search_result)}")
                    logger.info(f"🔍 Search result preview: {str(search_result)[:200]}...")
                except Exception as search_error:
                    logger.error(f"❌ Semantic search failed: {search_error}")
                    logger.error(f"🔍 Error type: {type(search_error).__name__}")
                    # Check if it's a rate limit error
                    if "429" in str(search_error) or "Too Many Requests" in str(search_error):
                        logger.warning("⚠️ Rate limit hit during semantic search - continuing without search")
                    else:
                        logger.error(f"🔍 Unexpected search error: {search_error}")
                    logger.info("🔄 Continuing with standard tool discovery")

                # Get the actual tools from the MCP client
                logger.info("📋 Listing all available tools...")
                tools = self.list_all_tools(mcp_client)
                logger.info(f"✅ Retrieved {len(tools)} tools from MCP client")
                
                # Log detailed tool information for debugging
                if tools:
                    logger.info("🔧 === AVAILABLE TOOLS DETAILS ===")
                    for i, tool in enumerate(tools, 1):
                        tool_name = getattr(tool, 'tool_name', 'Unknown')
                        tool_desc = getattr(tool, 'description', 'No description')
                        logger.info(f"   {i}. {tool_name}")
                        logger.info(f"      Description: {tool_desc}")
                        if hasattr(tool, 'input_schema'):
                            schema = getattr(tool, 'input_schema', {})
                            logger.info(f"      Schema keys: {list(schema.keys()) if isinstance(schema, dict) else 'Not a dict'}")
                    logger.info("🔧 === END TOOLS DETAILS ===")
                else:
                    logger.warning("⚠️ No tools retrieved from MCP client")
                
                logger.info(f"🔍 === SEMANTIC TOOL DISCOVERY END ===")
                return tools

        except Exception as e:
            logger.error(f"❌ Failed to get semantic tools for {agent_type} agent: {e}")
            logger.error(f"🔍 Error type: {type(e).__name__}")
            import traceback
            logger.error(f"🔍 Full traceback: {traceback.format_exc()}")
            logger.warning("🔄 Falling back to empty tool list")
            return []


    def list_all_tools(self, client: MCPClient) -> List:
        """
        List all tools with support for pagination.
        
        Args:
            client: MCP client instance
            
        Returns:
            List of all available tools from the gateway
        """
        logger.info("🔍 Discovering all available tools from AgentCore Gateway...")
        
        more_tools = True
        tools = []
        pagination_token = None
        
        try:
            while more_tools:
                # Rate limit each pagination request
                _rate_limiter.wait_if_needed()
                
                tmp_tools = client.list_tools_sync(pagination_token=pagination_token)
                tools.extend(tmp_tools)
                
                if tmp_tools.pagination_token is None:
                    more_tools = False
                else:
                    more_tools = True
                    pagination_token = tmp_tools.pagination_token
                    
            logger.info(f"✅ Found {len(tools)} tools from AgentCore Gateway")
            
            # Log detailed tool information
            for i, tool in enumerate(tools, 1):
                logger.info(f"   {i}. {tool.tool_name}")
                if hasattr(tool, 'description') and tool.description:
                    logger.info(f"      Description: {tool.description}")
                    
            return tools
            
        except Exception as e:
            # Check for rate limiting errors
            if "429" in str(e) or "Too Many Requests" in str(e):
                logger.warning(f"⚠️ Rate limit hit during tool discovery: {e}")
                logger.info("🔄 This is expected under heavy load - tools will be discovered on demand")
                return []
            else:
                logger.error(f"❌ Failed to list tools: {e}")
                return []

def create_agentcore_mcp_client(gateway_url: str, aws_region: str) -> AgentCoreMCPClient:
    """
    Factory function to create an AgentCore MCP client.

    Args:
        gateway_url: AgentCore Gateway MCP endpoint URL
        aws_region: AWS region for SigV4 authentication

    Returns:
        Configured AgentCoreMCPClient instance
    """
    return AgentCoreMCPClient(gateway_url, aws_region)


def get_healthcare_tools(gateway_url: str, aws_region: str) -> List:
    """
    Convenience function to get tools for healthcare agents using semantic search.

    Args:
        gateway_url: AgentCore Gateway MCP endpoint URL
        aws_region: AWS region for SigV4 authentication

    Returns:
        List of actual tool objects for healthcare operations
    """
    client = create_agentcore_mcp_client(gateway_url, aws_region)

    # Use semantic search with healthcare-specific query
    healthcare_query = """
    Healthcare management tools for patient information, medical records, appointments, 
    medical professionals, medical exams, and medical files. Tools for managing patients, 
    doctors, reservations, medical documents, and healthcare operations.
    """

    return client.get_semantic_tools(healthcare_query, "healthcare")


def get_appointment_tools(gateway_url: str, aws_region: str) -> List:
    """
    Convenience function to get tools for appointment scheduling agents using semantic search.

    Args:
        gateway_url: AgentCore Gateway MCP endpoint URL
        aws_region: AWS region for SigV4 authentication

    Returns:
        List of actual tool objects for appointment operations
    """
    client = create_agentcore_mcp_client(gateway_url, aws_region)

    # Use semantic search with appointment-specific query
    appointment_query = """
    Appointment scheduling and management tools. Tools for booking medical appointments,
    checking doctor availability, managing reservations, scheduling with medical professionals,
    finding available time slots, and managing medical appointments calendar.
    """

    return client.get_semantic_tools(appointment_query, "appointment")


def get_patient_info_tools(gateway_url: str, aws_region: str) -> List:
    """
    Convenience function to get tools for patient information agents using semantic search.

    Args:
        gateway_url: AgentCore Gateway MCP endpoint URL
        aws_region: AWS region for SigV4 authentication

    Returns:
        List of actual tool objects for patient information operations
    """
    client = create_agentcore_mcp_client(gateway_url, aws_region)

    # Use semantic search with patient-specific query
    patient_query = """
    Patient information and management tools. Tools for searching patients, 
    retrieving patient records, updating patient information, managing patient data,
    and accessing patient medical history.
    """

    return client.get_semantic_tools(patient_query, "patient_info")


def get_medical_records_tools(gateway_url: str, aws_region: str) -> List:
    """
    Convenience function to get tools for medical records agents using semantic search.

    Args:
        gateway_url: AgentCore Gateway MCP endpoint URL
        aws_region: AWS region for SigV4 authentication

    Returns:
        List of actual tool objects for medical records operations
    """
    client = create_agentcore_mcp_client(gateway_url, aws_region)

    # Use semantic search with medical records query
    records_query = """
    Medical records and document management tools. Tools for managing medical files,
    uploading documents, classifying medical records, searching medical documents,
    and accessing patient medical history and exam results.
    """

    return client.get_semantic_tools(records_query, "medical_records")


def get_semantic_tools(gateway_url: str, aws_region: str, search_query: str, agent_type: str = "healthcare") -> List:
    """
    Convenience function to get tools using custom semantic search query.

    Args:
        gateway_url: AgentCore Gateway MCP endpoint URL
        aws_region: AWS region for SigV4 authentication
        search_query: Natural language description of desired tools
        agent_type: Type of agent requesting tools

    Returns:
        List of actual tool objects matching the semantic search
    """
    client = create_agentcore_mcp_client(gateway_url, aws_region)
    return client.get_semantic_tools(search_query, agent_type)

