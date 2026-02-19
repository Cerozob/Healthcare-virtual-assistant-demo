"""
Essential Pydantic models for agent system.
Simplified to include only actively used models.
"""

from typing import Optional, Dict, Any, Union, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ErrorType(str, Enum):
    """Error type enumeration for categorizing failures."""
    API_ERROR = "api_error"
    STREAMING_ERROR = "streaming_error"
    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    GENERAL_ERROR = "general_error"


class PatientInfoResponse(BaseModel):
    """
    Structured response for patient information extraction.
    Used by healthcare agent for patient context.
    """
    
    patient_id: Optional[str] = Field(None, description="Patient identifier (cedula or medical record number)")
    full_name: Optional[str] = Field(None, description="Patient's full name")
    cedula: Optional[str] = Field(None, description="Patient's cedula (Colombian ID)")
    age: Optional[int] = Field(None, description="Patient's age if mentioned")
    phone: Optional[str] = Field(None, description="Patient's phone number if mentioned")
    email: Optional[str] = Field(None, description="Patient's email if mentioned")
    success: bool = Field(description="Whether extraction was successful")
    confidence: Optional[str] = Field(None, description="Confidence level of extraction (high/medium/low)")
    
    class Config:
        # Simplified - no complex validation needed
        pass


class SessionContext(BaseModel):
    """
    Shared context across agents in a session.
    Used by Strands session management.
    """
    
    session_id: str = Field(description="Session identifier")
    patient_id: Optional[str] = Field(None, description="Current patient ID")
    patient_name: Optional[str] = Field(None, description="Current patient name")
    language_preference: str = Field(default="es-LATAM", description="Language preference")
    
    class Config:
        # Simplified - Strands handles most session management
        pass


class IdentificationSource(str, Enum):
    """Source of patient identification."""
    TOOL_EXTRACTION = "tool_extraction"  # Direct MCP API calls
    AGENT_EXTRACTION = "agent_extraction"  # Information retrieval agent
    CONTENT_EXTRACTION = "content_extraction"  # Manual text parsing (fallback)
    IMAGE_ANALYSIS = "image_analysis"
    DOCUMENT_ANALYSIS = "document_analysis"
    MULTIMODAL_ANALYSIS = "multimodal_analysis"
    DEFAULT = "default"


class PatientContext(BaseModel):
    """
    Patient context information extracted by the healthcare agent.
    Used in structured output to avoid parsing response text.
    """
    
    patient_id: Optional[str] = Field(
        None, 
        description="Patient identifier (cedula, medical record number, or generated ID)"
    )
    patient_name: Optional[str] = Field(
        None, 
        description="Patient's full name as identified"
    )
    context_changed: bool = Field(
        default=False,
        description="Whether patient context changed in this interaction"
    )
    identification_source: IdentificationSource = Field(
        default=IdentificationSource.DEFAULT,
        description="How the patient was identified"
    )
    file_organization_id: Optional[str] = Field(
        None,
        description="AI-determined ID for file organization in S3, usually the patient id itself"
    )
    confidence_level: Optional[str] = Field(
        None,
        description="Confidence level of patient identification (high/medium/low)"
    )
    additional_identifiers: Optional[Dict[str, str]] = Field(
        None,
        description="Additional patient identifiers found (cedula, medical_record, etc.)"
    )


class HealthcareAgentResponse(BaseModel):
    """
    Structured output model for healthcare agent responses.
    Focuses on patient context extraction - metrics are handled separately by Strands.
    """
    
    response_content: Optional[str] = Field(
        None,
        description="The agent's response in markdown format"
    )
    patient_context: PatientContext = Field(
        default_factory=lambda: PatientContext(),
        description="Extracted patient context information"
    )
    file_processing_summary: Optional[str] = Field(
        None,
        description="Brief summary of any file processing that occurred"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
