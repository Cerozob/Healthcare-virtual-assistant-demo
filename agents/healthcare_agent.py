"""
Healthcare Agent - Simplified Version with Strands Multimodal Support
Single streaming function with multimodal support and short-term memory
"""

import logging
import json
import base64
from typing import Optional, List, Dict, Any, AsyncGenerator

from datetime import datetime
from strands import Agent
from strands.models import BedrockModel
from strands.agent.agent_result import AgentResult
from strands.types.content import Message, ContentBlock
from strands.telemetry.metrics import EventLoopMetrics
from bedrock_agentcore.memory import MemoryClient
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
from appointment_scheduling.agent import appointment_scheduling_agent
from info_retrieval.agent import information_retrieval_agent
from shared.config import get_agent_config
from shared.memory_logger import MemoryOperationLogger, MemoryDebugger
from shared.models import HealthcareAgentResponse
from tools.multimodal_uploader import create_multimodal_uploader, MultimodalUploader
from prompts import get_prompt

logger = logging.getLogger("healthcare_agent")

# CloudWatch structured logging helper


def log_memory_event(event_type: str, session_id: str, data: Dict[str, Any] = None):
    """Log structured memory events for CloudWatch analysis."""
    memory_logger = logging.getLogger("healthcare_agent.memory")

    # Create structured log message
    log_data = {
        "event_type": event_type,
        "session_id": session_id,
        **(data or {})
    }

    # Format as key=value pairs for better CloudWatch parsing
    log_parts = [f"{k}={v}" for k, v in log_data.items()]
    memory_logger.info(f"🧠 Memory operation | {' | '.join(log_parts)}")


def log_session_event(event_type: str, session_id: str, data: Dict[str, Any] = None):
    """Log structured session events for CloudWatch analysis."""
    session_logger = logging.getLogger("healthcare_agent.session")

    # Create structured log message
    log_data = {
        "event_type": event_type,
        "session_id": session_id,
        **(data or {})
    }

    # Format as key=value pairs for better CloudWatch parsing
    log_parts = [f"{k}={v}" for k, v in log_data.items()]
    session_logger.info(f"🔄 Session event | {' | '.join(log_parts)}")


def log_guardrail_event(event_type: str, session_id: str, data: Dict[str, Any] = None):
    """Log structured guardrail detection events for AgentCore monitoring."""
    guardrail_logger = logging.getLogger("healthcare_agent.guardrail")

    # Create structured log message
    log_data = {
        "event_type": event_type,
        "session_id": session_id,
        **(data or {})
    }

    # Format as key=value pairs for better CloudWatch parsing
    log_parts = [f"{k}={v}" for k, v in log_data.items()]
    guardrail_logger.info(f"🛡️ Guardrail event | {' | '.join(log_parts)}")


