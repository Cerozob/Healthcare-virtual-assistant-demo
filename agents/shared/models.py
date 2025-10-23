"""
Pydantic models for structured output and data validation.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class AppointmentStatus(str, Enum):
    """Appointment status enumeration."""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class ErrorType(str, Enum):
    """Error type enumeration."""
    API_ERROR = "api_error"
    KNOWLEDGE_BASE_ERROR = "knowledge_base_error"
    STREAMING_ERROR = "streaming_error"
    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    GENERAL_ERROR = "general_error"


class PatientInfoResponse(BaseModel):
    """
    Structured response for patient information queries.
    Used by Information Retrieval Agent for frontend integration.
    """
    
    patient_id: Optional[str] = Field(
        None, 
        description="Unique patient identifier from healthcare system"
    )
    
    full_name: Optional[str] = Field(
        None, 
        description="Patient's full name"
    )
    
    age: Optional[int] = Field(
        None, 
        description="Patient's age in years",
        ge=0,
        le=150
    )
    
    cedula: Optional[str] = Field(
        None,
        description="Patient's identification number (cedula)"
    )
    
    phone: Optional[str] = Field(
        None,
        description="Patient's contact phone number"
    )
    
    email: Optional[str] = Field(
        None,
        description="Patient's email address"
    )
    
    medical_history: Optional[Dict[str, Any]] = Field(
        None,
        description="Relevant medical history and conditions"
    )
    
    lab_results: Optional[Dict[str, Any]] = Field(
        None,
        description="Recent laboratory results and test data"
    )
    
    allergies: Optional[List[str]] = Field(
        None,
        description="Known allergies and adverse reactions"
    )
    
    medications: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Current medications and prescriptions"
    )
    
    conversation_summary: Optional[str] = Field(
        None,
        description="Summary of current conversation context"
    )
    
    knowledge_base_results: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Relevant documents from knowledge base search"
    )
    
    success: bool = Field(
        description="Whether the patient information query was successful"
    )
    
    message: str = Field(
        description="Human-readable response message in appropriate language"
    )
    
    error_type: Optional[ErrorType] = Field(
        None,
        description="Type of error if query failed"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )
    
    @validator('age')
    def validate_age(cls, v):
        if v is not None and (v < 0 or v > 150):
            raise ValueError('Age must be between 0 and 150')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if v is not None and '@' not in v:
            raise ValueError('Invalid email format')
        return v


class AppointmentResponse(BaseModel):
    """
    Structured response for appointment operations.
    Used by Appointment Scheduling Agent for frontend integration.
    """
    
    appointment_id: Optional[str] = Field(
        None,
        description="Unique appointment identifier"
    )
    
    patient_id: Optional[str] = Field(
        None,
        description="Patient identifier"
    )
    
    patient_name: Optional[str] = Field(
        None,
        description="Patient's full name"
    )
    
    medic_id: Optional[str] = Field(
        None,
        description="Assigned medic identifier"
    )
    
    medic_name: Optional[str] = Field(
        None,
        description="Assigned medic's name"
    )
    
    exam_id: Optional[str] = Field(
        None,
        description="Exam type identifier"
    )
    
    exam_name: Optional[str] = Field(
        None,
        description="Exam type name"
    )
    
    appointment_date: Optional[datetime] = Field(
        None,
        description="Scheduled date and time"
    )
    
    duration_minutes: Optional[int] = Field(
        None,
        description="Appointment duration in minutes",
        ge=1,
        le=480  # Max 8 hours
    )
    
    status: Optional[AppointmentStatus] = Field(
        None,
        description="Current appointment status"
    )
    
    location: Optional[str] = Field(
        None,
        description="Appointment location or room"
    )
    
    notes: Optional[str] = Field(
        None,
        description="Additional appointment notes"
    )
    
    available_slots: Optional[List[datetime]] = Field(
        None,
        description="Available time slots for scheduling"
    )
    
    conflicting_appointments: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Conflicting appointments if any"
    )
    
    success: bool = Field(
        description="Whether the appointment operation was successful"
    )
    
    message: str = Field(
        description="Human-readable response message in appropriate language"
    )
    
    error_type: Optional[ErrorType] = Field(
        None,
        description="Type of error if operation failed"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )
    
    @validator('duration_minutes')
    def validate_duration(cls, v):
        if v is not None and (v < 1 or v > 480):
            raise ValueError('Duration must be between 1 and 480 minutes')
        return v
    
    @validator('appointment_date')
    def validate_future_date(cls, v):
        if v is not None and v < datetime.utcnow():
            raise ValueError('Appointment date must be in the future')
        return v


class SessionContext(BaseModel):
    """
    Shared context across all agents in a session.
    Manages conversation state and patient context.
    """
    
    session_id: str = Field(
        description="AgentCore session identifier"
    )
    
    patient_id: Optional[str] = Field(
        None,
        description="Current patient context identifier"
    )
    
    patient_name: Optional[str] = Field(
        None,
        description="Current patient name for context"
    )
    
    medic_id: Optional[str] = Field(
        None,
        description="Current medic identifier"
    )
    
    medic_name: Optional[str] = Field(
        None,
        description="Current medic name"
    )
    
    conversation_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Recent conversation messages"
    )
    
    language_preference: str = Field(
        default="es-LATAM",
        description="User's language preference"
    )
    
    active_documents: List[str] = Field(
        default_factory=list,
        description="Documents uploaded in current session"
    )
    
    patient_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Current patient information context"
    )
    
    last_activity: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last activity timestamp"
    )
    
    session_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional session metadata"
    )
    
    @validator('language_preference')
    def validate_language(cls, v):
        valid_languages = ['es-LATAM', 'es-ES', 'en-US', 'en-GB']
        if v not in valid_languages:
            return 'es-LATAM'  # Default fallback
        return v


class ErrorResponse(BaseModel):
    """
    Standardized error response model for consistent error handling.
    """
    
    success: bool = Field(
        default=False,
        description="Always false for error responses"
    )
    
    message: str = Field(
        description="Human-readable error message"
    )
    
    error_type: ErrorType = Field(
        description="Categorized error type"
    )
    
    error_code: Optional[str] = Field(
        None,
        description="Specific error code for debugging"
    )
    
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error context (sanitized)"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp"
    )
    
    retry_after: Optional[int] = Field(
        None,
        description="Seconds to wait before retry (if applicable)"
    )


class DocumentProcessingStatus(BaseModel):
    """
    Status model for document processing operations.
    """
    
    document_id: str = Field(
        description="Document identifier"
    )
    
    filename: str = Field(
        description="Original filename"
    )
    
    status: str = Field(
        description="Processing status (uploading, processing, completed, failed)"
    )
    
    progress_percentage: Optional[int] = Field(
        None,
        description="Processing progress (0-100)",
        ge=0,
        le=100
    )
    
    message: str = Field(
        description="Status message"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Status timestamp"
    )


class AgentToolResult(BaseModel):
    """
    Result model for agent tool executions.
    """
    
    tool_name: str = Field(
        description="Name of the executed tool"
    )
    
    success: bool = Field(
        description="Whether tool execution was successful"
    )
    
    result: Optional[Union[Dict[str, Any], List[Any], str]] = Field(
        None,
        description="Tool execution result"
    )
    
    error_message: Optional[str] = Field(
        None,
        description="Error message if execution failed"
    )
    
    execution_time_ms: Optional[int] = Field(
        None,
        description="Tool execution time in milliseconds"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Execution timestamp"
    )
