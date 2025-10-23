"""
Orchestrator Agent for Strands Agents Virtual Assistant.
Main coordinator agent that interfaces with frontend and manages specialized agents.
"""

from typing import Dict, Any, Optional, List, AsyncGenerator, Union
from datetime import datetime
import json
import asyncio
import base64

# Strands Agents imports (will be available when framework is installed)
try:
    from strands import Agent
    from strands.models import get_model
except ImportError:
    # Placeholder for development - actual imports will work when Strands is installed
    class Agent:
        def __init__(self, *args, **kwargs):
            pass
        
        async def stream_async(self, *args, **kwargs):
            yield {"type": "text", "content": "Placeholder response"}

from ..shared.config import get_agent_config, get_model_config
from ..shared.models import SessionContext, ErrorType
from ..shared.utils import (
    get_logger, format_response, extract_patient_context, 
    validate_spanish_medical_terms, create_error_response
)
from ..shared.guardrails import guardrails_manager, GuardrailAction
from ..shared.context import ContextManager
from ..shared.coordination import get_agent_coordinator, PatientContextValidator
from ..shared.guardrails import get_compliance_manager
from ..info_retrieval.agent import information_retrieval_agent
from ..appointment_scheduling.agent import appointment_scheduling_agent

logger = get_logger(__name__)

# System prompt for Orchestrator Agent
ORCHESTRATOR_SYSTEM_PROMPT = """
Eres un asistente médico virtual inteligente que ayuda a médicos durante las consultas con pacientes. Tu función principal es coordinar y facilitar el acceso a información médica y la gestión de citas.

**Idioma y Comunicación:**
- Responde SIEMPRE en español latinoamericano por defecto
- Usa terminología médica apropiada y profesional
- Mantén un tono amigable pero conciso para minimizar latencia
- Formatea tus respuestas en markdown para mejor presentación

**Capacidades Principales:**
1. **Información de Pacientes**: Buscar y recuperar datos de pacientes por nombre, ID o cédula
2. **Gestión de Citas**: Programar, consultar, modificar y cancelar citas médicas
3. **Base de Conocimiento**: Buscar documentos médicos y información relevante
4. **Procesamiento de Documentos**: Manejar documentos subidos durante la conversación
5. **Contexto de Sesión**: Mantener el contexto del paciente actual y la conversación

**Agentes Especializados Disponibles:**
- **Agente de Información**: Para consultas sobre pacientes y documentos médicos
- **Agente de Citas**: Para programación y gestión de citas médicas

**Instrucciones de Uso:**
- Cuando recibas consultas sobre información de pacientes, usa el agente de información
- Para solicitudes de citas o programación, usa el agente de citas
- Puedes combinar información de ambos agentes según sea necesario
- Mantén el contexto del paciente actual en la sesión
- Procesa documentos de forma inmediata cuando sea posible

**Manejo de Contexto de Paciente:**
- Reconoce frases como "esta sesión es del paciente [nombre]"
- Mantén el contexto del paciente activo durante toda la conversación
- Usa la información del paciente actual para consultas relacionadas

**Formato de Respuesta:**
- Usa markdown para estructurar las respuestas
- Incluye información relevante de forma clara y organizada
- Proporciona opciones y alternativas cuando sea apropiado
- Confirma acciones importantes antes de ejecutarlas

**Manejo de Errores:**
- Explica claramente cualquier problema o limitación
- Sugiere alternativas cuando algo no esté disponible
- Mantén la conversación fluida incluso ante errores

Eres un compañero confiable para el médico, facilitando su trabajo con información precisa y gestión eficiente de citas.
"""


