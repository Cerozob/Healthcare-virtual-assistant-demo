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
from strands_tools import current_time
from strands.models import BedrockModel
from strands.agent.agent_result import AgentResult
from strands.types.content import Message, ContentBlock
from strands.telemetry.metrics import EventLoopMetrics
from strands.session.s3_session_manager import S3SessionManager
from appointment_scheduling.agent import appointment_scheduling_agent
from info_retrieval.agent import information_retrieval_agent
from shared.config import get_agent_config
from shared.memory_logger import MemoryOperationLogger, MemoryDebugger
from shared.models import HealthcareAgentResponse
from shared.guardrail_monitoring_hook import create_guardrail_monitoring_hook
# Multimodal uploader removed - using Lambda-based file upload tool instead
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
        self.session_manager = None

    def initialize(self) -> None:
        """Initialize the healthcare agent."""
        logger.info(
            f"🏥 Initializing Healthcare Agent | session_id={self.session_id}")

        # Log initialization start
        log_session_event("INIT_START", self.session_id, {
            "session_id_length": len(self.session_id),
            "model_id": self.config.model_id
        })

        try:
            # Setup session manager
            self._setup_session_manager()

            # Setup all tools (Strands tools + MCP tools + specialized agents)
            # Note: File uploads are handled by the Lambda-based healthcare-files-api tool
            tools = self._setup_all_tools()

            # Create guardrail monitoring hook for shadow-mode monitoring
            guardrail_hook = create_guardrail_monitoring_hook(
                guardrail_id=self.config.guardrail_id,
                guardrail_version=self.config.guardrail_version,
                aws_region=self.config.aws_region,
                session_id=self.session_id
            )

            # Create a Bedrock model instance with full guardrail tracing
            bedrock_model = BedrockModel(
                model_id=self.config.model_id,
                temperature=self.config.model_temperature,
                # top_p=self.config.model_top_p,
                guardrail_id=self.config.guardrail_id,
                guardrail_version=self.config.guardrail_version,
                guardrail_trace="enabled_full",  # Enable complete guardrail activity logging for AgentCore
                guardrail_redact_input=False,  # CRITICAL: Don't redact input - allow PII for patient lookup
                guardrail_redact_output=True,  # Don't redact output - let ANONYMIZE action in guardrail handle it
                guardrail_redact_input_message="[Mensaje redactado por Guardrails]",
                guardrail_redact_output_message="[Mensaje redactado por Guardrails]",
                streaming=False
            )

            logger.info(f"🛡️ Guardrail configured: ID={self.config.guardrail_id}, Version={self.config.guardrail_version}")
            logger.info("🔍 Guardrail tracing: ENABLED_FULL (detection without blocking)")
            logger.info("🔍 Guardrail monitoring hook: ENABLED (shadow mode with detailed logging)")

            # Create the agent with guardrail monitoring hook
            self.agent = Agent(
                model=bedrock_model,
                system_prompt=get_prompt("healthcare"),
                tools=tools,
                session_manager=self.session_manager,
                hooks=[guardrail_hook]  # Add guardrail monitoring hook
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
        """Setup S3 session manager for conversation history."""
        try:
            # Use S3 session manager for simple conversation history
            self.session_manager = S3SessionManager(
                session_id=self.session_id,
                bucket=self.config.session_bucket,
                prefix="chat_history",
                region_name=self.config.aws_region
            )

            logger.info(f"✅ S3 session manager created")
            logger.info(f"   Session ID: {self.session_id}")
            logger.info(f"   Bucket: {self.config.session_bucket}")
            logger.info(f"   Region: {self.config.aws_region}")

            # Log successful memory setup
            log_memory_event("SETUP_SUCCESS", self.session_id, {
                "session_manager_type": "S3SessionManager",
                "bucket": self.config.session_bucket
            })

        except Exception as e:
            logger.error(
                f"❌ Failed to create S3 session manager: {e}")

            # Log memory setup failure
            log_memory_event("SETUP_FAILURE", self.session_id, {
                "error": str(e),
                "error_type": type(e).__name__
            })

            raise ValueError(
                f"S3 session manager setup failed: {e}")

    # Multimodal uploader removed - file uploads are now handled exclusively by the
    # Lambda-based healthcare-files-api tool which has proper IAM permissions

    def _setup_all_tools(self) -> List[Any]:
        """Setup tools: specialized agents with semantic tool filtering."""
        tools = []

        # Add specialized agent tools - each handles semantic tool discovery
        logger.info(
            "🤖 Adding specialized agent tools with semantic filtering...")
        tools.extend([appointment_scheduling_agent,
                     information_retrieval_agent, current_time])

        logger.info(f"✅ Total tools configured: {len(tools)}")
        logger.info(
            "ℹ️ Each specialized agent uses semantic search for relevant MCP tools")
        return tools

    def _extract_text_from_content_blocks(self, content_blocks: List[ContentBlock]) -> str:
        """
        Extract text content from Strands ContentBlock list.
        
        ContentBlock is a TypedDict that can contain different types of content:
        - text: str - Direct text response from the model
        - toolUse: ToolUse - Model requesting to use a tool (not final response)
        - toolResult: ToolResult - Result from tool execution (not final response)
        - reasoningContent: ReasoningContentBlock - Internal reasoning (not final response)
        - image, document, video: Media content (not text)

        Args:
            content_blocks: List of ContentBlock TypedDict objects from Strands

        Returns:
            Combined text content as string
        """
        text_parts = []

        for i, block in enumerate(content_blocks):
            # ContentBlock is a TypedDict - access as dictionary
            # Only extract 'text' fields - these are the actual response content
            if 'text' in block and block['text']:
                text_parts.append(block['text'])
                logger.debug(f"   Block {i}: text ({len(block['text'])} chars)")
            elif 'toolUse' in block:
                # Tool use requests are not part of the final response
                logger.debug(f"   Block {i}: toolUse (skipped - not response content)")
            elif 'toolResult' in block:
                # Tool results are not part of the final response
                logger.debug(f"   Block {i}: toolResult (skipped - not response content)")
            elif 'reasoningContent' in block:
                # Reasoning is internal processing, not final response
                logger.debug(f"   Block {i}: reasoningContent (skipped - internal)")
            elif 'image' in block or 'document' in block or 'video' in block:
                # Media content is not text
                logger.debug(f"   Block {i}: media content (skipped - not text)")

        combined_text = '\n'.join(text_parts)
        logger.info(
            f"📝 Extracted {len(text_parts)} text blocks, total length: {len(combined_text)}")

        return combined_text

    def _sanitize_document_name(self, name: str) -> str:
        """
        Sanitize document name to meet Bedrock Converse API requirements:
        - Only alphanumeric characters, whitespace, hyphens, parentheses, and square brackets
        - No consecutive whitespace characters
        
        Args:
            name: Original document name
            
        Returns:
            Sanitized document name
        """
        import re
        
        # Replace invalid characters with underscores
        # Valid: alphanumeric, whitespace, hyphens, parentheses, square brackets
        sanitized = re.sub(r'[^\w\s\-\(\)\[\].]', '_', name)
        
        # Replace consecutive whitespace with single space
        sanitized = re.sub(r'\s+', ' ', sanitized)
        
        # Trim whitespace from start and end
        sanitized = sanitized.strip()
        
        # Ensure we have a valid name
        if not sanitized:
            sanitized = "document.pdf"
        
        return sanitized
    
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
                    
                    # Sanitize document name to meet Bedrock requirements:
                    # - Only alphanumeric, whitespace, hyphens, parentheses, square brackets
                    # - No consecutive whitespace
                    original_name = doc_block["document"].get("name", "document.pdf")
                    sanitized_name = self._sanitize_document_name(original_name)
                    
                    if sanitized_name != original_name:
                        logger.info(f"📝 Sanitized document name: '{original_name}' → '{sanitized_name}'")
                    
                    doc_block["document"]["name"] = sanitized_name
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
        Track multimodal content for logging purposes.
        
        NOTE: Actual file uploads are handled by the Lambda-based healthcare-files-api tool,
        which the agent calls automatically when needed. This method just logs what was sent.

        Args:
            content_blocks: List of content blocks (already prepared with bytes)
            patient_context: Patient context information from agent processing

        Returns:
            Empty list (uploads are handled by Lambda tool)
        """
        # Check if there's any multimodal content
        has_multimodal = any(
            "image" in block or "document" in block for block in content_blocks)

        if has_multimodal:
            multimodal_count = sum(1 for block in content_blocks if "image" in block or "document" in block)
            logger.info(
                f"📁 Detected {multimodal_count} multimodal content blocks - uploads handled by Lambda tool")
            
            # Log patient context if available
            if patient_context:
                patient_id = patient_context.get('fileOrganizationId') or patient_context.get('patientId')
                logger.info(f"📁 Patient context: {patient_id}")
        else:
            logger.debug("ℹ️ No multimodal content in this request")

        # Return empty list - actual uploads are handled by the Lambda tool
        return []

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
            
            # Debug: Log the actual content structure
            logger.debug(f"🔍 Content blocks structure: {[type(block).__name__ for block in content]}")
            if not content_text:
                logger.warning("⚠️ No text extracted from content blocks - checking message structure")
                logger.debug(f"🔍 Message role: {role}")
                logger.debug(f"🔍 Content blocks count: {len(content)}")

            # Use the original agent response as the primary content
            # The content_text already contains the agent's response
            full_content = content_text
            
            # Step 2: Extract structured patient context from the conversation
            # IMPORTANT: The agent() followed by agent.structured_output() pattern is the
            # intended way to get both the natural language response AND structured data.
            # - agent() generates the response and uses tools
            # - agent.structured_output() extracts structured data from the conversation
            logger.info("🔍 Extracting structured patient context from conversation...")
            patient_context = None
            
            try:
                # Use structured_output to extract patient context metadata
                # This makes a separate LLM call to extract structured data from the conversation
                structured_output: HealthcareAgentResponse = self.agent.structured_output(
                    HealthcareAgentResponse
                )
                
                patient_context_data = structured_output.patient_context
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
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to extract structured output: {e}")
                logger.debug(f"Exception details: {str(e)}")
                # Continue without patient context - not critical
            
            # Final safety check - if we still have no content, try to recover from metrics
            if not full_content:
                logger.error("❌ CRITICAL: No response content extracted from agent!")
                logger.error(f"   content_text length: {len(content_text)}")
                logger.error(f"   content blocks: {len(content)}")
                logger.error(f"   stop_reason: {stop_reason}")
                # Try to extract from metrics as last resort
                if metric_summary and 'traces' in metric_summary:
                    logger.info("🔍 Attempting to extract response from metrics traces...")
                    for trace in metric_summary['traces']:
                        if trace.get('message') and trace['message'].get('content'):
                            for block in trace['message']['content']:
                                if 'text' in block:
                                    full_content = block['text']
                                    logger.info(f"✅ Recovered response from traces: {len(full_content)} chars")
                                    break
                        if full_content:
                            break
                
                # If still no content, provide a fallback message
                if not full_content:
                    full_content = "Lo siento, hubo un problema al generar la respuesta. Por favor, intenta de nuevo."
                    logger.error("❌ Using fallback error message as response")

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

            # Get guardrail interventions from agent state
            guardrail_interventions = self.agent.state.get("guardrail_interventions")
            if not guardrail_interventions:
                guardrail_interventions = []
            
            # Create response with memory, upload information, and Strands metrics
            # IMPORTANT: sessionId is the Strands session ID (internal to the agent)
            # The AgentCore runtimeSessionId is managed by the SDK and should match this
            response = {
                "response": full_content,
                "sessionId": self.session_id,  # Strands session ID - should match runtimeSessionId from SDK
                "patientContext": patient_context,
                "memoryEnabled": bool(self.session_manager),
                "uploadResults": upload_results,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success",
                # Include Strands execution metrics
                "metrics": {
                    "stopReason": stop_reason,
                    "metricsSummary": metric_summary,
                    "interrupts": interrupts,
                    "structuredOutputUsed": patient_context is not None
                },
                # Include guardrail monitoring data
                "guardrailInterventions": guardrail_interventions
            }

            # Log guardrail activity for AgentCore monitoring
            log_guardrail_event("PROCESSING_COMPLETE", self.session_id, {
                "guardrail_id": self.config.guardrail_id,
                "guardrail_version": self.config.guardrail_version,
                "trace_enabled": True,
                "detection_mode": "ANONYMIZE",
                "blocking_disabled": True,
                "response_generated": True,
                "content_blocks_processed": len(content_blocks),
                "interventions_count": len(guardrail_interventions),
                "has_violations": len(guardrail_interventions) > 0
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
                "guardrail_active": bool(self.config.guardrail_id),
                "guardrail_interventions": len(guardrail_interventions)
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
