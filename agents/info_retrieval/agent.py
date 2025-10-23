"""
Information Retrieval Agent for Strands Agents Virtual Assistant.
Specialized agent for retrieving and storing patient information and conversation data.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import asyncio

# Strands Agents imports (will be available when framework is installed)
try:
    from strands import Agent, tool
    from strands.models import get_model
except ImportError:
    # Placeholder for development - actual imports will work when Strands is installed
    def tool(func):
        return func
    
    class Agent:
        def __init__(self, *args, **kwargs):
            pass
        
        def structured_output(self, *args, **kwargs):
            pass

from ..shared.config import get_agent_config, get_model_config
from ..shared.models import PatientInfoResponse, ErrorType
from ..shared.healthcare_api_tools import (
    query_patient_api, get_medics, get_exams
)
from ..shared.knowledge_base_tools import (
    search_knowledge_base, store_conversation, retrieve_conversation_history
)
from ..shared.utils import (
    get_logger, extract_patient_context, validate_spanish_medical_terms,
    create_error_response
)
from ..shared.context import ContextManager
from ..shared.coordination import get_agent_coordinator

logger = get_logger(__name__)

# System prompt for Information Retrieval Agent
INFO_RETRIEVAL_SYSTEM_PROMPT = """
Eres un asistente médico especializado en la recuperación y gestión de información de pacientes. Tu función principal es:

1. **Búsqueda de Pacientes**: Buscar información de pacientes por nombre, ID o cédula
2. **Consulta de Base de Conocimiento**: Buscar documentos médicos relevantes
3. **Gestión de Conversaciones**: Almacenar y recuperar historial de conversaciones médicas
4. **Contexto de Sesión**: Mantener el contexto del paciente actual en la sesión

**Capacidades Específicas:**
- Reconocer identificadores de pacientes en español (nombres completos, cédulas)
- Buscar en la base de conocimiento médica usando terminología en español
- Almacenar notas del médico y resúmenes de conversación
- Proporcionar respuestas estructuradas para integración con frontend

**Formato de Respuesta:**
- Siempre usar el modelo PatientInfoResponse para respuestas estructuradas
- Incluir información relevante del paciente cuando esté disponible
- Proporcionar mensajes claros en español sobre el estado de las consultas
- Indicar si se encontró información o si hay errores

**Manejo de Errores:**
- Informar claramente cuando no se encuentra un paciente
- Explicar problemas de conectividad con APIs o base de conocimiento
- Sugerir alternativas cuando las búsquedas no tienen resultados