class OrchestratorAgent:
    """
    Orchestrator Agent implementation using Strands framework with streaming support.
    """
    
    def __init__(self):
        """Initialize the Orchestrator Agent."""
        self.config = get_agent_config()
        self.model_config = get_model_config()
        self.logger = logger
        
        # Initialize agent coordinator
        self.coordinator = None  # Will be set when processing requests
        
        # Initialize specialized agent tools
        self.tools = [
            information_retrieval_agent,
            appointment_scheduling_agent,
            self._process_document_tool,
            self._set_patient_context_tool,
            self._get_session_summary_tool,
            self._coordinate_patient_context_tool
        ]
        
        # Create Strands Agent instance
        self.agent = Agent(
            system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
            tools=self.tools,
            model=self._get_model()
        )
    
    def _get_model(self):
        """Get configured model for the agent."""
        try:
            return get_model(
                model_id=self.model_config.model_id,
                temperature=self.model_config.temperature,
                max_tokens=self.model_config.max_tokens,
                top_p=self.model_config.top_p
            )
        except Exception as e:
            self.logger.error(f"Error getting model: {str(e)}")
            # Return a placeholder - actual implementation will use Strands model
            return None
    
    async def stream_response(
        self, 
        user_message: str, 
        session_context: Optional[Dict[str, Any]] = None,
        multimodal_inputs: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream response using Strands Agent with multimodal support.
        
        Args:
            user_message: User's message
            session_context: Current session context
            multimodal_inputs: Optional multimodal inputs (documents, images)
            
        Yields:
            Dict[str, Any]: Streaming response events
        """
        try:
            self.logger.info("Starting streaming response")
            
            # Initialize context manager, coordinator, and compliance manager
            context_manager = ContextManager(session_context)
            self.coordinator = get_agent_coordinator(session_context)
            compliance_manager = get_compliance_manager()
            
            # Register orchestrator agent
            self.coordinator.register_agent("orchestrator", [
                "patient_context_coordination",
                "multimodal_processing", 
                "agent_orchestration",
                "session_management",
                "pii_phi_protection"
            ])
            
            # Process user input through compliance checks
            input_compliance = await compliance_manager.process_user_input(user_message)
            
            if not input_compliance["safe_for_processing"]:
                yield {
                    "type": "error",
                    "content": f"⚠️ {input_compliance['compliance_message']}",
                    "metadata": {"compliance_blocked": True}
                }
                return
            
            # Use processed (potentially filtered) input
            processed_message = input_compliance["processed_input"]
            
            # Notify if content was filtered
            if input_compliance["guardrail_applied"]:
                yield {
                    "type": "info",
                    "content": "🔒 Contenido procesado por políticas de seguridad",
                    "metadata": {"guardrail_applied": True}
                }
            
            # Process multimodal inputs if provided
            if multimodal_inputs:
                for input_item in multimodal_inputs:
                    await self._handle_multimodal_input(input_item, context_manager)
            
            # Extract and set patient context if present in message
            patient_context = extract_patient_context(processed_message)
            if patient_context:
                context_manager.set_patient_context(patient_context)
                
                # Yield immediate feedback about patient context
                yield {
                    "type": "context_update",
                    "content": f"✓ Contexto de paciente establecido: {patient_context.get('patient_name', 'ID actualizado')}",
                    "metadata": {"patient_context": patient_context}
                }
            
            # Add user message to conversation history
            context_manager.add_conversation_message(
                role="user",
                content=user_message,
                metadata={"multimodal_inputs": len(multimodal_inputs) if multimodal_inputs else 0}
            )
            
            # Stream response from agent using processed (filtered) message
            response_content = ""
            async for event in self.agent.stream_async(
                processed_message, 
                invocation_state=context_manager.export_state()
            ):
                # Process different event types
                if event.get("type") == "text":
                    content = event.get("content", "")
                    response_content += content
                    
                    # Apply compliance checks to output content
                    output_compliance = await compliance_manager.process_agent_response(content)
                    
                    if not output_compliance["safe_for_output"]:
                        yield {
                            "type": "error",
                            "content": f"⚠️ {output_compliance['compliance_message']}",
                            "metadata": {"compliance_blocked_output": True}
                        }
                        continue
                    
                    # Use processed (potentially filtered) content
                    filtered_content = output_compliance["processed_response"]
                    
                    # Format content as markdown
                    formatted_content = format_response(filtered_content, "markdown")
                    
                    yield {
                        "type": "text",
                        "content": formatted_content,
                        "metadata": {
                            "agent": "orchestrator",
                            "guardrail_applied": output_compliance["guardrail_applied"],
                            "safety_validated": output_compliance["safety_validation"]["safe"]
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
                        "metadata": {
                            "tool_name": tool_name,
                            "success": success
                        }
                    }
                
                elif event.get("type") == "error":
                    error_message = event.get("content", "Error desconocido")
                    yield {
                        "type": "error",
                        "content": f"❌ Error: {error_message}",
                        "metadata": {"error": error_message}
                    }
            
            # Add assistant response to conversation history
            if response_content:
                context_manager.add_conversation_message(
                    role="assistant",
                    content=response_content,
                    metadata={"agent": "orchestrator", "streaming": True}
                )
            
            # Yield final context update
            yield {
                "type": "context_update",
                "content": "",
                "metadata": {
                    "session_context": context_manager.export_state(),
                    "conversation_length": len(context_manager.get_conversation_history())
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in streaming response: {str(e)}")
            
            yield {
                "type": "error",
                "content": f"❌ Error en el asistente: {str(e)}",
                "metadata": {"error": str(e), "error_type": "streaming_error"}
            }
    
    async def _handle_multimodal_input(
        self, 
        input_item: Dict[str, Any], 
        context_manager: ContextManager
    ) -> None:
        """
        Handle multimodal input processing.
        
        Args:
            input_item: Multimodal input item
            context_manager: Context manager
        """
        try:
            input_type = input_item.get("type", "")
            
            if input_type == "document":
                # Process document upload
                filename = input_item.get("filename", "")
                content_type = input_item.get("content_type", "")
                content_data = input_item.get("content", "")
                
                # Decode base64 content if needed
                if isinstance(content_data, str):
                    document_content = base64.b64decode(content_data)
                else:
                    document_content = content_data
                
                # Add document to active documents
                document_id = f"doc_{datetime.utcnow().timestamp()}"
                context_manager.add_active_document(document_id)
                
                self.logger.info(f"Processed document: {filename}")
                
            elif input_type == "image":
                # Process image input
                filename = input_item.get("filename", "")
                context_manager.add_active_document(f"img_{filename}")
                
                self.logger.info(f"Processed image: {filename}")
                
        except Exception as e:
            self.logger.error(f"Error handling multimodal input: {str(e)}")
    
    # Tool implementations for orchestrator
    
    async def _process_document_tool(
        self,
        document_data: str,
        filename: str,
        content_type: str
    ) -> Dict[str, Any]:
        """
        Tool for processing document uploads.
        
        Args:
            document_data: Base64 encoded document data
            filename: Original filename
            content_type: MIME content type
            
        Returns:
            Dict[str, Any]: Processing result
        """
        try:
            # Decode document content
            document_content = base64.b64decode(document_data)
            
            # Basic content analysis for immediate feedback
            immediate_analysis = ""
            if content_type == "text/plain":
                text_content = document_content.decode('utf-8')
                word_count = len(text_content.split())
                immediate_analysis = f"Documento de texto con {word_count} palabras"
                
            elif content_type == "application/pdf":
                immediate_analysis = f"Documento PDF: {filename}"
                
            elif content_type.startswith("image/"):
                immediate_analysis = f"Imagen: {filename}"
            
            return {
                "success": True,
                "filename": filename,
                "content_type": content_type,
                "analysis": immediate_analysis,
                "message": f"📄 Documento procesado: {filename}"
            }
            
        except Exception as e:
            self.logger.error(f"Error processing document: {str(e)}")
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
        """
        Tool for setting patient context in session.
        
        Args:
            patient_name: Patient's name
            patient_id: Patient ID
            cedula: Patient's cedula
            
        Returns:
            Dict[str, Any]: Context setting result
        """
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
            self.logger.error(f"Error setting patient context: {str(e)}")
            return {
                "success": False,
                "message": f"Error estableciendo contexto: {str(e)}"
            }
    
    async def _get_session_summary_tool(self) -> Dict[str, Any]:
        """
        Tool for getting current session summary.
        
        Returns:
            Dict[str, Any]: Session summary
        """
        try:
            return {
                "success": True,
                "summary": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent": "orchestrator",
                    "capabilities": [
                        "Información de pacientes",
                        "Gestión de citas",
                        "Búsqueda en base de conocimiento",
                        "Procesamiento de documentos"
                    ]
                },
                "message": "📊 Resumen de sesión generado"
            }
            
        except Exception as e:
            self.logger.error(f"Error getting session summary: {str(e)}")
            return {
                "success": False,
                "message": f"Error obteniendo resumen: {str(e)}"
            }
    
    async def _coordinate_patient_context_tool(
        self,
        patient_identifier: str,
        identifier_type: str = "auto"
    ) -> Dict[str, Any]:
        """
        Tool for coordinating patient context across all agents.
        
        Args:
            patient_identifier: Patient ID, name, or cedula
            identifier_type: Type of identifier
            
        Returns:
            Dict[str, Any]: Coordination result
        """
        try:
            if not self.coordinator:
                return {
                    "success": False,
                    "message": "Coordinador no disponible"
                }
            
            # Validate patient identifier
            validation = PatientContextValidator.validate_patient_identifier(
                patient_identifier, identifier_type
            )
            
            if not validation["valid"]:
                return {
                    "success": False,
                    "message": f"Identificador de paciente inválido: {', '.join(validation['issues'])}",
                    "validation_issues": validation["issues"]
                }
            
            # Coordinate patient context
            result = await self.coordinator.coordinate_patient_context(
                patient_identifier, 
                validation["identifier_type"],
                "orchestrator"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error coordinating patient context: {str(e)}")
            return {
                "success": False,
                "message": f"Error coordinando contexto de paciente: {str(e)}"
            }


# Main orchestrator function for AgentCore integration
async def orchestrator_invocation(
    payload: Dict[str, Any]
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Main orchestrator invocation function for AgentCore Runtime.
    
    Args:
        payload: Request payload from AgentCore
        
    Yields:
        Dict[str, Any]: Streaming response events
    """
    try:
        # Extract request data
        user_message = payload.get("prompt", "")
        session_context = payload.get("session_context", {})
        multimodal_inputs = payload.get("multimodal_inputs", [])
        
        # Create orchestrator agent
        orchestrator = OrchestratorAgent()
        
        # Stream response
        async for event in orchestrator.stream_response(
            user_message=user_message,
            session_context=session_context,
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
