"""
Context management for shared agent state and communication.
"""

from typing import Any, Dict, Optional, List
from datetime import datetime
import json
from .utils import get_logger, sanitize_for_logging

logger = get_logger(__name__)


class ContextManager:
    """
    Manages shared context between agents using invocation_state.
    """
    
    def __init__(self, invocation_state: Optional[Dict[str, Any]] = None):
        """
        Initialize context manager.
        
        Args:
            invocation_state: Shared state from AgentCore
        """
        self.state = invocation_state or {}
        self.logger = logger
    
    def get_session_context(self) -> Dict[str, Any]:
        """
        Get current session context.
        
        Returns:
            Dict[str, Any]: Session context
        """
        return self.state.get("session_context", {})
    
    def set_session_context(self, context: Dict[str, Any]) -> None:
        """
        Set session context.
        
        Args:
            context: Session context to set
        """
        if "session_context" not in self.state:
            self.state["session_context"] = {}
        
        self.state["session_context"].update(context)
        
        # Log context update (sanitized)
        sanitized_context = sanitize_for_logging(context)
        self.logger.info(f"Updated session context: {sanitized_context}")
    
    def get_patient_context(self) -> Optional[Dict[str, Any]]:
        """
        Get current patient context.
        
        Returns:
            Optional[Dict[str, Any]]: Patient context if available
        """
        session_context = self.get_session_context()
        return session_context.get("patient_context")
    
    def set_patient_context(self, patient_data: Dict[str, Any]) -> None:
        """
        Set patient context for the session.
        
        Args:
            patient_data: Patient information
        """
        session_context = self.get_session_context()
        session_context["patient_context"] = patient_data
        session_context["patient_context"]["updated_at"] = datetime.utcnow().isoformat()
        
        self.set_session_context(session_context)
        
        # Log patient context set (without PII)
        self.logger.info("Patient context updated for session")
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        Get conversation history.
        
        Returns:
            List[Dict[str, Any]]: Conversation messages
        """
        session_context = self.get_session_context()
        return session_context.get("conversation_history", [])
    
    def add_conversation_message(
        self, 
        role: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add message to conversation history.
        
        Args:
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Additional metadata
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        conversation_history = self.get_conversation_history()
        conversation_history.append(message)
        
        # Keep only last 20 messages to manage memory
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]
        
        session_context = self.get_session_context()
        session_context["conversation_history"] = conversation_history
        self.set_session_context(session_context)
    
    def get_language_preference(self) -> str:
        """
        Get user's language preference.
        
        Returns:
            str: Language code (default: es-LATAM)
        """
        session_context = self.get_session_context()
        return session_context.get("language_preference", "es-LATAM")
    
    def set_language_preference(self, language: str) -> None:
        """
        Set user's language preference.
        
        Args:
            language: Language code
        """
        session_context = self.get_session_context()
        session_context["language_preference"] = language
        self.set_session_context(session_context)
    
    def get_active_documents(self) -> List[str]:
        """
        Get list of active documents in session.
        
        Returns:
            List[str]: Document identifiers
        """
        session_context = self.get_session_context()
        return session_context.get("active_documents", [])
    
    def add_active_document(self, document_id: str) -> None:
        """
        Add document to active documents list.
        
        Args:
            document_id: Document identifier
        """
        active_docs = self.get_active_documents()
        if document_id not in active_docs:
            active_docs.append(document_id)
            
            session_context = self.get_session_context()
            session_context["active_documents"] = active_docs
            self.set_session_context(session_context)
            
            self.logger.info(f"Added document to session: {document_id}")
    
    def clear_patient_context(self) -> None:
        """
        Clear patient context from session.
        """
        session_context = self.get_session_context()
        if "patient_context" in session_context:
            del session_context["patient_context"]
            self.set_session_context(session_context)
            self.logger.info("Patient context cleared from session")
    
    def get_shared_tools_config(self) -> Dict[str, Any]:
        """
        Get shared tools configuration.
        
        Returns:
            Dict[str, Any]: Tools configuration
        """
        return self.state.get("tools_config", {})
    
    def set_shared_tools_config(self, config: Dict[str, Any]) -> None:
        """
        Set shared tools configuration.
        
        Args:
            config: Tools configuration
        """
        self.state["tools_config"] = config
        self.logger.info("Shared tools configuration updated")
    
    def export_state(self) -> Dict[str, Any]:
        """
        Export current state for persistence.
        
        Returns:
            Dict[str, Any]: Current state
        """
        return self.state.copy()
    
    def import_state(self, state: Dict[str, Any]) -> None:
        """
        Import state from persistence.
        
        Args:
            state: State to import
        """
        self.state = state.copy()
        self.logger.info("Context state imported")