class HealthcareAgent:
    """Simplified Healthcare Agent with unified streaming and multimodal support."""

    def __init__(self, config, session_id: str):
        self.config = config
        self.session_id = session_id
        self.agent: Optional[Agent] = None
        self.session_manager: Optional[AgentCoreMemorySessionManager] = None
        self.multimodal_uploader: Optional[MultimodalUploader] = None

    def initialize(self) -> None:
        """Initialize the healthcare agent."""
        logger.info(
            f"🏥 Initializing Healthcare Agent | session_id={self.session_id}")

        # Log initialization start
        log_session_event("INIT_START", self.session_id, {
            "session_id_length": len(self.session_id),
            "memory_id": self.config.agentcore_memory_id,
            "model_id": self.config.model_id
        })

        try:
            # Setup session manager
            self._setup_session_manager()

            # Setup multimodal uploader
            self._setup_multimodal_uploader()

            # Setup all tools (Strands tools + MCP tools + specialized agents)
            tools = self._setup_all_tools()

            # Create a Bedrock model instance with full guardrail tracing
            bedrock_model = BedrockModel(
                model_id=self.config.model_id,
                temperature=self.config.model_temperature,
                # top_p=self.config.model_top_p,
                guardrail_id=self.config.guardrail_id,
                guardrail_version=self.config.guardrail_version,
                guardrail_trace="enabled_full",  # Enable complete guardrail activity logging for AgentCore
                guardrail_stream_processing_mode="async",  # Use async processing to avoid blocking
                guardrail_redact_input=False,  # CRITICAL: Don't redact input - allow PII for patient lookup
                guardrail_redact_output=False,  # Don't redact output - let ANONYMIZE action in guardrail handle it
                guardrail_redact_input_message="[Entrada procesada de forma segura]",
                guardrail_redact_output_message="[Información sensible protegida]"
            )

            logger.info(f"🛡️ Guardrail configured: ID={self.config.guardrail_id}, Version={self.config.guardrail_version}")
            logger.info("🔍 Guardrail tracing: ENABLED_FULL (detection without blocking)")

            # Create the agent
            self.agent = Agent(
                model=bedrock_model,
                system_prompt=get_prompt("healthcare"),
                tools=tools,
                session_manager=self.session_manager
            )

            # Set initial state
            self.agent.state.set("session_id", self.session_id)

            logger.info(
                f"✅ Healthcare Agent initialized | session_id={self.session_id} | tools_count={len(self.agent.tool_names)}")
            logger.debug(
                f"🤖 Available tools | session_id={self.session_id} | tools={self.agent.tool_names}")

            # Log successful initialization
            log_session_event("INIT_SUCCESS", self.session_id, {
                "tools_count": len(self.agent.tool_names),
                "tools": self.agent.tool_names,
                "session_manager_type": type(self.session_manager).__name__
            })

        except Exception as e:
            logger.error(f"❌ Failed to initialize Healthcare Agent: {e}")

            # Log initialization failure
            log_session_event("INIT_FAILURE", self.session_id, {
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise

    def _setup_session_manager(self) -> None:
        """Setup AgentCore Memory session manager with proper configuration."""
        try:
            # Generate a user-specific actor ID (not session-specific)
            # This allows memory to persist across sessions for the same user
            actor_id = f"healthcare_user_{datetime.now().strftime('%Y%m%d')}"

            # Log memory setup start
            log_memory_event("SETUP_START", self.session_id, {
                "memory_id": self.config.agentcore_memory_id,
                "actor_id": actor_id,
                "session_id": self.session_id
            })

            # Create memory configuration with proper parameters
            agentcore_memory_config = AgentCoreMemoryConfig(
                memory_id=self.config.agentcore_memory_id,
                session_id=self.session_id,
                actor_id=actor_id,
                retrieval_config={
                    # Configure retrieval for different memory namespaces
                    "preferences": RetrievalConfig(
                        top_k=5,
                        relevance_score=0.7
                    ),
                    "facts": RetrievalConfig(
                        top_k=10,
                        relevance_score=0.6
                    ),
                    "summaries": RetrievalConfig(
                        top_k=3,
                        relevance_score=0.8
                    )
                }
            )

            # Create session manager
            self.session_manager = AgentCoreMemorySessionManager(
                agentcore_memory_config=agentcore_memory_config,
                region_name=self.config.aws_region
            )

            logger.info(f"✅ AgentCore Memory session manager created")
            logger.info(f"   Memory ID: {self.config.agentcore_memory_id}")
            logger.info(f"   Session ID: {self.session_id}")
            logger.info(f"   Actor ID: {actor_id}")
            logger.info(f"   Region: {self.config.aws_region}")

            # Log successful memory setup
            log_memory_event("SETUP_SUCCESS", self.session_id, {
                "memory_id": self.config.agentcore_memory_id,
                "actor_id": actor_id,
                "retrieval_namespaces": ["preferences", "facts", "summaries"]
            })

        except Exception as e:
            logger.error(
                f"❌ Failed to create AgentCore Memory session manager: {e}")

            # Log memory setup failure
            log_memory_event("SETUP_FAILURE", self.session_id, {
                "error": str(e),
                "error_type": type(e).__name__,
                "memory_id": self.config.agentcore_memory_id
            })

            raise ValueError(
                f"AgentCore Memory session manager setup failed: {e}")

    def _setup_multimodal_uploader(self) -> None:
        """Setup multimodal content uploader for S3 storage."""
        try:
            # Create multimodal uploader if bucket is configured
            self.multimodal_uploader = create_multimodal_uploader(
                raw_bucket_name=self.config.raw_bucket_name,
                aws_region=self.config.aws_region
            )

            if self.multimodal_uploader:
                logger.info(
                    f"✅ Multimodal uploader initialized for bucket: {self.config.raw_bucket_name}")
            else:
                logger.warning(
                    "⚠️ Multimodal uploader not available - uploads disabled")

        except Exception as e:
            logger.error(f"❌ Failed to setup multimodal uploader: {e}")
            self.multimodal_uploader = None

    def _setup_all_tools(self) -> List[Any]:
        """Setup tools: specialized agents with semantic tool filtering."""
        tools = []

        # Add specialized agent tools - each handles semantic tool discovery
        logger.info(
            "🤖 Adding specialized agent tools with semantic filtering...")
        tools.extend([appointment_scheduling_agent,
                     information_retrieval_agent])

        logger.info(f"✅ Total tools configured: {len(tools)}")
        logger.info(
            "ℹ️ Each specialized agent uses semantic search for relevant MCP tools")
        return tools

    def _extract_text_from_content_blocks(self, content_blocks: List[Any]) -> str:
        """
        Extract text content from Strands ContentBlock list.

        Args:
            content_blocks: List of ContentBlock objects from Strands

        Returns:
            Combined text content as string
        """
        text_parts = []

        for block in content_blocks:
            # Handle different types of content blocks
            if hasattr(block, 'text') and block.text:
                text_parts.append(block.text)
            elif hasattr(block, 'toolResult') and block.toolResult:
                # Include tool results in the response
                tool_result = block.toolResult
                if hasattr(tool_result, 'content') and tool_result.content:
                    text_parts.append(f"Tool result: {tool_result.content}")
            elif hasattr(block, 'reasoningContent') and block.reasoningContent:
                # Include reasoning content if available
                reasoning = block.reasoningContent
                if hasattr(reasoning, 'text') and reasoning.text:
                    text_parts.append(reasoning.text)

        combined_text = '\n'.join(text_parts)
        logger.info(
            f"📝 Extracted {len(text_parts)} text blocks, total length: {len(combined_text)}")

        return combined_text

    def _prepare_strands_content(self, content_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prepare Strands content blocks by converting base64 strings to bytes.

        Args:
            content_blocks: List of content blocks in Strands format with base64 data

        Returns:
            List of content blocks with bytes data for Strands Agent
        """
        prepared_blocks = []

        for block in content_blocks:
            if "text" in block:
                # Text blocks pass through unchanged
                prepared_blocks.append(block)

            elif "image" in block:
                # Convert base64 to bytes for image blocks
                image_block = block.copy()
                base64_data = image_block["image"]["source"]["bytes"]

                try:
                    # Convert base64 string to actual bytes
                    image_bytes = base64.b64decode(base64_data)
                    image_block["image"]["source"]["bytes"] = image_bytes
                    prepared_blocks.append(image_block)

                except Exception as e:
                    logger.warning(f"Failed to decode image data: {e}")
                    # Add as text description if decoding fails
                    prepared_blocks.append({
                        "text": f"[Imagen no válida - Error al decodificar: {str(e)}]"
                    })

            elif "document" in block:
                # Convert base64 to bytes for document blocks
                doc_block = block.copy()
                base64_data = doc_block["document"]["source"]["bytes"]

                try:
                    # Convert base64 string to actual bytes
                    doc_bytes = base64.b64decode(base64_data)
                    doc_block["document"]["source"]["bytes"] = doc_bytes
                    prepared_blocks.append(doc_block)

                except Exception as e:
                    logger.warning(f"Failed to decode document data: {e}")
                    # Add as text description if decoding fails
                    doc_name = doc_block["document"].get("name", "documento")
                    prepared_blocks.append({
                        "text": f"[Documento {doc_name} no válido - Error al decodificar: {str(e)}]"
                    })

        return prepared_blocks

    def _upload_multimodal_content(self, content_blocks: List[Dict[str, Any]], patient_context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Upload multimodal content to S3 with patient context organization.

        Args:
            content_blocks: List of content blocks (already prepared with bytes)
            patient_context: Patient context information from agent processing

        Returns:
            List of upload results for tracking
        """
        upload_results = []

        # Check if uploader is available
        if not self.multimodal_uploader:
            logger.warning(
                "⚠️ Multimodal uploader not available - skipping uploads")
            return upload_results

        # Determine patient ID for organizing uploads using AI identification
        patient_id = "unknown_patient"
        if patient_context:
            # Use the AI-determined file organization ID if available
            if patient_context.get('fileOrganizationId'):
                patient_id = patient_context['fileOrganizationId']
                logger.info(f"📁 Using AI file organization ID: {patient_id}")
            elif patient_context.get('patientId'):
                # Fallback to patientId with cleaning
                raw_id = patient_context['patientId']
                patient_id = raw_id.replace(
                    '-', '').replace(' ', '_').replace('.', '')
                logger.info(
                    f"📁 Using cleaned patient ID: {patient_id} (from {raw_id})")

            # Log AI identification details for debugging
            if patient_context.get('aiIdentificationData'):
                ai_data = patient_context['aiIdentificationData']
                logger.info(
                    f"🤖 AI Identification: {ai_data.get('primary_identifier_type')} with {ai_data.get('identification_confidence')} confidence")

        logger.info(
            f"📁 Uploading multimodal content for patient: {patient_id}")

        # Check if there's any multimodal content to upload
        has_multimodal = any(
            "image" in block or "document" in block for block in content_blocks)

        if not has_multimodal:
            logger.info("ℹ️ No multimodal content found - skipping uploads")
            return upload_results

        try:
            # Upload all multimodal content
            upload_results = self.multimodal_uploader.upload_multimodal_content(
                patient_id=patient_id,
                content_blocks=content_blocks
            )

            # Log upload summary
            successful_uploads = [
                r for r in upload_results if r.get('success')]
            failed_uploads = [
                r for r in upload_results if not r.get('success')]

            if successful_uploads:
                logger.info(
                    f"✅ Successfully uploaded {len(successful_uploads)} files for patient {patient_id}")
                for result in successful_uploads:
                    logger.info(
                        f"   📄 {result.get('content_type', 'file')}: {result.get('s3_url', 'unknown')}")

            if failed_uploads:
                logger.warning(
                    f"⚠️ Failed to upload {len(failed_uploads)} files for patient {patient_id}")
                for result in failed_uploads:
                    logger.warning(
                        f"   ❌ {result.get('content_type', 'file')}: {result.get('error', 'unknown error')}")

        except Exception as e:
            logger.error(f"❌ Error during multimodal content upload: {e}")
            upload_results.append({
                'success': False,
                'error': str(e),
                'patient_id': patient_id
            })

        return upload_results

    def process_message(
        self,
        content_blocks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process healthcare agent request with multimodal support and AgentCore Memory.

        Args:
            content_blocks: List of content blocks in Strands format

        Returns:
            Response dictionary with patient context and memory information
        """
        if not self.agent:
            raise ValueError("Agent not initialized. Call initialize() first.")

        logger.info(
            f"🏥 Processing healthcare request | session_id={self.session_id} | content_blocks={len(content_blocks)}")

        # Log request details
        block_types = [list(block.keys())[0] for block in content_blocks]
        log_session_event("REQUEST_START", self.session_id, {
            "content_blocks": len(content_blocks),
            "block_types": block_types
        })

        # Log memory operation start
        log_memory_event("PROCESSING_START", self.session_id, {
            "content_blocks": len(content_blocks),
            "has_session_manager": bool(self.session_manager)
        })

        try:
            # Prepare content blocks for Strands (convert base64 to bytes)
            prepared_blocks = self._prepare_strands_content(content_blocks)

            logger.info(
                f"📝 Prepared {len(prepared_blocks)} content blocks for Strands")

            # Log multimodal content details
            log_session_event("MULTIMODAL_PREPARATION", self.session_id, {
                "original_blocks": len(content_blocks),
                "prepared_blocks": len(prepared_blocks),
                "block_types": [list(block.keys())[0] for block in prepared_blocks]
            })

            # Step 1: Get response from agent normally (let it use tools and generate response)
            logger.info(
                "🧠 Invoking agent with AgentCore Memory integration...")

            # First, get the normal agent response with tools
            result: AgentResult = self.agent(prepared_blocks)

            stop_reason: str = result.stop_reason
            message: Message = result.message
            role: str = message.get("role")
            content: List[ContentBlock] = message.get("content")
            metrics: EventLoopMetrics = result.metrics
            metric_summary: Dict[str, Any] = metrics.get_summary()
            interrupts = result.interrupts if result.interrupts else []
            interrupts = [inter.to_dict() for inter in interrupts]

            # Extract text content from Strands ContentBlock objects
            content_text = self._extract_text_from_content_blocks(content)

            logger.info(f"📄 Agent response length: {len(content_text)} characters")

            # Step 2: Extract structured output from the conversation
            logger.info("🔍 Extracting structured patient context from conversation...")
            
            try:
                # Use structured_output to extract patient context from the conversation
                structured_result: AgentResult = self.agent.structured_output(
                    HealthcareAgentResponse
                )
                
                structured_output: HealthcareAgentResponse = structured_result.structured_output
                
                if structured_output:
                    logger.info("✅ Successfully extracted structured output")
                    
                    # Get response content from structured output
                    response_content = getattr(structured_output, 'response_content', None)
                    full_content = response_content or content_text

                    # Get patient context from structured output
                    patient_context_obj = getattr(structured_output, 'patient_context', None)
                    if patient_context_obj:
                        patient_context_data = patient_context_obj
                        patient_context = {
                            "patientId": patient_context_data.patient_id,
                            "patientName": patient_context_data.patient_name,
                            "contextChanged": patient_context_data.context_changed,
                            "identificationSource": patient_context_data.identification_source.value,
                            "fileOrganizationId": patient_context_data.file_organization_id,
                            "confidenceLevel": patient_context_data.confidence_level,
                            "additionalIdentifiers": patient_context_data.additional_identifiers
                        }
                        logger.info(f"🎯 Patient context extracted: {patient_context_data.patient_name}")
                    else:
                        patient_context = None
                        logger.info("ℹ️ No patient context identified")
                        
                else:
                    logger.warning("⚠️ No structured output received from extraction")
                    full_content = content_text
                    patient_context = None
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to extract structured output: {e}")
                # Fallback to original response
                full_content = content_text
                patient_context = None

            logger.info(
                f"📄 Final response length: {len(full_content)} characters")

            # Log memory operation completion
            log_memory_event("PROCESSING_SUCCESS", self.session_id, {
                "response_length": len(full_content),
                "memory_used": bool(self.session_manager),
                "structured_output_used": patient_context is not None,
                "patient_context_found": patient_context is not None
            })

            # Upload multimodal content to S3 with patient organization
            upload_results = self._upload_multimodal_content(
                prepared_blocks, patient_context)

            # Create response with memory, upload information, and Strands metrics
            response = {
                "response": full_content,
                "sessionId": self.session_id,
                "patientContext": patient_context,
                "memoryEnabled": bool(self.session_manager),
                "memoryId": self.config.agentcore_memory_id if self.session_manager else None,
                "uploadResults": upload_results,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success",
                # Include Strands execution metrics
                "metrics": {
                    "stopReason": stop_reason,
                    "metricsSummary": metric_summary,
                    "interrupts": interrupts,
                    "structuredOutputUsed": patient_context is not None
                }
            }

            # Log guardrail activity for AgentCore monitoring
            log_guardrail_event("PROCESSING_COMPLETE", self.session_id, {
                "guardrail_id": self.config.guardrail_id,
                "guardrail_version": self.config.guardrail_version,
                "trace_enabled": True,
                "detection_mode": "ANONYMIZE",
                "blocking_disabled": True,
                "response_generated": True,
                "content_blocks_processed": len(content_blocks)
            })

            # Log successful completion
            successful_uploads = [
                r for r in upload_results if r.get('success')]
            log_session_event("REQUEST_SUCCESS", self.session_id, {
                "response_length": len(full_content),
                "has_patient_context": bool(patient_context),
                "patient_id": patient_context.get('patientId') if patient_context else None,
                "memory_enabled": bool(self.session_manager),
                "uploads_count": len(upload_results),
                "successful_uploads": len(successful_uploads),
                "stop_reason": stop_reason,
                "tool_calls": metric_summary.get('tool_calls', 0),
                "structured_output_used": patient_context is not None,
                "interrupts_count": len(interrupts),
                "guardrail_active": bool(self.config.guardrail_id)
            })

            return response

        except Exception as e:
            logger.error(f"❌ Error in healthcare agent processing: {e}")

            # Log memory operation error
            log_memory_event("PROCESSING_ERROR", self.session_id, {
                "error": str(e),
                "error_type": type(e).__name__
            })

            # Log session error
            log_session_event("REQUEST_ERROR", self.session_id, {
                "error": str(e),
                "error_type": type(e).__name__
            })

            raise


def create_healthcare_agent(session_id: str) -> HealthcareAgent:
    """
    Factory function to create and initialize a healthcare agent with AgentCore Memory.

    Args:
        session_id: Unique session identifier

    Returns:
        Initialized HealthcareAgent instance
    """
    config = get_agent_config()
    agent = HealthcareAgent(config, session_id)
    agent.initialize()
    return agent
