"""
Appointment Scheduling Agent for Strands Agents Virtual Assistant.
Specialized agent for managing appointment-related operations.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import asyncio
import re

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
from ..shared.models import AppointmentResponse, ErrorType, AppointmentStatus
from ..shared.healthcare_api_tools import (
    schedule_appointment, check_availability, get_appointments, 
    cancel_appointment, get_medics, get_exams, query_patient_api
)
from ..shared.utils import (
    get_logger, extract_patient_context, validate_spanish_medical_terms,
    create_error_response
)
from ..shared.context import ContextManager
from ..shared.coordination import get_agent_coordinator

logger = get_logger(__name__)

# System prompt for Appointment Scheduling Agent
SCHEDULING_SYSTEM_PROMPT = """
Eres un asistente médico especializado en la gestión de citas y programación de consultas. Tu función principal es:

1. **Programación de Citas**: Crear nuevas citas médicas verificando disponibilidad
2. **Consulta de Disponibilidad**: Verificar horarios disponibles de médicos y exámenes
3. **Gestión de Citas**: Consultar, modificar y cancelar citas existentes
4. **Coordinación de Recursos**: Asegurar que médicos, pacientes y exámenes estén disponibles

**Capacidades Específicas:**
- Entender solicitudes de citas en español con fechas y horarios naturales
- Verificar disponibilidad de médicos por especialidad
- Coordinar citas considerando tipos de exámenes y duración
- Manejar cancelaciones y reprogramaciones
- Proporcionar alternativas cuando no hay disponibilidad

**Formato de Respuesta:**
- Siempre usar el modelo AppointmentResponse para respuestas estructuradas
- Incluir detalles completos de la cita (paciente, médico, examen, fecha)
- Proporcionar horarios alternativos cuando sea necesario
- Confirmar todos los detalles antes de programar

**Manejo de Fechas y Horarios:**
- Reconocer formatos de fecha en español (ej: "mañana", "próximo lunes", "15 de marzo")
- Convertir a formato ISO para el sistema
- Sugerir horarios disponibles más cercanos a la preferencia del usuario
- Considerar horarios de trabajo médico estándar

**Manejo de Errores:**
- Informar claramente sobre conflictos de horario
- Explicar cuando médicos o exámenes no están disponibles
- Sugerir alternativas viables
- Confirmar antes de realizar cambios

