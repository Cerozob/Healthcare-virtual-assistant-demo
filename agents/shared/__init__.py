"""
Simplified shared utilities for agent communication.
"""

from .config import AgentConfig, get_agent_config
from .models import (
    PatientInfoResponse,
    AppointmentResponse,
    SessionContext,
    ErrorResponse,
)
from .context import SimpleContextManager, get_context_manager
from .utils import get_logger, format_response, sanitize_for_logging

from .knowledge_base_tools import (
    BedrockKnowledgeBaseManager,
    get_knowledge_base_manager,
    search_medical_knowledge,
    search_patient_info
)
from .prompts import get_prompt, load_prompt

__all__ = [
    "AgentConfig",
    "get_agent_config",
    "PatientInfoResponse",
    "AppointmentResponse", 
    "SessionContext",
    "ErrorResponse",
    "SimpleContextManager",
    "get_context_manager",
    "get_logger",
    "format_response",
    "sanitize_for_logging",

    "BedrockKnowledgeBaseManager",
    "get_knowledge_base_manager",
    "search_medical_knowledge",
    "search_patient_info",
    "get_prompt",
    "load_prompt",
]
