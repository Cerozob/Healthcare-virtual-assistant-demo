"""
Orchestrator Agent using Strands "Agents as Tools" pattern with shared state.
Main coordinator agent that interfaces with frontend and manages specialized agents.
"""

from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime
import base64
from strands import Agent
from strands.models import BedrockModel


from ..shared.config import get_agent_config, get_model_config
from ..shared.utils import get_logger, extract_patient_context
from ..shared.prompts import get_prompt

from ..info_retrieval.agent import information_retrieval_agent
from ..appointment_scheduling.agent import appointment_scheduling_agent

logger = get_logger(__name__)


class OrchestratorAgent:
    """
    Simplified Orchestrator Agent using Strands "Agents as Tools" pattern.
    Uses shared state for context management instead of complex coordination.
    """

    def __init__(self):
        """Initialize the Orchestrator Agent."""
        self.config = get_agent_config()
        self.model_config = get_model_config()
        self.logger = logger

        # Load system prompt from file
        system_prompt = get_prompt("orchestrator")

        # Create Strands Agent with specialized agent tools and Bedrock Guardrails
        self.agent = Agent(
            system_prompt=system_prompt,
            tools=[
                information_retrieval_agent,
                appointment_scheduling_agent,
                self._process_document_tool,
                self._set_patient_context_tool
            ],
            model=self._get_model(),
            guardrail_id=self.config.guardrail_id,
            guardrail_version=self.config.guardrail_version
        )

    def _get_model(self):
        """Get configured model for the agent."""
        try:
            return BedrockModel(
                model_id=self.model_config.model_id,
                temperature=self.model_config.temperature,
                max_tokens=self.model_config.max_tokens,
                top_p=self.model_config.top_p
            )
        except Exception as e:
            self.logger.error(f"Error getting model: {str(e)}")
            return None

    async def stream_response(
        self,
        user_message: str,
        invocation_state: Optional[Dict[str, Any]] = None,
        multimodal_inputs: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream response using Strands Agent with shared state.

        Args:
            user_message: User's message
            invocation_state: Shared state across agents (Strands pattern)
            multimodal_inputs: Optional multimodal inputs

        Yields:
            Dict[str, Any]: Streaming response events
        """
        try:
            self.logger.info("Starting orchestrator streaming response")

            # Initialize shared state if not provided
            if invocation_state is None:
                invocation_state = {
                    "session_id": f"session_{datetime.utcnow().timestamp()}",
                    "patient_context": {},
                    "conversation_history": [],
                    "active_documents": []
                }

            # Bedrock Guardrails are now handled automatically by Strands Agent

            # Process multimodal inputs if provided
            if multimodal_inputs:
                for input_item in multimodal_inputs:
                    self._handle_multimodal_input(input_item, invocation_state)

            # Extract and set patient context if present in message
            patient_context = extract_patient_context(user_message)
            if patient_context:
                invocation_state["patient_context"] = patient_context

                yield {
                    "type": "context_update",
                    "content": f"✓ Contexto de paciente: {patient_context.get('patient_name', 'ID actualizado')}",
                    "metadata": {"patient_context": patient_context}
                }

            # Add user message to conversation history in shared state
            invocation_state["conversation_history"].append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.utcnow().isoformat(),
                "multimodal_inputs": len(multimodal_inputs) if multimodal_inputs else 0
            })

            # Stream response from agent with shared state (Bedrock Guardrails applied automatically)
            response_content = ""
            async for event in self.agent.stream_async(
                user_message,
                invocation_state=invocation_state
            ):
                # Process different event types (Bedrock Guardrails applied automatically)
                if event.get("type") == "text":
                    content = event.get("content", "")
                    response_content += content

                    yield {
                        "type": "text",
                        "content": content,
                        "metadata": {
                            "agent": "orchestrator"
                        }
                    }

                elif event.get("type") == "tool_call":
                    tool_name = event.get("tool_name", "")
                    yield {
                        "type": "tool_execution",
                        "content": f"🔧 Ejecutando: {tool_name}",
                        "metadata": {"tool_name": tool_name}
                    }

                elif event.get("type") == "tool_result":
                    tool_name = event.get("tool_name", "")
                    success = event.get("success", False)
                    status_icon = "✅" if success else "❌"

                    yield {
                        "type": "tool_result",
                        "content": f"{status_icon} {tool_name} completado",
                        "metadata": {"tool_name": tool_name, "success": success}
                    }

                elif event.get("type") == "error":
                    error_message = event.get("content", "Error desconocido")
                    yield {
                        "type": "error",
                        "content": f"❌ Error: {error_message}",
                        "metadata": {"error": error_message}
                    }

            # Add assistant response to conversation history in shared state
            if response_content:
                invocation_state["conversation_history"].append({
                    "role": "assistant",
                    "content": response_content,
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent": "orchestrator"
                })

            # Yield final context update with shared state
            yield {
                "type": "context_update",
                "content": "",
                "metadata": {
                    "invocation_state": invocation_state,
                    "conversation_length": len(invocation_state["conversation_history"])
                }
            }

        except Exception as e:
            self.logger.error(f"Error in streaming response: {str(e)}")

            yield {
                "type": "error",
                "content": f"❌ Error en el asistente: {str(e)}",
                "metadata": {"error": str(e), "error_type": "streaming_error"}
            }

    def _handle_multimodal_input(
        self,
        input_item: Dict[str, Any],
        invocation_state: Dict[str, Any]
    ) -> None:
        """
        Handle multimodal input processing using shared state.

        Args:
            input_item: Multimodal input item
            invocation_state: Shared state dictionary
        """
        try:
            input_type = input_item.get("type", "")
            filename = input_item.get("filename", "")

            if input_type in ["document", "image"]:
                # Add to active documents in shared state
                document_id = f"{input_type}_{datetime.utcnow().timestamp()}"
                invocation_state["active_documents"].append({
                    "id": document_id,
                    "type": input_type,
                    "filename": filename,
                    "processed_at": datetime.utcnow().isoformat()
                })

                self.logger.info(f"Processed {input_type}: {filename}")

        except Exception as e:
            self.logger.error(f"Error handling multimodal input: {str(e)}")

    # Simplified tool implementations

    async def _process_document_tool(
        self,
        document_data: str,
        filename: str,
        content_type: str
    ) -> Dict[str, Any]:
        """Tool for processing document uploads."""
        try:
            # Basic content analysis
            if content_type == "text/plain":
                try:
                    text_content = base64.b64decode(
                        document_data).decode('utf-8')
                    word_count = len(text_content.split())
                    analysis = f"Documento de texto con {word_count} palabras"
                except:
                    analysis = "Documento de texto"
            elif content_type == "application/pdf":
                analysis = f"Documento PDF: {filename}"
            elif content_type.startswith("image/"):
                analysis = f"Imagen: {filename}"
            else:
                analysis = f"Documento: {filename}"

            return {
                "success": True,
                "filename": filename,
                "analysis": analysis,
                "message": f"📄 Documento procesado: {filename}"
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error procesando documento: {str(e)}"
            }

    async def _set_patient_context_tool(
        self,
        patient_name: Optional[str] = None,
        patient_id: Optional[str] = None,
        cedula: Optional[str] = None
    ) -> Dict[str, Any]:
        """Tool for setting patient context."""
        try:
            context_data = {}

            if patient_name:
                context_data["patient_name"] = patient_name
            if patient_id:
                context_data["patient_id"] = patient_id
            if cedula:
                context_data["cedula"] = cedula

            if context_data:
                return {
                    "success": True,
                    "context": context_data,
                    "message": f"👤 Contexto de paciente establecido"
                }
            else:
                return {
                    "success": False,
                    "message": "No se proporcionó información del paciente"
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error estableciendo contexto: {str(e)}"
            }


# Main orchestrator function for AgentCore integration
async def orchestrator_invocation(
    payload: Dict[str, Any]
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Main orchestrator invocation function for AgentCore Runtime.
    Uses Strands shared state pattern for context management.

    Args:
        payload: Request payload from AgentCore

    Yields:
        Dict[str, Any]: Streaming response events
    """
    try:
        # Extract request data
        user_message = payload.get("prompt", "")
        invocation_state = payload.get("invocationState", {})
        multimodal_inputs = payload.get("multimodalInputs", [])

        # Create orchestrator agent
        orchestrator = OrchestratorAgent()

        # Stream response using shared state
        async for event in orchestrator.stream_response(
            user_message=user_message,
            invocation_state=invocation_state,
            multimodal_inputs=multimodal_inputs
        ):
            yield event

    except Exception as e:
        logger.error(f"Error in orchestrator invocation: {str(e)}")

        yield {
            "type": "error",
            "content": f"❌ Error del sistema: {str(e)}",
            "metadata": {
                "error": str(e),
                "error_type": "system_error"
            }
        }


# Export the agent class and main function
__all__ = ["OrchestratorAgent", "orchestrator_invocation"]
