"""
Simplified patient lookup tool for healthcare assistant.
Uses LLM to extract patient information. Database queries are handled by MCP Gateway tools.
"""

import logging
from typing import Optional, Dict, Any
from strands import tool, Agent
from pydantic import BaseModel, Field
from shared.prompts import get_prompt

logger = logging.getLogger(__name__)

class PatientInfo(BaseModel):
    """Patient information extracted from natural language."""
    cedula: Optional[str] = Field(None, description="Patient cedula number")
    first_name: Optional[str] = Field(None, description="Patient first name")
    last_name: Optional[str] = Field(None, description="Patient last name")
    full_name: Optional[str] = Field(None, description="Patient full name")
    medical_record_number: Optional[str] = Field(None, description="Medical record number")
    has_patient_info: bool = Field(False, description="True if patient info found in message")

# Create extraction agent
extraction_agent = Agent(
    system_prompt=get_prompt("patient_extraction"),
    callback_handler=None
)

@tool(
    name="extract_patient_info",
    description="Extract patient information from natural language using LLM"
)
def extract_patient_info(user_message: str, tool_context=None) -> Dict[str, Any]:
    """
    Extract patient information using LLM structured output.
    Database queries should be done using MCP Gateway tools.
    
    Args:
        user_message: User's message containing patient information
        tool_context: Tool execution context
        
    Returns:
        Dict containing extracted patient information
    """
    try:
        logger.info(f"Extracting patient info: {user_message[:100]}...")
        
        if not user_message.strip():
            return {"success": False, "error": "Message cannot be empty", "extracted_info": None}
        
        # Extract patient info using LLM
        extraction_prompt = get_prompt("patient_analysis").format(user_message=user_message)
        patient_info = extraction_agent.structured_output(
            output_model=PatientInfo,
            prompt=extraction_prompt
        )
        
        logger.info(f"Extracted patient info: {patient_info}")
        
        if not patient_info.has_patient_info:
            return {
                "success": False,
                "error": "No patient information found in message",
                "extracted_info": None
            }
        
        # Prepare extracted data
        extracted_data = {}
        for field, value in patient_info.model_dump().items():
            if value and field not in ["has_patient_info"]:
                extracted_data[field] = value
        
        if not extracted_data:
            return {
                "success": False,
                "error": "No searchable patient information extracted",
                "extracted_info": None
            }
        
        return {
            "success": True,
            "extracted_info": extracted_data,
            "message": f"Extracted patient information: {extracted_data}"
        }
            
    except Exception as e:
        logger.error(f"Error extracting patient info: {e}")
        return {
            "success": False,
            "error": f"Patient info extraction failed: {str(e)}",
            "extracted_info": None
        }
