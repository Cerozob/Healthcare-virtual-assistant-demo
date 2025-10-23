"""
Agent coordination and shared context management for Strands Agents system.
Ensures consistent patient identification and context sharing across all agents.
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import json
import asyncio
from .utils import get_logger, sanitize_for_logging
from .context import ContextManager
from .models import SessionContext, PatientInfoResponse, AppointmentResponse

logger = get_logger(__name__)


class AgentCoordinator:
    """
    Coordinates communication and context sharing between specialized agents.
    Ensures consistent patient identification and tool sharing.
    """
    
    def __init__(self, invocation_state: Optional[Dict[str, Any]] = None):
        """
        Initialize agent coordinator.
        
        Args:
            invocation_state: Shared state from AgentCore
        """
        self.context_manager = ContextManager(invocation_state)
        self.logger = logger
        
        # Track active agents and their capabilities
        self.active_agents = {}
        self.shared_tools = {}
        
        # Patient context consistency tracking
        self.patient_context_version = 0
        self.last_patient_update = None
    
    def register_agent(self, agent_name: str, capabilities: List[str]) -> None:
        """
        Register an agent with its capabilities.
        
        Args:
            agent_name: Name of the agent
            capabilities: List of agent capabilities
        """
        self.active_agents[agent_name] = {
            "capabilities": capabilities,
            "registered_at": datetime.utcnow().isoformat(),
            "last_used": None
        }
        
        self.logger.info(f"Agent registered: {agent_name} with capabilities: {capabilities}")
    
    def register_shared_tool(self, tool_name: str, tool_function: callable) -> None:
        """
        Register a tool that can be shared between agents.
        
        Args:
            tool_name: Name of the tool
            tool_function: Tool function
        """
        self.shared_tools[tool_name] = {
            "function": tool_function,
            "registered_at": datetime.utcnow().isoformat(),
            "usage_count": 0
        }
        
        self.logger.info(f"Shared tool registered: {tool_name}")
    
    async def coordinate_patient_context(
        self, 
        patient_identifier: str, 
        identifier_type: str = "auto",
        requesting_agent: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Coordinate patient context across all agents.
        Ensures consistent patient identification system.
        
        Args:
            patient_identifier: Patient ID, name, or cedula
            identifier_type: Type of identifier
            requesting_agent: Agent requesting the context
            
        Returns:
            Dict[str, Any]: Coordinated patient context
        """
        try:
            self.logger.info(f"Coordinating patient context for {requesting_agent}")
            
            # Check if we already have this patient in context
            current_patient = self.context_manager.get_patient_context()
            
            # Determine if this is the same patient
            is_same_patient = False
            if current_patient:
                if identifier_type == "id" and current_patient.get("patient_id") == patient_identifier:
                    is_same_patient = True
                elif identifier_type == "name" and current_patient.get("patient_name", "").lower() == patient_identifier.lower():
                    is_same_patient = True
                elif identifier_type == "cedula" and current_patient.get("cedula") == patient_identifier:
                    is_same_patient = True
            
            # If same patient, return existing context
            if is_same_patient:
                self.logger.info("Using existing patient context")
                return {
                    "success": True,
                    "patient_context": current_patient,
                    "context_source": "existing",
                    "message": f"Contexto de paciente activo: {current_patient.get('patient_name', 'ID disponible')}"
                }
            
            # Need to fetch new patient context
            from .healthcare_api_tools import query_patient_api
            
            result = await query_patient_api(patient_identifier, identifier_type)
            
            if result.success:
                patient_data = result.result
                
                # Create standardized patient context
                patient_context = {
                    "patient_id": patient_data.get("patient_id"),
                    "patient_name": patient_data.get("full_name"),
                    "cedula": patient_data.get("cedula"),
                    "phone": patient_data.get("phone"),
                    "email": patient_data.get("email"),
                    "age": patient_data.get("age"),
                    "medical_history": patient_data.get("medical_history"),
                    "allergies": patient_data.get("allergies"),
                    "medications": patient_data.get("medications"),
                    "context_established_by": requesting_agent,
                    "context_established_at": datetime.utcnow().isoformat(),
                    "identifier_used": patient_identifier,
                    "identifier_type": identifier_type
                }
                
                # Update context manager
                self.context_manager.set_patient_context(patient_context)
                
                # Update version tracking
                self.patient_context_version += 1
                self.last_patient_update = datetime.utcnow()
                
                # Notify all agents of context change
                await self._notify_agents_context_change("patient_context_updated", patient_context)
                
                return {
                    "success": True,
                    "patient_context": patient_context,
                    "context_source": "api",
                    "message": f"Contexto de paciente establecido: {patient_context.get('patient_name', 'Paciente encontrado')}"
                }
            else:
                return {
                    "success": False,
                    "message": f"No se pudo establecer contexto de paciente: {result.error_message}",
                    "error": result.error_message
                }
                
        except Exception as e:
            self.logger.error(f"Error coordinating patient context: {str(e)}")
            return {
                "success": False,
                "message": f"Error coordinando contexto de paciente: {str(e)}",
                "error": str(e)
            }
    
    async def coordinate_tool_sharing(
        self, 
        tool_name: str, 
        tool_args: Dict[str, Any],
        requesting_agent: str
    ) -> Dict[str, Any]:
        """
        Coordinate tool sharing between agents.
        
        Args:
            tool_name: Name of the tool to execute
            tool_args: Tool arguments
            requesting_agent: Agent requesting the tool
            
        Returns:
            Dict[str, Any]: Tool execution result
        """
        try:
            if tool_name not in self.shared_tools:
                return {
                    "success": False,
                    "message": f"Tool {tool_name} not available for sharing",
                    "error": "tool_not_found"
                }
            
            tool_info = self.shared_tools[tool_name]
            tool_function = tool_info["function"]
            
            # Update usage tracking
            tool_info["usage_count"] += 1
            tool_info["last_used"] = datetime.utcnow().isoformat()
            tool_info["last_used_by"] = requesting_agent
            
            # Execute tool with context
            result = await tool_function(**tool_args)
            
            self.logger.info(f"Shared tool executed: {tool_name} by {requesting_agent}")
            
            return {
                "success": True,
                "result": result,
                "tool_name": tool_name,
                "executed_by": requesting_agent
            }
            
        except Exception as e:
            self.logger.error(f"Error executing shared tool {tool_name}: {str(e)}")
            return {
                "success": False,
                "message": f"Error ejecutando herramienta compartida: {str(e)}",
                "error": str(e)
            }
    
    async def ensure_context_consistency(self) -> Dict[str, Any]:
        """
        Ensure context consistency across all agents.
        
        Returns:
            Dict[str, Any]: Consistency check result
        """
        try:
            consistency_report = {
                "patient_context_version": self.patient_context_version,
                "last_patient_update": self.last_patient_update.isoformat() if self.last_patient_update else None,
                "active_agents": len(self.active_agents),
                "shared_tools": len(self.shared_tools),
                "session_messages": len(self.context_manager.get_conversation_history()),
                "active_documents": len(self.context_manager.get_active_documents()),
                "language_preference": self.context_manager.get_language_preference()
            }
            
            # Check for context inconsistencies
            issues = []
            
            # Check if patient context is stale
            if self.last_patient_update:
                time_since_update = datetime.utcnow() - self.last_patient_update
                if time_since_update.total_seconds() > 3600:  # 1 hour
                    issues.append("patient_context_stale")
            
            # Check conversation history size
            if len(self.context_manager.get_conversation_history()) > 100:
                issues.append("conversation_history_large")
            
            consistency_report["issues"] = issues
            consistency_report["consistent"] = len(issues) == 0
            
            return {
                "success": True,
                "consistency_report": consistency_report,
                "message": "Verificación de consistencia completada"
            }
            
        except Exception as e:
            self.logger.error(f"Error checking context consistency: {str(e)}")
            return {
                "success": False,
                "message": f"Error verificando consistencia: {str(e)}",
                "error": str(e)
            }
    
    async def _notify_agents_context_change(
        self, 
        change_type: str, 
        change_data: Dict[str, Any]
    ) -> None:
        """
        Notify all active agents of context changes.
        
        Args:
            change_type: Type of change
            change_data: Change data
        """
        try:
            notification = {
                "change_type": change_type,
                "change_data": sanitize_for_logging(change_data),
                "timestamp": datetime.utcnow().isoformat(),
                "version": self.patient_context_version
            }
            
            # Add to context manager for agent access
            session_context = self.context_manager.get_session_context()
            if "agent_notifications" not in session_context:
                session_context["agent_notifications"] = []
            
            session_context["agent_notifications"].append(notification)
            
            # Keep only last 10 notifications
            if len(session_context["agent_notifications"]) > 10:
                session_context["agent_notifications"] = session_context["agent_notifications"][-10:]
            
            self.context_manager.set_session_context(session_context)
            
            self.logger.debug(f"Context change notification sent: {change_type}")
            
        except Exception as e:
            self.logger.error(f"Error notifying agents of context change: {str(e)}")
    
    def get_coordination_summary(self) -> Dict[str, Any]:
        """
        Get summary of current coordination state.
        
        Returns:
            Dict[str, Any]: Coordination summary
        """
        return {
            "active_agents": self.active_agents,
            "shared_tools": {
                name: {
                    "usage_count": info["usage_count"],
                    "last_used": info.get("last_used"),
                    "last_used_by": info.get("last_used_by")
                }
                for name, info in self.shared_tools.items()
            },
            "patient_context_version": self.patient_context_version,
            "last_patient_update": self.last_patient_update.isoformat() if self.last_patient_update else None,
            "context_summary": self.context_manager.get_session_summary()
        }
    
    def export_coordination_state(self) -> Dict[str, Any]:
        """
        Export coordination state for persistence.
        
        Returns:
            Dict[str, Any]: Exportable coordination state
        """
        return {
            "coordination_metadata": {
                "patient_context_version": self.patient_context_version,
                "last_patient_update": self.last_patient_update.isoformat() if self.last_patient_update else None,
                "active_agents": self.active_agents,
                "tool_usage": {
                    name: {
                        "usage_count": info["usage_count"],
                        "last_used": info.get("last_used")
                    }
                    for name, info in self.shared_tools.items()
                }
            },
            "context_state": self.context_manager.export_state()
        }


