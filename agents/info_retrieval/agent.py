"""
Information Retrieval Agent using Strands "Agents as Tools" pattern.
Handles patient information queries and medical document searches using Bedrock Knowledge Base.
"""

from typing import Dict, Any, Optional

# Strands Agents imports
try:
    from strands import Agent, tool
    from strands.models import BedrockModel
except ImportError:
    # Placeholder for development
    def tool(func):
        return func
    
    class Agent:
        def __init__(self, *args, **kwargs):
            pass
        
        def __call__(self, *args, **kwargs):
            return "Placeholder response"
    
    class BedrockModel:
        def __init__(self, *args, **kwargs):
            pass

from ..shared.config import get_agent_config, get_model_config
from ..shared.utils import get_logger
from ..shared.prompts import get_prompt
from ..shared.mcp_gateway_tools import (
    get_patient_by_id_mcp, list_patients_mcp, query_patients_mcp
)
from ..shared.knowledge_base_tools import search_medical_knowledge, search_patient_info

logger = get_logger(__name__)


# Strands "Agents as Tools" implementation
@tool
async def information_retrieval_agent(query: str) -> str:
    """
    Process and respond to information retrieval queries using Bedrock Knowledge Base.
    
    This agent specializes in:
    - Patient information searches
    - Medical document retrieval from Bedrock Knowledge Base
    - Healthcare data queries
    
    Args:
        query: Information query requiring patient data or medical knowledge
        
    Returns:
        str: Detailed information response with sources when available
    """
    try:
        logger.debug(f"Information retrieval agent processing query: {query[:100]}...")
        logger.info("Information retrieval agent processing query")
        
        # Get configuration
        config = get_agent_config()
        model_config = get_model_config()
        
        # Load system prompt from file
        system_prompt = get_prompt("information_retrieval")
        
        # Create specialized agent with tools for information retrieval and Bedrock Guardrails
        info_agent = Agent(
            system_prompt=system_prompt,
            tools=[
                _search_patient_tool,
                _search_medical_knowledge_tool, 
                _search_patient_info_tool
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
        
        # Process the query
        response = info_agent(query)
        return str(response)
        
    except Exception as e:
        logger.error(f"Error in information retrieval agent: {str(e)}")
        return f"❌ Error en agente de información: {str(e)}"


# Tool implementations for the information retrieval agent
async def _search_patient_tool(
    search_term: str,
    search_type: str = "name"
) -> Dict[str, Any]:
    """Search for patients by name, ID, or cedula using MCP Gateway."""
    try:
        if search_type == "id":
            result = await get_patient_by_id_mcp(search_term)
            if result.success:
                patient_data = result.result
                return {
                    "success": True,
                    "patients": [patient_data.get("patient", {})],
                    "message": f"👤 Paciente encontrado"
                }
        else:
            # For name/cedula searches, get all patients and filter
            # Note: This is a simplified approach - in production you'd want server-side filtering
            result = await list_patients_mcp(limit=100)
            if result.success:
                patients_data = result.result
                all_patients = patients_data.get("patients", [])
                
                # Filter patients based on search term and type
                filtered_patients = []
                for patient in all_patients:
                    if search_type == "name" and search_term.lower() in patient.get("full_name", "").lower():
                        filtered_patients.append(patient)
                    elif search_type == "cedula" and search_term in str(patient.get("cedula", "")):
                        filtered_patients.append(patient)
                
                return {
                    "success": True,
                    "patients": filtered_patients,
                    "message": f"👤 {len(filtered_patients)} pacientes encontrados"
                }
        
        return {
            "success": False,
            "message": "❌ No se encontraron pacientes"
        }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Error buscando pacientes: {str(e)}"
        }


async def _search_medical_knowledge_tool(
    query: str,
    document_type: Optional[str] = None,
    max_results: int = 5
) -> Dict[str, Any]:
    """Search medical knowledge using Bedrock Knowledge Base."""
    try:
        result = await search_medical_knowledge(
            query=query,
            document_type=document_type,
            max_results=max_results
        )
        
        if result.get("success"):
            results = result.get("results", [])
            return {
                "success": True,
                "documents": results,
                "message": f"📄 {len(results)} documentos encontrados en base de conocimiento"
            }
        else:
            return {
                "success": False,
                "message": f"❌ No se encontraron documentos: {result.get('error', 'Error')}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Error en búsqueda médica: {str(e)}"
        }


async def _search_patient_info_tool(
    patient_query: str,
    max_results: int = 3
) -> Dict[str, Any]:
    """Search patient information using Bedrock Knowledge Base."""
    try:
        result = await search_patient_info(
            patient_query=patient_query,
            max_results=max_results
        )
        
        if result.get("success"):
            results = result.get("results", [])
            return {
                "success": True,
                "information": results,
                "message": f"📋 {len(results)} resultados de información de pacientes"
            }
        else:
            return {
                "success": False,
                "message": f"❌ No se encontró información: {result.get('error', 'Error')}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Error buscando información: {str(e)}"
        }


# Export the tool function
__all__ = ["information_retrieval_agent"]
