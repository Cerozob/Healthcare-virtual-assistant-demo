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
    
    patient_id: Optional[str] = Field(None, description="Patient identifier")
    full_name: Optional[str] = Field(None, description="Patient's full name")
    cedula: Optional[str] = Field(None, description="Patient's cedula")
    success: bool = Field(description="Whether extraction was successful")
    
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