class PatientContextValidator:
    """
    Validates and ensures consistency of patient context across agents.
    """
    
    @staticmethod
    def validate_patient_identifier(identifier: str, identifier_type: str) -> Dict[str, Any]:
        """
        Validate patient identifier format and type.
        
        Args:
            identifier: Patient identifier
            identifier_type: Type of identifier
            
        Returns:
            Dict[str, Any]: Validation result
        """
        validation_result = {
            "valid": False,
            "identifier": identifier,
            "identifier_type": identifier_type,
            "issues": []
        }
        
        if not identifier or not identifier.strip():
            validation_result["issues"].append("empty_identifier")
            return validation_result
        
        identifier = identifier.strip()
        
        if identifier_type == "id":
            # UUID format validation
            if len(identifier) == 36 and identifier.count('-') == 4:
                validation_result["valid"] = True
            else:
                validation_result["issues"].append("invalid_uuid_format")
        
        elif identifier_type == "cedula":
            # Basic cedula validation (numeric, reasonable length)
            if identifier.isdigit() and 6 <= len(identifier) <= 12:
                validation_result["valid"] = True
            else:
                validation_result["issues"].append("invalid_cedula_format")
        
        elif identifier_type == "name":
            # Name validation (at least 2 characters, contains letters)
            if len(identifier) >= 2 and any(c.isalpha() for c in identifier):
                validation_result["valid"] = True
            else:
                validation_result["issues"].append("invalid_name_format")
        
        elif identifier_type == "auto":
            # Auto-detect and validate
            if len(identifier) == 36 and identifier.count('-') == 4:
                validation_result["identifier_type"] = "id"
                validation_result["valid"] = True
            elif identifier.isdigit() and 6 <= len(identifier) <= 12:
                validation_result["identifier_type"] = "cedula"
                validation_result["valid"] = True
            elif len(identifier) >= 2 and any(c.isalpha() for c in identifier):
                validation_result["identifier_type"] = "name"
                validation_result["valid"] = True
            else:
                validation_result["issues"].append("unrecognized_identifier_format")
        
        return validation_result
    
    @staticmethod
    def normalize_patient_context(patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize patient context to ensure consistency.
        
        Args:
            patient_data: Raw patient data
            
        Returns:
            Dict[str, Any]: Normalized patient context
        """
        normalized = {
            "patient_id": patient_data.get("patient_id"),
            "patient_name": patient_data.get("full_name") or patient_data.get("patient_name"),
            "cedula": patient_data.get("cedula"),
            "phone": patient_data.get("phone"),
            "email": patient_data.get("email"),
            "age": patient_data.get("age"),
            "date_of_birth": patient_data.get("date_of_birth"),
            "medical_history": patient_data.get("medical_history") or {},
            "allergies": patient_data.get("allergies") or [],
            "medications": patient_data.get("medications") or [],
            "lab_results": patient_data.get("lab_results") or {},
            "normalized_at": datetime.utcnow().isoformat()
        }
        
        # Remove None values
        normalized = {k: v for k, v in normalized.items() if v is not None}
        
        return normalized


# Global coordinator instance for agent coordination
_global_coordinator = None


def get_agent_coordinator(invocation_state: Optional[Dict[str, Any]] = None) -> AgentCoordinator:
    """
    Get or create global agent coordinator instance.
    
    Args:
        invocation_state: Shared state from AgentCore
        
    Returns:
        AgentCoordinator: Global coordinator instance
    """
    global _global_coordinator
    
    if _global_coordinator is None or invocation_state is not None:
        _global_coordinator = AgentCoordinator(invocation_state)
    
    return _global_coordinator


# Export main classes and functions
__all__ = [
    "AgentCoordinator",
    "PatientContextValidator", 
    "get_agent_coordinator"
]
