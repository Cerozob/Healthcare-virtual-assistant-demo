"""
Simplified Healthcare Assistant Agent using Strands framework.
Uses proper Strands tools and configuration management.
"""

import logging
from typing import List, Optional, Dict, Any
from strands import Agent
from strands.models import BedrockModel
from strands_tools import memory, use_llm, use_aws
from appointment_scheduling.agent import appointment_scheduling_agent
from info_retrieval.agent import information_retrieval_agent
from strands.session.s3_session_manager import S3SessionManager
# MCP client is now handled by shared.mcp_client
import os
from datetime import datetime

from shared.config import get_agent_config
from shared.utils import get_logger
from shared.prompts import get_prompt
from shared.models import PatientInfoResponse, SessionContext
from shared.mcp_client import get_healthcare_tools

logger = get_logger(__name__)


class HealthcareAgent:
    """Healthcare Assistant Agent with proper Strands integration."""

    def __init__(self, session_id: str):
        """Initialize the healthcare agent."""
        self.session_id = session_id
        self.config = get_agent_config()
        self.session_manager = None
        self.agent = None
        self._setup_session_manager()
        self._setup_agent()

    def _setup_session_manager(self):
        """Set up S3 session manager for conversation persistence (always S3, always persisted)."""
        logger.info("📁 Setting up S3 session manager")
        logger.info(f"Session ID: {self.session_id}")
        logger.info(f"S3 Bucket: {self.config.session_bucket}")
        logger.info("S3 Prefix: chats/ (hardcoded)")

        try:
            self.session_manager = S3SessionManager(
                session_id=self.session_id,
                bucket=self.config.session_bucket,
                prefix="chats/",  # Always "chats/" as specified
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
        logger.info(f"Configuration: {self.config.model_dump()}")

        # Prepare tools list
        tools = []

        # Add memory tool for knowledge base operations (always available)
        logger.info("📚 Adding knowledge base memory tool")
        os.environ["STRANDS_KNOWLEDGE_BASE_ID"] = self.config.knowledge_base_id
        tools.append(memory)

        # Add LLM tool for structured operations
        tools.append(use_llm)

        # Add specialized agent tools for orchestration

        tools.extend([appointment_scheduling_agent,
                     information_retrieval_agent])
        logger.info("✅ Added specialized agent tools for orchestration")

        # Add MCP Gateway tools (always required)
        logger.info("🌐 Adding MCP Gateway tools")
        mcp_clients = self._setup_mcp_tools()
        if not mcp_clients:
            raise ValueError(
                "No MCP clients available - healthcare agent cannot function without MCP tools")

        tools.extend(mcp_clients)
        logger.info(f"✅ Added {len(mcp_clients)} MCP clients")

        # Create the agent
        system_prompt = self._get_system_prompt()

        logger.info(
            f"🚀 Creating agent with {len(tools)} tools (including MCP clients) and session management")
        self.agent = Agent(
            system_prompt=system_prompt,
            tools=tools,
            model=BedrockModel(
                model_id=self.config.model_id,
                guardrail_id=self.config.guardrail_id,
                guardrail_version=self.config.guardrail_version,
                guardrail_trace="enabled"
            ),
            session_manager=self.session_manager
        )

        logger.info(
            f"🤖 current tools for healthcare agent: {self.agent.tool_names}")

        # Set initial state (will be persisted via session manager)
        self.agent.state.set("session_id", self.session_id)
        self.agent.state.set("language", "es-LATAM")  # Always Spanish LATAM
        self.agent.state.set("current_patient_id", None)
        self.agent.state.set("session_created_at", str(datetime.now()))

        logger.info("✅ Healthcare Agent setup complete")

    def _setup_mcp_tools(self) -> List:
        """Set up MCP Gateway tools using unified MCP client."""
        try:
            logger.info(
                f"🔗 Connecting to AgentCore Gateway: {self.config.mcp_gateway_url}")

            # Import the test function for tool discovery
            from shared.mcp_client import test_agentcore_gateway, create_agentcore_mcp_client

            # Test gateway connection and discover all tools
            logger.info(
                "🔍 Discovering available tools from AgentCore Gateway...")
            test_results = test_agentcore_gateway(
                self.config.mcp_gateway_url,
                self.config.aws_region
            )

            # Log discovered tools for debugging
            if test_results["connection_successful"]:
                logger.info(
                    f"✅ Gateway connection successful - found {test_results['tools_discovered']} tools")

                if test_results["tool_names"]:
                    logger.info("📋 Available tools from AgentCore Gateway:")
                    for i, tool_name in enumerate(test_results["tool_names"], 1):
                        logger.info(f"   {i:2d}. {tool_name}")

                    # Log tool details for semantic search debugging
                    logger.info("🔍 Tool details for semantic search:")
                    for tool in test_results["tool_details"]:
                        logger.info(
                            f"   • {tool['name']}: {tool['description']}")

                    # Check for expected healthcare tools
                    expected_tools = ['patients_api', 'medics_api',
                                      'exams_api', 'reservations_api', 'files_api']
                    found_healthcare_tools = []

                    for expected in expected_tools:
                        matching_tools = [tool for tool in test_results["tool_names"]
                                          if expected in tool or expected.replace('_api', '') in tool]
                        if matching_tools:
                            found_healthcare_tools.extend(matching_tools)

                    if found_healthcare_tools:
                        logger.info(
                            f"✅ Found expected healthcare tools: {found_healthcare_tools}")
                    else:
                        logger.warning(
                            "⚠️ No expected healthcare tools found - check gateway target configuration")

                else:
                    logger.warning("⚠️ No tools discovered from gateway")

                if test_results["semantic_search_available"]:
                    logger.info("✅ Semantic search capability confirmed")
                else:
                    logger.warning("⚠️ Semantic search not available")

            else:
                logger.error(
                    f"❌ Gateway connection failed: {test_results.get('error_message', 'Unknown error')}")

            # Use the unified MCP client to get healthcare tools
            mcp_tools = get_healthcare_tools(
                self.config.mcp_gateway_url,
                self.config.aws_region
            )

            logger.info(
                f"✅ Retrieved {len(mcp_tools)} MCP clients from unified setup")

            # Additional verification: try to list tools from the MCP client
            if mcp_tools:
                try:
                    # Get the first (and likely only) MCP client
                    mcp_client = mcp_tools[0]
                    agentcore_client = create_agentcore_mcp_client(
                        self.config.mcp_gateway_url,
                        self.config.aws_region
                    )

                    with mcp_client:
                        tools_from_client = agentcore_client.list_all_tools(
                            mcp_client)
                        logger.info(
                            f"🔍 Verified: MCP client can access {len(tools_from_client)} tools")

                except Exception as verification_error:
                    logger.warning(
                        f"⚠️ Tool verification failed: {verification_error}")

            return mcp_tools

        except Exception as e:
            logger.error(f"❌ Failed to setup AgentCore MCP tools: {e}")
            logger.error(f"   Gateway URL: {self.config.mcp_gateway_url}")
            logger.error(f"   AWS Region: {self.config.aws_region}")
            logger.error(
                "   Healthcare agent requires MCP tools to function properly")
            # Re-raise the exception with more context
            raise ValueError(
                f"AgentCore MCP Gateway connection failed - agent cannot start: {e}")

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

        logger.info(
            f"💬 Processing prompt with structured output: {prompt[:100]}...")

        try:
            # First get the regular response
            response_message = self.invoke(prompt)

            # Use structured output to extract patient context
            context_extraction_prompt = get_prompt(
                "patient_context_extraction")
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
                        self.agent.state.set(
                            "current_patient_id", structured_result.patient_id)
                        self.agent.state.set(
                            "current_patient_name", structured_result.full_name)
                        self.agent.state.set(
                            "patient_found_in_last_interaction", True)

                        # Convert to dict for response
                        context_dict = {
                            "patient_id": structured_result.patient_id,
                            "patient_name": structured_result.full_name,
                            "has_patient_context": True,
                            "patient_found": True,
                            "patient_data": structured_result.model_dump()
                        }

                        logger.info(
                            f"✅ Structured patient context extracted: {structured_result.patient_id}")
                        return response_message, context_dict

                logger.info("ℹ️ No patient context found in structured output")
                return response_message, None

            except Exception as struct_error:
                logger.warning(
                    f"⚠️ Structured output failed, using fallback: {struct_error}")
                return response_message, None

        except Exception as e:
            logger.error(
                f"❌ Error processing prompt with structured output: {e}")
            return f"Lo siento, ocurrió un error al procesar tu consulta: {str(e)}", None

    def invoke_with_multimodal_support(self, prompt: str, attachments: List[Any]) -> tuple[str, Optional[Dict[str, Any]]]:
        """Invoke the agent with multimodal support for files and images."""
        if not self.agent:
            raise ValueError("Agent not initialized")

        logger.info(
            f"🖼️ Processing multimodal prompt with {len(attachments)} attachments")

        try:
            # Enhanced prompt for multimodal processing
            multimodal_prompt = f"""
            {prompt}
            
            MULTIMODAL PROCESSING INSTRUCTIONS:
            - Analyze any attached images for medical content (X-rays, lab results, etc.)
            - Process document attachments for relevant medical information
            - Correlate file content with patient context when available
            - Provide comprehensive analysis combining text query and file content
            
            Available file processing tools:
            - Use healthcare-files-api for document management
            - Use knowledge base search for medical reference information
            - Use patient tools for context correlation
            """

            # Store attachment information in agent state for tool access
            self.agent.state.set("current_attachments", [
                {
                    "fileName": att.fileName,
                    "fileType": att.fileType,
                    "category": att.category,
                    "s3Key": att.s3Key,
                    "hasContent": bool(att.content),
                    "mimeType": att.mimeType
                } for att in attachments
            ])

            # Process with enhanced multimodal prompt
            response_message = self.invoke(multimodal_prompt)

            # Extract patient context (same as regular processing)
            context_extraction_prompt = get_prompt(
                "patient_context_extraction")
            context_prompt = f"""
            {context_extraction_prompt}
            
            ## Multimodal Conversation to Analyze:
            User Message: {prompt}
            Attachments: {len(attachments)} files
            Assistant Response: {response_message}
            
            Extract patient context from this multimodal conversation.
            """

            try:
                structured_result = self.agent.structured_output(
                    output_model=PatientInfoResponse,
                    prompt=context_prompt
                )

                if structured_result and structured_result.success and structured_result.patient_id:
                    # Update agent state
                    self.agent.state.set(
                        "current_patient_id", structured_result.patient_id)
                    self.agent.state.set(
                        "current_patient_name", structured_result.full_name)
                    self.agent.state.set(
                        "patient_found_in_last_interaction", True)

                    context_dict = {
                        "patient_id": structured_result.patient_id,
                        "patient_name": structured_result.full_name,
                        "has_patient_context": True,
                        "patient_found": True,
                        "patient_data": structured_result.model_dump(),
                        "multimodal_processing": True,
                        "attachments_processed": len(attachments)
                    }

                    logger.info(
                        f"✅ Multimodal patient context extracted: {structured_result.patient_id}")
                    return response_message, context_dict

                logger.info(
                    "ℹ️ No patient context found in multimodal processing")
                return response_message, {
                    "has_patient_context": False,
                    "multimodal_processing": True,
                    "attachments_processed": len(attachments)
                }

            except Exception as struct_error:
                logger.warning(
                    f"⚠️ Multimodal structured output failed: {struct_error}")
                return response_message, {
                    "has_patient_context": False,
                    "multimodal_processing": True,
                    "attachments_processed": len(attachments)
                }

        except Exception as e:
            logger.error(f"❌ Error processing multimodal prompt: {e}")
            return f"Lo siento, ocurrió un error al procesar tu consulta multimodal: {str(e)}", None

    def invoke_with_agentcore_multimodal(self, prompt: str, media_object: Dict[str, Any], attachment_context: List[Any]) -> tuple[str, Optional[Dict[str, Any]]]:
        """Invoke the agent with AgentCore official multimodal format."""
        if not self.agent:
            raise ValueError("Agent not initialized")

        logger.info(
            f"🎯 Processing AgentCore multimodal: {media_object['type']}/{media_object['format']}")

        try:
            # Enhanced prompt for AgentCore multimodal processing
            agentcore_prompt = f"""
            {prompt}
            
            AGENTCORE MULTIMODAL PROCESSING:
            - Media Type: {media_object['type']}
            - Format: {media_object['format']}
            - File: {media_object['metadata']['fileName']}
            - Category: {media_object['metadata']['category']}
            - Base64 content available for AI analysis
            
            PROCESSING INSTRUCTIONS:
            - Analyze the {media_object['type']} content for medical information
            - Extract relevant data (text, measurements, findings, etc.)
            - Correlate with patient context when available
            - Use healthcare tools for data management and lookup
            - Provide comprehensive medical analysis
            
            Available tools for processing:
            - healthcare-files-api for document management
            - healthcare-patients-api for patient correlation
            - Knowledge base search for medical reference
            """

            # Store AgentCore media information in agent state
            self.agent.state.set("agentcore_media", {
                "type": media_object['type'],
                "format": media_object['format'],
                "fileName": media_object['metadata']['fileName'],
                "category": media_object['metadata']['category'],
                "s3Key": media_object['metadata']['s3Key'],
                "hasBase64Content": True
            })

            # Store attachment context
            self.agent.state.set("attachment_context", [
                {
                    "fileName": ctx.fileName,
                    "fileType": ctx.fileType,
                    "category": ctx.category,
                    "s3Key": ctx.s3Key,
                    "hasContent": ctx.hasContent,
                    "mimeType": ctx.mimeType
                } for ctx in attachment_context
            ])

            # Process with AgentCore multimodal prompt
            response_message = self.invoke(agentcore_prompt)

            # Extract patient context with multimodal awareness
            context_extraction_prompt = get_prompt(
                "patient_context_extraction")
            context_prompt = f"""
            {context_extraction_prompt}
            
            ## AgentCore Multimodal Conversation to Analyze:
            User Message: {prompt}
            Media Content: {media_object['type']} file ({media_object['metadata']['fileName']})
            Additional Files: {len(attachment_context)} files
            Assistant Response: {response_message}
            
            Extract patient context from this AgentCore multimodal conversation.
            """

            try:
                structured_result = self.agent.structured_output(
                    output_model=PatientInfoResponse,
                    prompt=context_prompt
                )

                if structured_result and structured_result.success and structured_result.patient_id:
                    # Update agent state
                    self.agent.state.set(
                        "current_patient_id", structured_result.patient_id)
                    self.agent.state.set(
                        "current_patient_name", structured_result.full_name)
                    self.agent.state.set(
                        "patient_found_in_last_interaction", True)

                    context_dict = {
                        "patient_id": structured_result.patient_id,
                        "patient_name": structured_result.full_name,
                        "has_patient_context": True,
                        "patient_found": True,
                        "patient_data": structured_result.model_dump(),
                        "agentcore_multimodal": True,
                        "media_type": media_object['type'],
                        "media_format": media_object['format'],
                        "primary_file": media_object['metadata']['fileName'],
                        "total_attachments": len(attachment_context)
                    }

                    logger.info(
                        f"✅ AgentCore multimodal patient context: {structured_result.patient_id}")
                    return response_message, context_dict

                logger.info(
                    "ℹ️ No patient context found in AgentCore multimodal processing")
                return response_message, {
                    "has_patient_context": False,
                    "agentcore_multimodal": True,
                    "media_type": media_object['type'],
                    "media_format": media_object['format'],
                    "primary_file": media_object['metadata']['fileName'],
                    "total_attachments": len(attachment_context)
                }

            except Exception as struct_error:
                logger.warning(
                    f"⚠️ AgentCore multimodal structured output failed: {struct_error}")
                return response_message, {
                    "has_patient_context": False,
                    "agentcore_multimodal": True,
                    "media_type": media_object['type'],
                    "media_format": media_object['format'],
                    "primary_file": media_object['metadata']['fileName'],
                    "total_attachments": len(attachment_context),
                    "error": "Context extraction failed"
                }

        except Exception as e:
            logger.error(f"❌ Error processing AgentCore multimodal: {e}")
            return f"Lo siento, ocurrió un error al procesar el contenido multimodal: {str(e)}", None

    async def stream_response(self, prompt: str):
        """Stream agent response for text-only queries using AgentCore pattern."""
        if not self.agent:
            raise ValueError("Agent not initialized")

        logger.info(f"🌊 Streaming text response: {prompt[:100]}...")

        try:
            # Use Strands streaming capability - yield events directly like AgentCore docs
            stream = self.agent.stream_async(prompt)

            chunk_count = 0

            async for event in stream:
                chunk_count += 1

                # Log first few events for debugging
                if chunk_count <= 3:
                    logger.info(
                        f"🔍 Raw event #{chunk_count}: {type(event)} = {str(event)[:200]}...")

                # Yield the raw event directly as per AgentCore pattern
                yield event

                logger.debug(f"📤 Yielded raw event #{chunk_count}")

                # Stop excessive logging after first few events
                if chunk_count > 100:  # Safety limit
                    logger.warning(
                        "🛑 Stopping stream after 100 events (safety limit)")
                    break

            logger.info(f"✅ Streaming completed after {chunk_count} events")

        except Exception as e:
            logger.error(f"❌ Error streaming response: {e}")
            yield {
                "type": "error",
                "error": f"Streaming failed: {str(e)}"
            }

    async def stream_with_agentcore_multimodal(self, prompt: str, media_object: Dict[str, Any], attachment_context: List[Any]):
        """Stream agent response for AgentCore multimodal content using AgentCore pattern."""
        if not self.agent:
            raise ValueError("Agent not initialized")

        logger.info(
            f"🌊 Streaming AgentCore multimodal: {media_object['type']}/{media_object['format']}")

        try:
            # Store multimodal context in agent state
            self.agent.state.set("agentcore_media", {
                "type": media_object['type'],
                "format": media_object['format'],
                "fileName": media_object['metadata']['fileName'],
                "category": media_object['metadata']['category'],
                "s3Key": media_object['metadata']['s3Key'],
                "hasBase64Content": True
            })

            # Enhanced prompt for multimodal processing
            agentcore_prompt = f"""
            {prompt}
            
            AGENTCORE MULTIMODAL PROCESSING:
            - Media Type: {media_object['type']}
            - Format: {media_object['format']}
            - File: {media_object['metadata']['fileName']}
            - Category: {media_object['metadata']['category']}
            
            Analyze the {media_object['type']} content and provide comprehensive medical analysis.
            """

            # Stream the response using AgentCore pattern
            stream = self.agent.stream_async(agentcore_prompt)

            chunk_count = 0

            async for event in stream:
                chunk_count += 1

                # Log first few events for debugging
                if chunk_count <= 3:
                    logger.info(
                        f"🔍 Multimodal raw event #{chunk_count}: {type(event)} = {str(event)[:200]}...")

                # Yield the raw event directly as per AgentCore pattern
                yield event

                logger.debug(f"📤 Yielded multimodal raw event #{chunk_count}")

                # Safety limit
                if chunk_count > 100:
                    logger.warning(
                        "🛑 Stopping multimodal stream after 100 events")
                    break

            logger.info(
                f"✅ Multimodal streaming completed after {chunk_count} events")

        except Exception as e:
            logger.error(f"❌ Error streaming multimodal response: {e}")
            yield {
                "type": "error",
                "error": f"Multimodal streaming failed: {str(e)}"
            }

    async def stream_with_multimodal_support(self, prompt: str, attachments: List[Any]):
        """Stream agent response for legacy multimodal attachments using AgentCore pattern."""
        if not self.agent:
            raise ValueError("Agent not initialized")

        logger.info(
            f"🌊 Streaming legacy multimodal: {len(attachments)} attachments")

        try:
            # Store attachment information
            self.agent.state.set("current_attachments", [
                {
                    "fileName": att.fileName,
                    "fileType": att.fileType,
                    "category": att.category,
                    "s3Key": att.s3Key,
                    "hasContent": bool(att.content),
                    "mimeType": att.mimeType
                } for att in attachments
            ])

            # Stream the response using AgentCore pattern
            stream = self.agent.stream_async(prompt)

            chunk_count = 0

            async for event in stream:
                chunk_count += 1

                # Log first few events for debugging
                if chunk_count <= 3:
                    logger.info(
                        f"🔍 Legacy multimodal raw event #{chunk_count}: {type(event)} = {str(event)[:200]}...")

                # Yield the raw event directly as per AgentCore pattern
                yield event

                logger.debug(
                    f"📤 Yielded legacy multimodal raw event #{chunk_count}")

                # Safety limit
                if chunk_count > 100:
                    logger.warning(
                        "🛑 Stopping legacy multimodal stream after 100 events")
                    break

            logger.info(
                f"✅ Legacy multimodal streaming completed after {chunk_count} events")

        except Exception as e:
            logger.error(f"❌ Error streaming legacy multimodal: {e}")
            yield {
                "type": "error",
                "error": f"Legacy multimodal streaming failed: {str(e)}"
            }

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
            "session_prefix": "chats/",  # Always "chats/" as specified
            "session_manager_type": "S3SessionManager",
            "aws_region": self.config.aws_region,
            "conversation_persisted": True  # Always persisted as specified
        }


def create_healthcare_agent(session_id: str) -> HealthcareAgent:
    """Factory function to create a healthcare agent."""
    return HealthcareAgent(session_id)
