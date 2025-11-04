"""
Memory Logger - CloudWatch logging for AgentCore Memory operations
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)


class MemoryOperationLogger:
    """Logger for AgentCore Memory operations with CloudWatch structured logging."""
    
    @staticmethod
    def log_memory_operation(operation: str, session_id: str, data: Dict[str, Any] = None):
        """Log memory operations with structured data for CloudWatch."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": f"AGENTCORE_MEMORY_{operation}",
            "session_id": session_id,
            "component": "memory_operations",
            **(data or {})
        }
        logger.info(f"AGENTCORE_MEMORY: {json.dumps(log_entry)}")
    
    @staticmethod
    def log_retrieval_operation(operation: str, session_id: str, namespace: str, 
                              results_count: int = 0, data: Dict[str, Any] = None):
        """Log memory retrieval operations."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": f"MEMORY_RETRIEVAL_{operation}",
            "session_id": session_id,
            "namespace": namespace,
            "results_count": results_count,
            "component": "memory_retrieval",
            **(data or {})
        }
        logger.info(f"MEMORY_RETRIEVAL: {json.dumps(log_entry)}")
    
    @staticmethod
    def log_session_operation(operation: str, session_id: str, data: Dict[str, Any] = None):
        """Log session-related operations."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": f"SESSION_{operation}",
            "session_id": session_id,
            "component": "session_management",
            **(data or {})
        }
        logger.info(f"SESSION_MANAGEMENT: {json.dumps(log_entry)}")


def log_memory_calls(session_id: str):
    """Decorator to log memory-related function calls."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            operation_name = func.__name__.upper()
            start_time = datetime.utcnow()
            
            MemoryOperationLogger.log_memory_operation(
                f"{operation_name}_START", 
                session_id, 
                {
                    "function": func.__name__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys())
                }
            )
            
            try:
                result = await func(*args, **kwargs)
                
                end_time = datetime.utcnow()
                duration_ms = (end_time - start_time).total_seconds() * 1000
                
                MemoryOperationLogger.log_memory_operation(
                    f"{operation_name}_SUCCESS", 
                    session_id, 
                    {
                        "function": func.__name__,
                        "duration_ms": duration_ms,
                        "result_type": type(result).__name__
                    }
                )
                
                return result
                
            except Exception as e:
                end_time = datetime.utcnow()
                duration_ms = (end_time - start_time).total_seconds() * 1000
                
                MemoryOperationLogger.log_memory_operation(
                    f"{operation_name}_ERROR", 
                    session_id, 
                    {
                        "function": func.__name__,
                        "duration_ms": duration_ms,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            operation_name = func.__name__.upper()
            start_time = datetime.utcnow()
            
            MemoryOperationLogger.log_memory_operation(
                f"{operation_name}_START", 
                session_id, 
                {
                    "function": func.__name__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys())
                }
            )
            
            try:
                result = func(*args, **kwargs)
                
                end_time = datetime.utcnow()
                duration_ms = (end_time - start_time).total_seconds() * 1000
                
                MemoryOperationLogger.log_memory_operation(
                    f"{operation_name}_SUCCESS", 
                    session_id, 
                    {
                        "function": func.__name__,
                        "duration_ms": duration_ms,
                        "result_type": type(result).__name__
                    }
                )
                
                return result
                
            except Exception as e:
                end_time = datetime.utcnow()
                duration_ms = (end_time - start_time).total_seconds() * 1000
                
                MemoryOperationLogger.log_memory_operation(
                    f"{operation_name}_ERROR", 
                    session_id, 
                    {
                        "function": func.__name__,
                        "duration_ms": duration_ms,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )
                raise
        
        # Return appropriate wrapper based on whether function is async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Memory debugging utilities
class MemoryDebugger:
    """Utilities for debugging memory operations."""
    
    @staticmethod
    def log_memory_state(session_id: str, state_name: str, memory_data: Dict[str, Any]):
        """Log current memory state for debugging."""
        MemoryOperationLogger.log_memory_operation(
            f"STATE_{state_name}", 
            session_id, 
            {
                "state_name": state_name,
                "memory_keys": list(memory_data.keys()) if memory_data else [],
                "memory_size": len(str(memory_data)) if memory_data else 0
            }
        )
    
    @staticmethod
    def log_context_retrieval(session_id: str, query: str, results: list, namespace: str):
        """Log context retrieval operations."""
        MemoryOperationLogger.log_retrieval_operation(
            "CONTEXT_RETRIEVED",
            session_id,
            namespace,
            len(results),
            {
                "query_length": len(query),
                "query_preview": query[:100],
                "results_preview": [str(r)[:50] for r in results[:3]] if results else []
            }
        )
    
    @staticmethod
    def log_session_continuity(session_id: str, previous_session: Optional[str], 
                             context_found: bool, context_count: int):
        """Log session continuity information."""
        MemoryOperationLogger.log_session_operation(
            "CONTINUITY_CHECK",
            session_id,
            {
                "previous_session": previous_session,
                "context_found": context_found,
                "context_count": context_count,
                "is_new_session": previous_session is None
            }
        )
