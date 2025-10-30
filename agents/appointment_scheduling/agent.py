"""
Appointment Scheduling Agent using Strands "Agents as Tools" pattern.
Specialized agent for managing appointment-related operations.
"""

from typing import Dict, Any, Optional

from strands import Agent, tool
from strands.models import BedrockModel
from ..shared.config import get_agent_config, get_model_config
from ..shared.utils import get_logger
from ..shared.prompts import get_prompt
from ..shared.mcp_gateway_tools import (
    query_reservations_mcp, query_medics_mcp, schedule_appointment_mcp,
    check_availability_mcp, get_medics_by_specialty_mcp
)

logger = get_logger(__name__)


# Strands "Agents as Tools" implementation
@tool
async def appointment_scheduling_agent(request: str) -> str:
    """
    Handle appointment scheduling and management requests.
    
    This agent specializes in:
    - Scheduling new medical appointments
    - Checking availability of doctors and time slots
    - Managing existing appointments (view, cancel, modify)
    - Coordinating medical resources
    
    Args:
        request: Appointment scheduling request with patient and scheduling details
        
    Returns:
        str: Scheduling response with confirmation or available alternatives
    """
    try:
        logger.info("Appointment scheduling agent processing request")
        
        # Get configuration
        config = get_agent_config()
        model_config = get_model_config()
        
        # Load system prompt from file
        system_prompt = get_prompt("appointment_scheduling")
        
        # Create specialized agent with tools for appointment management and Bedrock Guardrails
        scheduling_agent = Agent(
            system_prompt=system_prompt,
            tools=[
                _schedule_appointment_tool,
                _check_availability_tool,
                _get_appointments_tool,
                _cancel_appointment_tool,
                _get_medics_tool
            ],
            model=BedrockModel(
                model_id=model_config.model_id,
                temperature=model_config.temperature,
                max_tokens=model_config.max_tokens,
                top_p=model_config.top_p
            ),
            guardrail_id=config.guardrail_id,
            guardrail_version=config.guardrail_version
        )
        
        # Process the request
        response = scheduling_agent(request)
        return str(response)
        
    except Exception as e:
        logger.error(f"Error in appointment scheduling agent: {str(e)}")
        return f"❌ Error en agente de citas: {str(e)}"


# Tool implementations for the appointment scheduling agent
async def _schedule_appointment_tool(
    patient_id: str,
    medic_id: str,
    exam_id: str,
    appointment_date: str,
    appointment_time: str = None
) -> Dict[str, Any]:
    """Schedule a new appointment using MCP Gateway."""
    try:
        # Combine date and time if provided separately
        if appointment_time and appointment_date:
            reservation_datetime = f"{appointment_date}T{appointment_time}:00"
        else:
            reservation_datetime = appointment_date
            
        result = await schedule_appointment_mcp(
            patient_id=patient_id,
            medic_id=medic_id,
            exam_id=exam_id,
            reservation_date=reservation_datetime
        )
        
        if result.success:
            appointment = result.result.get("reservation", {})
            return {
                "success": True,
                "appointment": appointment,
                "message": f"📅 Cita programada exitosamente para {appointment_date}"
            }
        else:
            return {
                "success": False,
                "message": f"❌ Error programando cita: {result.error_message}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Error programando cita: {str(e)}"
        }


async def _check_availability_tool(
    medic_id: str,
    date: str
) -> Dict[str, Any]:
    """Check availability for appointments using MCP Gateway."""
    try:
        result = await check_availability_mcp(
            medic_id=medic_id,
            date=date
        )
        
        if result.success:
            availability_data = result.result
            available_slots = availability_data.get("available_slots", [])
            return {
                "success": True,
                "available_slots": available_slots,
                "message": f"🕐 {len(available_slots)} horarios disponibles para {date}"
            }
        else:
            return {
                "success": False,
                "message": f"❌ Error verificando disponibilidad: {result.error_message}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Error verificando disponibilidad: {str(e)}"
        }


async def _get_appointments_tool(
    patient_id: Optional[str] = None,
    medic_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """Get appointments using MCP Gateway."""
    try:
        result = await query_reservations_mcp(
            action="list",
            patient_id=patient_id,
            medic_id=medic_id,
            date_from=date_from,
            date_to=date_to,
            status=status,
            pagination={"limit": 50, "offset": 0}
        )
        
        if result.success:
            reservations_data = result.result
            appointments = reservations_data.get("reservations", [])
            return {
                "success": True,
                "appointments": appointments,
                "message": f"📋 {len(appointments)} citas encontradas"
            }
        else:
            return {
                "success": False,
                "message": f"❌ Error obteniendo citas: {result.error_message}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Error obteniendo citas: {str(e)}"
        }


async def _cancel_appointment_tool(
    reservation_id: str,
    reason: str = "Cancelación solicitada"
) -> Dict[str, Any]:
    """Cancel an appointment using MCP Gateway."""
    try:
        result = await query_reservations_mcp(
            action="delete",
            reservation_id=reservation_id
        )
        
        if result.success:
            return {
                "success": True,
                "message": f"✅ Cita cancelada exitosamente: {reason}"
            }
        else:
            return {
                "success": False,
                "message": f"❌ Error cancelando cita: {result.error_message}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Error cancelando cita: {str(e)}"
        }


async def _get_medics_tool(
    specialty: Optional[str] = None
) -> Dict[str, Any]:
    """Get list of medics using MCP Gateway."""
    try:
        if specialty:
            result = await get_medics_by_specialty_mcp(specialty=specialty)
        else:
            result = await query_medics_mcp(
                action="list",
                pagination={"limit": 50, "offset": 0}
            )
        
        if result.success:
            medics_data = result.result
            medics = medics_data.get("medics", [])
            return {
                "success": True,
                "medics": medics,
                "message": f"👨‍⚕️ {len(medics)} médicos disponibles"
            }
        else:
            return {
                "success": False,
                "message": f"❌ Error obteniendo médicos: {result.error_message}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Error obteniendo médicos: {str(e)}"
        }


# Export the tool function
__all__ = ["appointment_scheduling_agent"]
