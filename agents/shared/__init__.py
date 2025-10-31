"""
Simplified shared utilities for agent communication.
"""

from .config import AgentConfig, get_agent_config, get_model_config
from .models import PatientInfoResponse, SessionContext, ErrorType
from .utils import get_logger, sanitize_for_logging, extract_patient_context
from .prompts import get_prompt

__all__ = [
    "AgentConfig",
    "get_agent_config",
    "get_model_config",
    "PatientInfoResponse",
    "SessionContext",
    "ErrorType",
    "get_logger",
    "sanitize_for_logging",
    "extract_patient_context",
    "get_prompt",
]
