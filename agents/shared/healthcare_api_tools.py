"""
Healthcare API integration tools for Strands Agents.
Provides tools for querying patient information, scheduling appointments, and managing healthcare data.
"""

import httpx
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import json
from .config import get_agent_config
from .models import ErrorType, AgentToolResult
from .utils import get_logger, create_error_response, sanitize_for_logging

logger = get_logger(__name__)


class HealthcareAPIClient:
    """
    HTTP client for Healthcare API integration with retry logic and error handling.
    """
    
    def __init__(self):
        """Initialize the Healthcare API client."""
        self.config = get_agent_config()
        self.base_url = self.config.healthcare_api_endpoint.rstrip('/')
        self.timeout = 30.0
        self.max_retries = 3
        
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic and error handling.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            
        Returns:
            Dict[str, Any]: API response
            
        Raises:
            Exception: If request fails after retries
        """
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    # Sanitize data for logging
                    sanitized_data = sanitize_for_logging(data) if data else None
                    sanitized_params = sanitize_for_logging(params) if params else None
                    
                    logger.info(f"Making {method} request to {endpoint} (attempt {attempt + 1})")
                    logger.debug(f"Request data: {sanitized_data}, params: {sanitized_params}")
                    
                    response = await client.request(
                        method=method,
                        url=url,
                        json=data,
                        params=params,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    response.raise_for_status()
                    result = response.json()
                    
                    logger.info(f"Request successful: {response.status_code}")
                    return result
                    
                except httpx.HTTPStatusError as e:
                    logger.error(f"HTTP error on attempt {attempt + 1}: {e.response.status_code} - {e.response.text}")
                    if e.response.status_code in [400, 401, 403, 404]:
                        # Don't retry client errors
                        raise Exception(f"API error: {e.response.status_code} - {e.response.text}")
                    
                    if attempt == self.max_retries - 1:
                        raise Exception(f"API request failed after {self.max_retries} attempts: {str(e)}")
                        
                except Exception as e:
                    logger.error(f"Request error on attempt {attempt + 1}: {str(e)}")
                    if attempt == self.max_retries - 1:
                        raise Exception(f"API request failed after {self.max_retries} attempts: {str(e)}")
                
                # Wait before retry
                await asyncio.sleep(2 ** attempt)


# Initialize API client
api_client = HealthcareAPIClient()


async def query_patient_api(
    patient_identifier: str,
    identifier_type: str = "auto"
) -> AgentToolResult:
    """
    Query patient information from Healthcare API.
    
    Args:
        patient_identifier: Patient ID, name, or cedula
        identifier_type: Type of identifier (id, name, cedula, auto)
        
    Returns:
        AgentToolResult: Patient information or error
    """
    start_time = datetime.utcnow()
    
    try:
        logger.info(f"Querying patient with identifier: {identifier_type}")
        
        # If identifier_type is auto, try to determine the type
        if identifier_type == "auto":
            if patient_identifier.isdigit() and len(patient_identifier) >= 8:
                identifier_type = "cedula"
            elif len(patient_identifier) == 36 and '-' in patient_identifier:
                identifier_type = "id"
            else:
                identifier_type = "name"
        
        patient_data = None
        
        if identifier_type == "id":
            # Query by patient ID
            result = await api_client._make_request("GET", f"/patients/{patient_identifier}")
            if result.get("patient"):
                patient_data = result["patient"]
                
        elif identifier_type == "name":
            # Search by name
            params = {"limit": 10, "offset": 0}
            result = await api_client._make_request("GET", "/patients", params=params)
            
            if result.get("patients"):
                # Filter by name match
                for patient in result["patients"]:
                    if patient_identifier.lower() in patient.get("full_name", "").lower():
                        patient_data = patient
                        break
                        
        elif identifier_type == "cedula":
            # Search all patients and filter by cedula (if stored in a custom field)
            # Note: This assumes cedula might be stored in a custom field or we need to extend the API
            params = {"limit": 100, "offset": 0}
            result = await api_client._make_request("GET", "/patients", params=params)
            
            if result.get("patients"):
                # This would need to be enhanced based on actual cedula storage
                logger.warning("Cedula search not fully implemented - using name fallback")
                for patient in result["patients"]:
                    if patient_identifier in patient.get("full_name", ""):
                        patient_data = patient
                        break
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        if patient_data:
            return AgentToolResult(
                tool_name="query_patient_api",
                success=True,
                result=patient_data,
                execution_time_ms=execution_time
            )
        else:
            return AgentToolResult(
                tool_name="query_patient_api",
                success=False,
                error_message=f"Patient not found with {identifier_type}: {patient_identifier}",
                execution_time_ms=execution_time
            )
            
    except Exception as e:
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        logger.error(f"Error querying patient API: {str(e)}")
        
        return AgentToolResult(
            tool_name="query_patient_api",
            success=False,
            error_message=f"API error: {str(e)}",
            execution_time_ms=execution_time
        )


async def schedule_appointment(
    patient_id: str,
    medic_id: str,
    exam_id: str,
    appointment_date: str,
    notes: Optional[str] = None
) -> AgentToolResult:
    """
    Schedule a new appointment via Healthcare API.
    
    Args:
        patient_id: Patient identifier
        medic_id: Medic identifier
        exam_id: Exam identifier
        appointment_date: Appointment date/time (ISO format)
        notes: Optional appointment notes
        
    Returns:
        AgentToolResult: Created appointment or error
    """
    start_time = datetime.utcnow()
    
    try:
        logger.info("Creating new appointment reservation")
        
        appointment_data = {
            "patient_id": patient_id,
            "medic_id": medic_id,
            "exam_id": exam_id,
            "reservation_date": appointment_date
        }
        
        result = await api_client._make_request("POST", "/reservations", data=appointment_data)
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        if result.get("reservation"):
            return AgentToolResult(
                tool_name="schedule_appointment",
                success=True,
                result=result["reservation"],
                execution_time_ms=execution_time
            )
        else:
            return AgentToolResult(
                tool_name="schedule_appointment",
                success=False,
                error_message="Failed to create appointment",
                execution_time_ms=execution_time
            )
            
    except Exception as e:
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        logger.error(f"Error scheduling appointment: {str(e)}")
        
        return AgentToolResult(
            tool_name="schedule_appointment",
            success=False,
            error_message=f"Scheduling error: {str(e)}",
            execution_time_ms=execution_time
        )


async def check_availability(
    medic_id: str,
    date: str,
    duration_hours: int = 1
) -> AgentToolResult:
    """
    Check medic availability for a specific date.
    
    Args:
        medic_id: Medic identifier
        date: Date to check (YYYY-MM-DD format)
        duration_hours: Duration in hours
        
    Returns:
        AgentToolResult: Availability information
    """
    start_time = datetime.utcnow()
    
    try:
        logger.info(f"Checking availability for medic on date: {date}")
        
        availability_data = {
            "medic_id": medic_id,
            "date": date,
            "duration_hours": duration_hours
        }
        
        result = await api_client._make_request("POST", "/reservations/availability", data=availability_data)
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return AgentToolResult(
            tool_name="check_availability",
            success=True,
            result=result,
            execution_time_ms=execution_time
        )
        
    except Exception as e:
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        logger.error(f"Error checking availability: {str(e)}")
        
        return AgentToolResult(
            tool_name="check_availability",
            success=False,
            error_message=f"Availability check error: {str(e)}",
            execution_time_ms=execution_time
        )


async def get_appointments(
    patient_id: Optional[str] = None,
    medic_id: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 50
) -> AgentToolResult:
    """
    Retrieve appointments with optional filters.
    
    Args:
        patient_id: Filter by patient ID
        medic_id: Filter by medic ID
        status: Filter by status
        date_from: Filter from date (YYYY-MM-DD)
        date_to: Filter to date (YYYY-MM-DD)
        limit: Maximum number of results
        
    Returns:
        AgentToolResult: List of appointments
    """
    start_time = datetime.utcnow()
    
    try:
        logger.info("Retrieving appointments with filters")
        
        params = {"limit": limit, "offset": 0}
        
        if patient_id:
            params["patient_id"] = patient_id
        if medic_id:
            params["medic_id"] = medic_id
        if status:
            params["status"] = status
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        
        result = await api_client._make_request("GET", "/reservations", params=params)
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return AgentToolResult(
            tool_name="get_appointments",
            success=True,
            result=result,
            execution_time_ms=execution_time
        )
        
    except Exception as e:
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        logger.error(f"Error retrieving appointments: {str(e)}")
        
        return AgentToolResult(
            tool_name="get_appointments",
            success=False,
            error_message=f"Retrieval error: {str(e)}",
            execution_time_ms=execution_time
        )


async def cancel_appointment(reservation_id: str) -> AgentToolResult:
    """
    Cancel an existing appointment.
    
    Args:
        reservation_id: Reservation identifier
        
    Returns:
        AgentToolResult: Cancellation result
    """
    start_time = datetime.utcnow()
    
    try:
        logger.info(f"Cancelling appointment: {reservation_id}")
        
        result = await api_client._make_request("DELETE", f"/reservations/{reservation_id}")
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return AgentToolResult(
            tool_name="cancel_appointment",
            success=True,
            result=result,
            execution_time_ms=execution_time
        )
        
    except Exception as e:
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        logger.error(f"Error cancelling appointment: {str(e)}")
        
        return AgentToolResult(
            tool_name="cancel_appointment",
            success=False,
            error_message=f"Cancellation error: {str(e)}",
            execution_time_ms=execution_time
        )


async def get_medics(
    specialty: Optional[str] = None,
    limit: int = 50
) -> AgentToolResult:
    """
    Retrieve medics with optional specialty filter.
    
    Args:
        specialty: Filter by medical specialty
        limit: Maximum number of results
        
    Returns:
        AgentToolResult: List of medics
    """
    start_time = datetime.utcnow()
    
    try:
        logger.info("Retrieving medics list")
        
        params = {"limit": limit, "offset": 0}
        if specialty:
            params["specialty"] = specialty
        
        result = await api_client._make_request("GET", "/medics", params=params)
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return AgentToolResult(
            tool_name="get_medics",
            success=True,
            result=result,
            execution_time_ms=execution_time
        )
        
    except Exception as e:
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        logger.error(f"Error retrieving medics: {str(e)}")
        
        return AgentToolResult(
            tool_name="get_medics",
            success=False,
            error_message=f"Retrieval error: {str(e)}",
            execution_time_ms=execution_time
        )


async def get_exams(
    exam_type: Optional[str] = None,
    limit: int = 50
) -> AgentToolResult:
    """
    Retrieve exams with optional type filter.
    
    Args:
        exam_type: Filter by exam type
        limit: Maximum number of results
        
    Returns:
        AgentToolResult: List of exams
    """
    start_time = datetime.utcnow()
    
    try:
        logger.info("Retrieving exams list")
        
        params = {"limit": limit, "offset": 0}
        if exam_type:
            params["exam_type"] = exam_type
        
        result = await api_client._make_request("GET", "/exams", params=params)
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return AgentToolResult(
            tool_name="get_exams",
            success=True,
            result=result,
            execution_time_ms=execution_time
        )
        
    except Exception as e:
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        logger.error(f"Error retrieving exams: {str(e)}")
        
        return AgentToolResult(
            tool_name="get_exams",
            success=False,
            error_message=f"Retrieval error: {str(e)}",
            execution_time_ms=execution_time
        )
