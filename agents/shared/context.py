"""
Simplified context management for shared agent state.
"""

from typing import Any, Dict, Optional, List
from datetime import datetime
from .utils import get_logger

logger = get_logger(__name__)


class SimpleContextManager:
    """
    Simplified context manager for Strands agents.
    Uses invocation_state for shared context between agents.
    """
    
    def __init__(self, invocation_state: Optional[Dict[str, Any]] = None):
        """Initialize context manager with shared state."""
        self.state = invocation_state or {}
        self.logger = logger
        
        # Ensure basic structure exists
        if "session_context" not in self.state:
            self.state["session_context"] = {}
    
    def get_patient_context(self) -> Optional[Dict[str, Any]]:
        """Get current patient context."""
        return self.state.get("session_context", {}).get("patient_context")
    
    def set_patient_context(self, patient_data: Dict[str, Any]) -> None:
        """Set patient context for the session."""
        if "session_context" not in self.state:
            self.state["session_context"] = {}
        
        self.state["session_context"]["patient_context"] = {
            **patient_data,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        self.logger.info("Patient context updated")
    
    def get_language_preference(self) -> str:
        """Get user's language preference (default: es-LATAM)."""
        return self.state.get("session_context", {}).get("language_preference", "es-LATAM")
    
    def set_language_preference(self, language: str) -> None:
        """Set user's language preference."""
        if "session_context" not in self.state:
            self.state["session_context"] = {}
        
        self.state["session_context"]["language_preference"] = language
        self.logger.info(f"Language preference set: {language}")
    
    def add_conversation_message(self, role: str, content: str) -> None:
        """Add message to conversation history."""
        if "session_context" not in self.state:
            self.state["session_context"] = {}
        
        if "conversation_history" not in self.state["session_context"]:
            self.state["session_context"]["conversation_history"] = []
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        history = self.state["session_context"]["conversation_history"]
        history.append(message)
        
        # Keep only last 20 messages
        if len(history) > 20:
            self.state["session_context"]["conversation_history"] = history[-20:]
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history."""
        return self.state.get("session_context", {}).get("conversation_history", [])
    
    def clear_patient_context(self) -> None:
        """Clear patient context from session."""
        if "session_context" in self.state and "patient_context" in self.state["session_context"]:
            del self.state["session_context"]["patient_context"]
            self.logger.info("Patient context cleared")


# Global context manager instance
_context_manager = None


def get_context_manager(invocation_state: Optional[Dict[str, Any]] = None) -> SimpleContextManager:
    """Get or create global context manager instance."""
    global _context_manager
    
    if _context_manager is None or invocation_state is not None:
        _context_manager = SimpleContextManager(invocation_state)
    
    return _context_manager
