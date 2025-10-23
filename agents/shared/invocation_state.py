"""
Shared invocation state management for AgentCore Runtime.
Handles context passing between agents and session management.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import copy
from .utils import get_logger, sanitize_for_logging
from .models import SessionContext

logger = get_logger(__name__)


class InvocationStateManager:
    """
    Manages shared invocation state for AgentCore Runtime.
    Provides context passing between agents and session continuity.
    """
    
    def __init__(self, initial_state: Optional[Dict[str, Any]] = None):
        """
        Initialize invocation state manager.
        
        Args:
            initial_state: Initial state from AgentCore
        """
        self.state = initial_state or {}
        self.logger = logger
        
        # Initialize default state structure
        if "session_context" not in self.state:
            self.state["session_context"] = {}
        
        if "shared_config" not in self.state:
            self.state["shared_config"] = {}
        
        if "agent_history" not in self.state:
            self.state["agent_history"] = []
    
    def get_session_context(self) -> Dict[str, Any]:
        """
        Get current session context.
        
        Returns:
            Dict[str, Any]: Session context
        """
        return self.state.get("session_context", {})
    
    def update_session_context(self, updates: Dict[str, Any]) -> None:
        """
        Update session context with new data.
        
        Args:
            updates: Context updates to apply
        """
        session_context = self.get_session_context()
        session_context.update(updates)
        session_context["last_updated"] = datetime.utcnow().isoformat()
        
        self.state["session_context"] = session_context
        
        # Log update (sanitized)
        sanitized_updates = sanitize_for_logging(updates)
        self.logger.debug(f"Session context updated: {sanitized_updates}")
    
    def get_patient_context(self) -> Optional[Dict[str, Any]]:
        """
        Get current patient context from session.
        
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
        session_context["patient_context"]["set_at"] = datetime.utcnow().isoformat()
        
        self.update_session_context(session_context)
        self.logger.info("Patient context set for session")
    
    def clear_patient_context(self) -> None:
        """Clear patient context from session."""
        session_context = self.get_session_context()
        if "patient_context" in session_context:
            del session_context["patient_context"]
            self.update_session_context(session_context)
            self.logger.info("Patient context cleared from session")
    
    def get_shared_config(self) -> Dict[str, Any]:
        """
        Get shared configuration for all agents.
        
        Returns:
            Dict[str, Any]: Shared configuration
        """
        return self.state.get("shared_config", {})
    
    def set_shared_config(self, config: Dict[str, Any]) -> None:
        """
        Set shared configuration for all agents.
        
        Args:
            config: Configuration to share
        """
        self.state["shared_config"] = config
        self.logger.debug("Shared configuration updated")
    
    def add_agent_execution(
        self, 
        agent_name: str, 
        input_data: Any, 
        output_data: Any,
        execution_time_ms: Optional[int] = None
    ) -> None:
        """
        Record agent execution in history.
        
        Args:
            agent_name: Name of the executed agent
            input_data: Input provided to agent (will be sanitized)
            output_data: Output from agent (will be sanitized)
            execution_time_ms: Execution time in milliseconds
        """
        execution_record = {
            "agent_name": agent_name,
            "timestamp": datetime.utcnow().isoformat(),
            "input_data": sanitize_for_logging(input_data),
            "output_data": sanitize_for_logging(output_data),
            "execution_time_ms": execution_time_ms
        }
        
        agent_history = self.state.get("agent_history", [])
        agent_history.append(execution_record)
        
        # Keep only last 50 executions to manage memory
        if len(agent_history) > 50:
            agent_history = agent_history[-50:]
        
        self.state["agent_history"] = agent_history
        self.logger.debug(f"Agent execution recorded: {agent_name}")
    
    def get_agent_history(self, agent_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get agent execution history.
        
        Args:
            agent_name: Filter by specific agent name
            
        Returns:
            List[Dict[str, Any]]: Agent execution history
        """
        history = self.state.get("agent_history", [])
        
        if agent_name:
            history = [record for record in history if record.get("agent_name") == agent_name]
        
        return history
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        Get conversation history from session context.
        
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
            content: Message content (will be sanitized for logging)
            metadata: Additional metadata
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        session_context = self.get_session_context()
        conversation_history = session_context.get("conversation_history", [])
        conversation_history.append(message)
        
        # Keep only last 100 messages to manage memory
        if len(conversation_history) > 100:
            conversation_history = conversation_history[-100:]
        
        session_context["conversation_history"] = conversation_history
        self.update_session_context(session_context)
        
        # Log message addition (sanitized)
        sanitized_content = sanitize_for_logging(content)
        self.logger.debug(f"Conversation message added: {role} - {len(sanitized_content)} chars")
    
    def get_active_documents(self) -> List[str]:
        """
        Get list of active documents in session.
        
        Returns:
            List[str]: Document identifiers
        """
        session_context = self.get_session_context()
        return session_context.get("active_documents", [])
    
    def add_active_document(self, document_id: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add document to active documents list.
        
        Args:
            document_id: Document identifier
            metadata: Document metadata
        """
        session_context = self.get_session_context()
        active_docs = session_context.get("active_documents", [])
        
        document_entry = {
            "document_id": document_id,
            "added_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        # Check if document already exists
        existing_doc = next(
            (doc for doc in active_docs if doc.get("document_id") == document_id), 
            None
        )
        
        if not existing_doc:
            active_docs.append(document_entry)
            session_context["active_documents"] = active_docs
            self.update_session_context(session_context)
            self.logger.info(f"Document added to session: {document_id}")
    
    def remove_active_document(self, document_id: str) -> None:
        """
        Remove document from active documents list.
        
        Args:
            document_id: Document identifier
        """
        session_context = self.get_session_context()
        active_docs = session_context.get("active_documents", [])
        
        updated_docs = [
            doc for doc in active_docs 
            if doc.get("document_id") != document_id
        ]
        
        if len(updated_docs) != len(active_docs):
            session_context["active_documents"] = updated_docs
            self.update_session_context(session_context)
            self.logger.info(f"Document removed from session: {document_id}")
    
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
        self.update_session_context(session_context)
        self.logger.info(f"Language preference set: {language}")
    
    def export_state(self) -> Dict[str, Any]:
        """
        Export current state for AgentCore persistence.
        
        Returns:
            Dict[str, Any]: Current state
        """
        return copy.deepcopy(self.state)
    
    def import_state(self, state: Dict[str, Any]) -> None:
        """
        Import state from AgentCore.
        
        Args:
            state: State to import
        """
        self.state = copy.deepcopy(state)
        
        # Ensure required structure exists
        if "session_context" not in self.state:
            self.state["session_context"] = {}
        
        if "shared_config" not in self.state:
            self.state["shared_config"] = {}
        
        if "agent_history" not in self.state:
            self.state["agent_history"] = []
        
        self.logger.debug("Invocation state imported")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get summary of current session state.
        
        Returns:
            Dict[str, Any]: Session summary
        """
        session_context = self.get_session_context()
        
        summary = {
            "session_id": session_context.get("session_id", "unknown"),
            "language_preference": self.get_language_preference(),
            "has_patient_context": bool(self.get_patient_context()),
            "conversation_messages": len(self.get_conversation_history()),
            "active_documents": len(self.get_active_documents()),
            "agent_executions": len(self.get_agent_history()),
            "last_activity": session_context.get("last_updated"),
            "created_at": session_context.get("created_at", datetime.utcnow().isoformat())
        }
        
        return summary
    
    def cleanup_old_data(self, max_age_hours: int = 24) -> None:
        """
        Clean up old data from state to manage memory.
        
        Args:
            max_age_hours: Maximum age of data to keep in hours
        """
        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        
        # Clean up old agent history
        agent_history = self.get_agent_history()
        cleaned_history = []
        
        for record in agent_history:
            try:
                record_time = datetime.fromisoformat(record["timestamp"]).timestamp()
                if record_time > cutoff_time:
                    cleaned_history.append(record)
            except (ValueError, KeyError):
                # Keep records with invalid timestamps
                cleaned_history.append(record)
        
        if len(cleaned_history) != len(agent_history):
            self.state["agent_history"] = cleaned_history
            self.logger.info(f"Cleaned up {len(agent_history) - len(cleaned_history)} old agent records")


def create_invocation_state_manager(
    initial_state: Optional[Dict[str, Any]] = None
) -> InvocationStateManager:
    """
    Factory function to create invocation state manager.
    
    Args:
        initial_state: Initial state from AgentCore
        
    Returns:
        InvocationStateManager: Configured state manager
    """
    return InvocationStateManager(initial_state)
