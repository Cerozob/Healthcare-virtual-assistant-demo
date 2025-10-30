"""
Simplified Healthcare Assistant Agent using Strands framework.
Uses proper Strands tools and configuration management.
"""

import logging
from typing import List, Optional, Dict, Any
from strands import Agent
from strands_tools import memory, use_llm, use_aws
from strands.session.s3_session_manager import S3SessionManager
import boto3
import os
from datetime import datetime

from config import get_config
from shared.utils import get_logger
from shared.prompts import get_prompt
from shared.models import PatientInfoResponse, SessionContext
from shared.mcp_sigv4_client import create_sigv4_mcp_tools, test_sigv4_connection

logger = get_logger(__name__)


class HealthcareAgent:
    """Healthcare Assistant Agent with proper Strands integration."""

    def __init__(self, session_id: str):
        """Initialize the healthcare agent."""
        self.session_id = session_id
        self.config = get_config()
        self.session_manager = None
        self.agent = None
        self._setup_session_manager()
        self._setup_agent()

    def _setup_session_manager(self):
        """Set up S3 session manager for conversation persistence."""
        logger.info("📁 Setting up S3 session manager")
        logger.info(f"Session ID: {self.session_id}")
        logger.info(f"S3 Bucket: {self.config.session_bucket}")
        logger.info(f"S3 Prefix: {self.config.session_prefix}")

        try:
            self.session_manager = S3SessionManager(
                session_id=self.session_id,
                bucket=self.config.session_bucket,
                prefix=self.config.session_prefix,
                region_name=self.config.aws_region
            )
            logger.info("✅ S3 session manager created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create S3 session manager: {e}")
            raise ValueError(f"Session manager setup failed: {e}")

    def _setup_agent(self):
        """Set up the Strands agent with proper tools."""
        logger.info("🤖 Setting up Healthcare Agent")
        logger.info(f"Session ID: {self.session_id}")
        logger.info(f"Configuration: {self.config.to_dict()}")

        # Prepare tools list
        tools = []

        # Add memory tool for knowledge base operations (always available)
        logger.info("📚 Adding knowledge base memory tool")
        os.environ["STRANDS_KNOWLEDGE_BASE_ID"] = self.config.bedrock_knowledge_base_id
        tools.append(memory)

        # Add LLM tool for structured operations
        tools.append(use_llm)

        # Add MCP Gateway tools (always required)
        logger.info("🌐 Adding MCP Gateway tools")
        mcp_tools = self._setup_mcp_tools()
        if not mcp_tools:
            raise ValueError("No MCP tools available - healthcare agent cannot function without MCP tools")
        
        tools.extend(mcp_tools)
        logger.info(f"✅ Added {len(mcp_tools)} MCP tools")

        # Create the agent
        system_prompt = self._get_system_prompt()

        logger.info(
            f"🚀 Creating agent with {len(tools)} tools and session management")
        self.agent = Agent(
            system_prompt=system_prompt,
            tools=tools,
            model_id=self.config.bedrock_model_id,
            session_manager=self.session_manager
        )

        # Set initial state (will be persisted via session manager)
        self.agent.state.set("session_id", self.session_id)
        self.agent.state.set("language", "es-LATAM")  # Always Spanish LATAM
        self.agent.state.set("current_patient_id", None)
        self.agent.state.set("session_created_at", str(datetime.now()))

        logger.info("✅ Healthcare Agent setup complete")

    def _setup_mcp_tools(self) -> List:
        """Set up MCP Gateway tools with SigV4 authentication."""
        try:
            logger.info(
                f"🔗 Connecting to MCP Gateway with SigV4: {self.config.mcp_gateway_url}")

            # Test the connection first
            if not test_sigv4_connection(self.config.mcp_gateway_url, self.config.aws_region):
                raise ValueError("SigV4 connection test failed")

            # Create SigV4-authenticated MCP tools
            tools = create_sigv4_mcp_tools(
                self.config.mcp_gateway_url, 
                self.config.aws_region
            )

            logger.info(f"✅ Retrieved {len(tools)} SigV4-authenticated tools from MCP Gateway")
            return tools

        except Exception as e:
            logger.error(f"❌ Failed to setup SigV4 MCP tools: {e}")
            logger.error(f"   Gateway URL: {self.config.mcp_gateway_url}")
            logger.error(f"   AWS Region: {self.config.aws_region}")
            logger.error("   Healthcare agent requires MCP tools to function properly")
            # Re-raise the exception with more context
            raise ValueError(f"SigV4 MCP Gateway connection failed - agent cannot start: {e}")

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the healthcare agent."""
        return get_prompt("healthcare")

    def invoke(self, prompt: str) -> str:
        """Invoke the agent with a prompt."""
        if not self.agent:
            raise ValueError("Agent not initialized")

        logger.info(f"💬 Processing prompt: {prompt[:100]}...")

        try:
            # Use the agent to process the prompt
            response = self.agent(prompt)

            # Extract the message from the response
            if hasattr(response, 'message'):
                message = str(response.message)
            else:
                message = str(response)

            logger.info(f"✅ Response generated: {len(message)} characters")
            return message

        except Exception as e:
            logger.error(f"❌ Error processing prompt: {e}")
            return f"Lo siento, ocurrió un error al procesar tu consulta: {str(e)}"

    def invoke_with_structured_output(self, prompt: str) -> tuple[str, Optional[Dict[str, Any]]]:
        """Invoke the agent with structured output for patient context."""
        if not self.agent:
            raise ValueError("Agent not initialized")

        logger.info(f"💬 Processing prompt with structured output: {prompt[:100]}...")

        try:
            # First get the regular response
            response_message = self.invoke(prompt)
            
            # Use structured output to extract patient context
            context_extraction_prompt = get_prompt("patient_context_extraction")
            context_prompt = f"""
            {context_extraction_prompt}
            
            ## Conversation to Analyze:
            User Message: {prompt}
            Assistant Response: {response_message}
            
            Extract patient context from this conversation.
            """
            
            try:
                # Use structured output to get patient context
                structured_result = self.agent.structured_output(
                    output_model=PatientInfoResponse,
                    prompt=context_prompt
                )
                
                if structured_result and structured_result.success:
                    # Update agent state with structured context
                    if structured_result.patient_id:
                        self.agent.state.set("current_patient_id", structured_result.patient_id)
                        self.agent.state.set("current_patient_name", structured_result.full_name)
                        self.agent.state.set("patient_found_in_last_interaction", True)
                        
                        # Convert to dict for response
                        context_dict = {
                            "patient_id": structured_result.patient_id,
                            "patient_name": structured_result.full_name,
                            "has_patient_context": True,
                            "patient_found": True,
                            "patient_data": structured_result.model_dump()
                        }
                        
                        logger.info(f"✅ Structured patient context extracted: {structured_result.patient_id}")
                        return response_message, context_dict
                
                logger.info("ℹ️ No patient context found in structured output")
                return response_message, None
                
            except Exception as struct_error:
                logger.warning(f"⚠️ Structured output failed, using fallback: {struct_error}")
                return response_message, None

        except Exception as e:
            logger.error(f"❌ Error processing prompt with structured output: {e}")
            return f"Lo siento, ocurrió un error al procesar tu consulta: {str(e)}", None

    def get_patient_context(self) -> Dict[str, Any]:
        """Get current patient context from agent state."""
        if not self.agent:
            return {"has_patient_context": False}

        return {
            "patient_id": self.agent.state.get("current_patient_id"),
            "patient_name": self.agent.state.get("current_patient_name"),
            "has_patient_context": bool(self.agent.state.get("current_patient_id")),
            "patient_found": bool(self.agent.state.get("patient_found_in_last_interaction")),
            "patient_data": self.agent.state.get("current_patient_data")
        }

    def reset_patient_context(self):
        """Reset patient context in agent state."""
        if self.agent:
            self.agent.state.set("current_patient_id", None)
            self.agent.state.set("current_patient_name", None)
            self.agent.state.set("current_patient_data", None)
            self.agent.state.set("patient_found_in_last_interaction", False)
            logger.info("🔄 Patient context reset")

    def get_session_info(self) -> Dict[str, Any]:
        """Get session information."""
        return {
            "session_id": self.session_id,
            "session_bucket": self.config.session_bucket,
            "session_prefix": self.config.session_prefix,
            "session_manager_type": "S3SessionManager",
            "aws_region": self.config.aws_region,
            "conversation_persisted": True
        }


def create_healthcare_agent(session_id: str) -> HealthcareAgent:
    """Factory function to create a healthcare agent."""
    return HealthcareAgent(session_id)