Responde siempre en español y mantén un tono profesional y útil para el contexto médico.
"""


class InformationRetrievalAgent:
    """
    Information Retrieval Agent implementation using Strands framework.
    """
    
    def __init__(self):
        """Initialize the Information Retrieval Agent."""
        self.config = get_agent_config()
        self.model_config = get_model_config()
        self.logger = logger
        
        # Initialize agent with tools
        self.tools = [
            self._query_patient_tool,
            self._search_knowledge_base_tool,
            self._store_conversation_tool,
            self._get_conversation_history_tool,
            self._get_medics_tool,
            self._get_exams_tool
        ]
        
        # Create Strands Agent instance
        self.agent = Agent(
            system_prompt=INFO_RETRIEVAL_SYSTEM_PROMPT,
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
    
    async def process_query(
        self, 
        query: str, 
        context_manager: ContextManager
    ) -> PatientInfoResponse:
        """
        Process information retrieval query with structured output.
        
        Args:
            query: User query for patient information
            context_manager: Shared context manager
            
        Returns:
            PatientInfoResponse: Structured response
        """
        try:
            self.logger.info("Processing information retrieval query")
            
            # Get coordinator for context coordination
            coordinator = get_agent_coordinator(context_manager.export_state())
            coordinator.register_agent("information_retrieval", [
                "patient_data_retrieval",
                "knowledge_base_search",
                "conversation_storage",
                "medical_information"
            ])
            
            # Extract patient context from query if present
            patient_context = extract_patient_context(query)
            if patient_context:
                # Use coordinator for consistent patient context
                coord_result = await coordinator.coordinate_patient_context(
                    patient_context.get("patient_name") or patient_context.get("cedula", ""),
                    "auto",
                    "information_retrieval"
                )
                if coord_result["success"]:
                    context_manager.set_patient_context(coord_result["patient_context"])
            
            # Use structured output for consistent response format
            response = self.agent.structured_output(
                PatientInfoResponse,
                query,
                invocation_state=context_manager.export_state()
            )
            
            # Update conversation history
            context_manager.add_conversation_message(
                role="user",
                content=query,
                metadata={"agent": "information_retrieval"}
            )
            
            context_manager.add_conversation_message(
                role="assistant", 
                content=response.message,
                metadata={"agent": "information_retrieval", "structured_response": True}
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing information retrieval query: {str(e)}")
            
            return PatientInfoResponse(
                success=False,
                message=f"Error procesando consulta de información: {str(e)}",
                error_type=ErrorType.GENERAL_ERROR
            )
    
    # Tool implementations
    
    async def _query_patient_tool(
        self, 
        patient_identifier: str, 
        identifier_type: str = "auto"
    ) -> Dict[str, Any]:
        """
        Tool for querying patient information from Healthcare API.
        
        Args:
            patient_identifier: Patient ID, name, or cedula
            identifier_type: Type of identifier (id, name, cedula, auto)
            
        Returns:
            Dict[str, Any]: Patient information
        """
        try:
            result = await query_patient_api(patient_identifier, identifier_type)
            
            if result.success:
                return {
                    "success": True,
                    "patient_data": result.result,
                    "message": f"Paciente encontrado: {patient_identifier}"
                }
            else:
                return {
                    "success": False,
                    "message": f"No se encontró paciente con {identifier_type}: {patient_identifier}",
                    "error": result.error_message
                }
                
        except Exception as e:
            self.logger.error(f"Error in patient query tool: {str(e)}")
            return {
                "success": False,
                "message": f"Error consultando paciente: {str(e)}"
            }
    
    async def _search_knowledge_base_tool(
        self, 
        query: str, 
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Tool for searching Bedrock Knowledge Base.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            Dict[str, Any]: Search results
        """
        try:
            result = await search_knowledge_base(query, max_results)
            
            if result.success:
                return {
                    "success": True,
                    "search_results": result.result,
                    "message": f"Encontrados {len(result.result.get('results', []))} documentos relevantes"
                }
            else:
                return {
                    "success": False,
                    "message": "Error buscando en base de conocimiento",
                    "error": result.error_message
                }
                
        except Exception as e:
            self.logger.error(f"Error in knowledge base search tool: {str(e)}")
            return {
                "success": False,
                "message": f"Error en búsqueda de documentos: {str(e)}"
            }
    
    async def _store_conversation_tool(
        self,
        session_id: str,
        conversation_data: Dict[str, Any],
        patient_id: Optional[str] = None,
        medic_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tool for storing conversation history.
        
        Args:
            session_id: Session identifier
            conversation_data: Conversation messages
            patient_id: Patient identifier
            medic_id: Medic identifier
            notes: Doctor's notes
            
        Returns:
            Dict[str, Any]: Storage result
        """
        try:
            result = await store_conversation(
                session_id, patient_id, medic_id, conversation_data, notes
            )
            
            if result.success:
                return {
                    "success": True,
                    "conversation_id": result.result.get("conversation_id"),
                    "message": "Conversación almacenada correctamente"
                }
            else:
                return {
                    "success": False,
                    "message": "Error almacenando conversación",
                    "error": result.error_message
                }
                
        except Exception as e:
            self.logger.error(f"Error in store conversation tool: {str(e)}")
            return {
                "success": False,
                "message": f"Error almacenando conversación: {str(e)}"
            }
    
    async def _get_conversation_history_tool(
        self,
        session_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Tool for retrieving conversation history.
        
        Args:
            session_id: Session identifier
            patient_id: Patient identifier
            limit: Maximum number of records
            
        Returns:
            Dict[str, Any]: Conversation history
        """
        try:
            result = await retrieve_conversation_history(session_id, patient_id, None, limit)
            
            if result.success:
                return {
                    "success": True,
                    "conversations": result.result.get("conversations", []),
                    "message": f"Recuperadas {result.result.get('total_retrieved', 0)} conversaciones"
                }
            else:
                return {
                    "success": False,
                    "message": "Error recuperando historial de conversaciones",
                    "error": result.error_message
                }
                
        except Exception as e:
            self.logger.error(f"Error in get conversation history tool: {str(e)}")
            return {
                "success": False,
                "message": f"Error recuperando historial: {str(e)}"
            }
    
    async def _get_medics_tool(
        self, 
        specialty: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tool for retrieving medics list.
        
        Args:
            specialty: Filter by specialty
            
        Returns:
            Dict[str, Any]: Medics list
        """
        try:
            result = await get_medics(specialty)
            
            if result.success:
                medics_data = result.result.get("medics", [])
                return {
                    "success": True,
                    "medics": medics_data,
                    "message": f"Encontrados {len(medics_data)} médicos" + 
                              (f" en especialidad {specialty}" if specialty else "")
                }
            else:
                return {
                    "success": False,
                    "message": "Error consultando lista de médicos",
                    "error": result.error_message
                }
                
        except Exception as e:
            self.logger.error(f"Error in get medics tool: {str(e)}")
            return {
                "success": False,
                "message": f"Error consultando médicos: {str(e)}"
            }
    
    async def _get_exams_tool(
        self, 
        exam_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tool for retrieving exams list.
        
        Args:
            exam_type: Filter by exam type
            
        Returns:
            Dict[str, Any]: Exams list
        """
        try:
            result = await get_exams(exam_type)
            
            if result.success:
                exams_data = result.result.get("exams", [])
                return {
                    "success": True,
                    "exams": exams_data,
                    "message": f"Encontrados {len(exams_data)} exámenes" + 
                              (f" de tipo {exam_type}" if exam_type else "")
                }
            else:
                return {
                    "success": False,
                    "message": "Error consultando lista de exámenes",
                    "error": result.error_message
                }
                
        except Exception as e:
            self.logger.error(f"Error in get exams tool: {str(e)}")
            return {
                "success": False,
                "message": f"Error consultando exámenes: {str(e)}"
            }


# Tool wrapper for orchestrator integration
@tool
async def information_retrieval_agent(
    query: str, 
    invocation_state: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Information Retrieval Agent tool wrapper for orchestrator integration.
    
    Args:
        query: Information retrieval query
        invocation_state: Shared agent state
        
    Returns:
        Dict[str, Any]: Structured patient information response
    """
    try:
        # Initialize context manager
        context_manager = ContextManager(invocation_state)
        
        # Create and use information retrieval agent
        info_agent = InformationRetrievalAgent()
        response = await info_agent.process_query(query, context_manager)
        
        # Update invocation state
        if invocation_state is not None:
            invocation_state.update(context_manager.export_state())
        
        return response.dict()
        
    except Exception as e:
        logger.error(f"Error in information retrieval agent tool: {str(e)}")
        
        error_response = PatientInfoResponse(
            success=False,
            message=f"Error en agente de información: {str(e)}",
            error_type=ErrorType.GENERAL_ERROR
        )
        
        return error_response.dict()


# Export the agent class and tool
__all__ = ["InformationRetrievalAgent", "information_retrieval_agent"]