Responde siempre en español y mantén un tono profesional y servicial para facilitar la programación de citas médicas.
"""


class AppointmentSchedulingAgent:
    """
    Appointment Scheduling Agent implementation using Strands framework.
    """
    
    def __init__(self):
        """Initialize the Appointment Scheduling Agent."""
        self.config = get_agent_config()
        self.model_config = get_model_config()
        self.logger = logger
        
        # Initialize agent with tools
        self.tools = [
            self._schedule_appointment_tool,
            self._check_availability_tool,
            self._get_appointments_tool,
            self._cancel_appointment_tool,
            self._get_medics_tool,
            self._get_exams_tool,
            self._find_patient_tool
        ]
        
        # Create Strands Agent instance
        self.agent = Agent(
            system_prompt=SCHEDULING_SYSTEM_PROMPT,
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
    
    async def process_scheduling_request(
        self, 
        query: str, 
        context_manager: ContextManager
    ) -> AppointmentResponse:
        """
        Process appointment scheduling request with structured output.
        
        Args:
            query: User query for appointment scheduling
            context_manager: Shared context manager
            
        Returns:
            AppointmentResponse: Structured response
        """
        try:
            self.logger.info("Processing appointment scheduling request")
            
            # Get coordinator for context coordination
            coordinator = get_agent_coordinator(context_manager.export_state())
            coordinator.register_agent("appointment_scheduling", [
                "appointment_management",
                "availability_checking",
                "medic_coordination",
                "exam_scheduling"
            ])
            
            # Extract patient context from query if present
            patient_context = extract_patient_context(query)
            if patient_context:
                # Use coordinator for consistent patient context
                coord_result = await coordinator.coordinate_patient_context(
                    patient_context.get("patient_name") or patient_context.get("cedula", ""),
                    "auto",
                    "appointment_scheduling"
                )
                if coord_result["success"]:
                    context_manager.set_patient_context(coord_result["patient_context"])
            
            # Use structured output for consistent response format
            response = self.agent.structured_output(
                AppointmentResponse,
                query,
                invocation_state=context_manager.export_state()
            )
            
            # Update conversation history
            context_manager.add_conversation_message(
                role="user",
                content=query,
                metadata={"agent": "appointment_scheduling"}
            )
            
            context_manager.add_conversation_message(
                role="assistant", 
                content=response.message,
                metadata={"agent": "appointment_scheduling", "structured_response": True}
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing scheduling request: {str(e)}")
            
            return AppointmentResponse(
                success=False,
                message=f"Error procesando solicitud de cita: {str(e)}",
                error_type=ErrorType.GENERAL_ERROR
            )
    
    def _parse_spanish_date(self, date_text: str) -> Optional[str]:
        """
        Parse Spanish date expressions to ISO format.
        
        Args:
            date_text: Date in Spanish (e.g., "mañana", "próximo lunes")
            
        Returns:
            Optional[str]: ISO date string or None
        """
        try:
            date_text = date_text.lower().strip()
            today = datetime.now().date()
            
            # Handle relative dates
            if "mañana" in date_text:
                target_date = today + timedelta(days=1)
            elif "hoy" in date_text:
                target_date = today
            elif "próximo" in date_text or "siguiente" in date_text:
                # Handle "próximo lunes", etc.
                days_of_week = {
                    "lunes": 0, "martes": 1, "miércoles": 2, "jueves": 3,
                    "viernes": 4, "sábado": 5, "domingo": 6
                }
                
                for day_name, day_num in days_of_week.items():
                    if day_name in date_text:
                        days_ahead = day_num - today.weekday()
                        if days_ahead <= 0:  # Target day already happened this week
                            days_ahead += 7
                        target_date = today + timedelta(days=days_ahead)
                        break
                else:
                    return None
            else:
                # Try to parse specific dates (basic implementation)
                # This could be enhanced with more sophisticated date parsing
                return None
            
            return target_date.isoformat()
            
        except Exception as e:
            self.logger.error(f"Error parsing Spanish date: {str(e)}")
            return None
    
    # Tool implementations
    
    async def _schedule_appointment_tool(
        self,
        patient_identifier: str,
        medic_identifier: str,
        exam_identifier: str,
        appointment_date: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tool for scheduling new appointments.
        
        Args:
            patient_identifier: Patient ID or name
            medic_identifier: Medic ID or name
            exam_identifier: Exam ID or name
            appointment_date: Date/time for appointment
            notes: Optional notes
            
        Returns:
            Dict[str, Any]: Scheduling result
        """
        try:
            # Parse date if it's in Spanish format
            parsed_date = self._parse_spanish_date(appointment_date)
            if parsed_date:
                appointment_date = parsed_date
            
            # For this implementation, we assume IDs are provided
            # In a full implementation, we would resolve names to IDs
            result = await schedule_appointment(
                patient_id=patient_identifier,
                medic_id=medic_identifier,
                exam_id=exam_identifier,
                appointment_date=appointment_date,
                notes=notes
            )
            
            if result.success:
                appointment_data = result.result
                return {
                    "success": True,
                    "appointment": appointment_data,
                    "message": f"Cita programada exitosamente para {appointment_date}"
                }
            else:
                return {
                    "success": False,
                    "message": f"Error programando cita: {result.error_message}",
                    "error": result.error_message
                }
                
        except Exception as e:
            self.logger.error(f"Error in schedule appointment tool: {str(e)}")
            return {
                "success": False,
                "message": f"Error programando cita: {str(e)}"
            }
    
    async def _check_availability_tool(
        self,
        medic_id: str,
        date: str,
        duration_hours: int = 1
    ) -> Dict[str, Any]:
        """
        Tool for checking medic availability.
        
        Args:
            medic_id: Medic identifier
            date: Date to check
            duration_hours: Duration in hours
            
        Returns:
            Dict[str, Any]: Availability information
        """
        try:
            # Parse date if it's in Spanish format
            parsed_date = self._parse_spanish_date(date)
            if parsed_date:
                date = parsed_date
            
            result = await check_availability(medic_id, date, duration_hours)
            
            if result.success:
                availability_data = result.result
                available = availability_data.get("available", False)
                
                message = "Médico disponible" if available else "Médico no disponible"
                if not available:
                    conflicts = availability_data.get("conflicts", 0)
                    message += f" - {conflicts} citas en conflicto"
                
                return {
                    "success": True,
                    "availability": availability_data,
                    "message": message
                }
            else:
                return {
                    "success": False,
                    "message": f"Error verificando disponibilidad: {result.error_message}",
                    "error": result.error_message
                }
                
        except Exception as e:
            self.logger.error(f"Error in check availability tool: {str(e)}")
            return {
                "success": False,
                "message": f"Error verificando disponibilidad: {str(e)}"
            }
    
    async def _get_appointments_tool(
        self,
        patient_id: Optional[str] = None,
        medic_id: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tool for retrieving appointments.
        
        Args:
            patient_id: Filter by patient
            medic_id: Filter by medic
            status: Filter by status
            date_from: Filter from date
            date_to: Filter to date
            
        Returns:
            Dict[str, Any]: Appointments list
        """
        try:
            result = await get_appointments(
                patient_id=patient_id,
                medic_id=medic_id,
                status=status,
                date_from=date_from,
                date_to=date_to
            )
            
            if result.success:
                appointments_data = result.result
                appointments = appointments_data.get("reservations", [])
                
                return {
                    "success": True,
                    "appointments": appointments,
                    "pagination": appointments_data.get("pagination", {}),
                    "message": f"Encontradas {len(appointments)} citas"
                }
            else:
                return {
                    "success": False,
                    "message": f"Error consultando citas: {result.error_message}",
                    "error": result.error_message
                }
                
        except Exception as e:
            self.logger.error(f"Error in get appointments tool: {str(e)}")
            return {
                "success": False,
                "message": f"Error consultando citas: {str(e)}"
            }
    
    async def _cancel_appointment_tool(
        self,
        reservation_id: str
    ) -> Dict[str, Any]:
        """
        Tool for cancelling appointments.
        
        Args:
            reservation_id: Reservation identifier
            
        Returns:
            Dict[str, Any]: Cancellation result
        """
        try:
            result = await cancel_appointment(reservation_id)
            
            if result.success:
                return {
                    "success": True,
                    "reservation_id": reservation_id,
                    "message": "Cita cancelada exitosamente"
                }
            else:
                return {
                    "success": False,
                    "message": f"Error cancelando cita: {result.error_message}",
                    "error": result.error_message
                }
                
        except Exception as e:
            self.logger.error(f"Error in cancel appointment tool: {str(e)}")
            return {
                "success": False,
                "message": f"Error cancelando cita: {str(e)}"
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
    
    async def _find_patient_tool(
        self,
        patient_identifier: str
    ) -> Dict[str, Any]:
        """
        Tool for finding patient information for scheduling.
        
        Args:
            patient_identifier: Patient ID, name, or cedula
            
        Returns:
            Dict[str, Any]: Patient information
        """
        try:
            result = await query_patient_api(patient_identifier, "auto")
            
            if result.success:
                return {
                    "success": True,
                    "patient": result.result,
                    "message": f"Paciente encontrado: {patient_identifier}"
                }
            else:
                return {
                    "success": False,
                    "message": f"No se encontró paciente: {patient_identifier}",
                    "error": result.error_message
                }
                
        except Exception as e:
            self.logger.error(f"Error in find patient tool: {str(e)}")
            return {
                "success": False,
                "message": f"Error buscando paciente: {str(e)}"
            }


# Tool wrapper for orchestrator integration
@tool
async def appointment_scheduling_agent(
    query: str, 
    invocation_state: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Appointment Scheduling Agent tool wrapper for orchestrator integration.
    
    Args:
        query: Appointment scheduling query
        invocation_state: Shared agent state
        
    Returns:
        Dict[str, Any]: Structured appointment response
    """
    try:
        # Initialize context manager
        context_manager = ContextManager(invocation_state)
        
        # Create and use appointment scheduling agent
        scheduling_agent = AppointmentSchedulingAgent()
        response = await scheduling_agent.process_scheduling_request(query, context_manager)
        
        # Update invocation state
        if invocation_state is not None:
            invocation_state.update(context_manager.export_state())
        
        return response.dict()
        
    except Exception as e:
        logger.error(f"Error in appointment scheduling agent tool: {str(e)}")
        
        error_response = AppointmentResponse(
            success=False,
            message=f"Error en agente de citas: {str(e)}",
            error_type=ErrorType.GENERAL_ERROR
        )
        
        return error_response.dict()


# Export the agent class and tool
__all__ = ["AppointmentSchedulingAgent", "appointment_scheduling_agent"]
