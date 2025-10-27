"""
Simplified Bedrock Knowledge Base integration for healthcare assistant.
Uses managed Bedrock Knowledge Base instead of custom retrieval logic.
"""

import boto3
from typing import Dict, Any, List, Optional
from datetime import datetime
from botocore.exceptions import ClientError
from .config import get_agent_config
from .utils import get_logger

logger = get_logger(__name__)


class BedrockKnowledgeBaseManager:
    """
    Manages Bedrock Knowledge Base integration for document retrieval.
    Uses AWS managed knowledge base instead of custom retrieval logic.
    """
    
    def __init__(self):
        """Initialize Bedrock Knowledge Base manager."""
        self.config = get_agent_config()
        self.logger = logger
        
        # Initialize Bedrock Agent Runtime client
        self.bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
        
        # Knowledge Base configuration
        self.knowledge_base_id = self.config.knowledge_base_id
        
        # Track usage
        self.usage_stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "last_used": None
        }
    
    async def search_knowledge_base(
        self,
        query: str,
        max_results: int = 5,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search the Bedrock Knowledge Base.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            filter_criteria: Optional filter criteria
            
        Returns:
            Dict[str, Any]: Search results
        """
        if not self.knowledge_base_id:
            return {
                "success": False,
                "error": "Knowledge Base not configured",
                "results": []
            }
        
        try:
            self.usage_stats["total_queries"] += 1
            self.usage_stats["last_used"] = datetime.utcnow().isoformat()
            
            # Prepare retrieval configuration
            retrieval_config = {
                "vectorSearchConfiguration": {
                    "numberOfResults": max_results
                }
            }
            
            # Add filter if provided
            if filter_criteria:
                retrieval_config["vectorSearchConfiguration"]["filter"] = filter_criteria
            
            # Query the knowledge base
            response = self.bedrock_agent_runtime.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={
                    "text": query
                },
                retrievalConfiguration=retrieval_config
            )
            
            # Process results
            retrieval_results = response.get("retrievalResults", [])
            
            processed_results = []
            for result in retrieval_results:
                content = result.get("content", {})
                location = result.get("location", {})
                
                processed_results.append({
                    "content": content.get("text", ""),
                    "score": result.get("score", 0.0),
                    "source": location.get("s3Location", {}).get("uri", ""),
                    "metadata": result.get("metadata", {})
                })
            
            self.usage_stats["successful_queries"] += 1
            
            return {
                "success": True,
                "results": processed_results,
                "total_results": len(processed_results),
                "query": query,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            self.logger.error(f"Bedrock Knowledge Base error: {str(e)}")
            self.usage_stats["failed_queries"] += 1
            
            return {
                "success": False,
                "error": f"Knowledge Base query failed: {str(e)}",
                "results": []
            }
        
        except Exception as e:
            self.logger.error(f"Unexpected Knowledge Base error: {str(e)}")
            self.usage_stats["failed_queries"] += 1
            
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "results": []
            }
    
    async def search_medical_documents(
        self,
        query: str,
        document_type: Optional[str] = None,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Search for medical documents in the knowledge base.
        
        Args:
            query: Medical query
            document_type: Optional document type filter
            max_results: Maximum results to return
            
        Returns:
            Dict[str, Any]: Search results
        """
        # Prepare filter for medical documents
        filter_criteria = None
        if document_type:
            filter_criteria = {
                "equals": {
                    "key": "document_type",
                    "value": document_type
                }
            }
        
        # Add medical context to query
        medical_query = f"Información médica: {query}"
        
        return await self.search_knowledge_base(
            query=medical_query,
            max_results=max_results,
            filter_criteria=filter_criteria
        )
    
    async def search_patient_information(
        self,
        patient_query: str,
        max_results: int = 3
    ) -> Dict[str, Any]:
        """
        Search for patient-related information.
        
        Args:
            patient_query: Patient-related query
            max_results: Maximum results to return
            
        Returns:
            Dict[str, Any]: Search results
        """
        # Filter for patient information documents
        filter_criteria = {
            "equals": {
                "key": "category",
                "value": "patient_information"
            }
        }
        
        return await self.search_knowledge_base(
            query=patient_query,
            max_results=max_results,
            filter_criteria=filter_criteria
        )
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get knowledge base usage statistics.
        
        Returns:
            Dict[str, Any]: Usage statistics
        """
        return {
            **self.usage_stats,
            "knowledge_base_id": self.knowledge_base_id,
            "configured": bool(self.knowledge_base_id)
        }


# Global knowledge base manager instance
_global_kb_manager = None


def get_knowledge_base_manager() -> BedrockKnowledgeBaseManager:
    """
    Get global knowledge base manager instance.
    
    Returns:
        BedrockKnowledgeBaseManager: Global KB manager
    """
    global _global_kb_manager
    
    if _global_kb_manager is None:
        _global_kb_manager = BedrockKnowledgeBaseManager()
    
    return _global_kb_manager


# Tool functions for Strands agents
async def search_medical_knowledge(
    query: str,
    document_type: Optional[str] = None,
    max_results: int = 5
) -> Dict[str, Any]:
    """
    Tool function to search medical knowledge base.
    
    Args:
        query: Medical query
        document_type: Optional document type
        max_results: Maximum results
        
    Returns:
        Dict[str, Any]: Search results
    """
    kb_manager = get_knowledge_base_manager()
    return await kb_manager.search_medical_documents(
        query=query,
        document_type=document_type,
        max_results=max_results
    )


async def search_patient_info(
    patient_query: str,
    max_results: int = 3
) -> Dict[str, Any]:
    """
    Tool function to search patient information.
    
    Args:
        patient_query: Patient-related query
        max_results: Maximum results
        
    Returns:
        Dict[str, Any]: Search results
    """
    kb_manager = get_knowledge_base_manager()
    return await kb_manager.search_patient_information(
        patient_query=patient_query,
        max_results=max_results
    )


# Export main classes and functions
__all__ = [
    "BedrockKnowledgeBaseManager",
    "get_knowledge_base_manager", 
    "search_medical_knowledge",
    "search_patient_info"
]
