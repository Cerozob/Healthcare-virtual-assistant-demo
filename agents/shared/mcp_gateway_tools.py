"""
MCP Gateway Tools for Strands Agents.
Provides tools for interacting with AWS Lambda functions through AgentCore Gateway.
Replaces direct database access with gateway-mediated lambda calls.
"""

import json
import httpx
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from .config import get_agent_config
from .models import ErrorType, AgentToolResult
from .utils import get_logger, create_error_response, sanitize_for_logging

logger = get_logger(__name__)


class MCPGatewayClient:
    """
    Client for interacting with AgentCore Gateway MCP endpoints.
    Handles authentication, request formatting, and error handling.
    """
    
    def __init__(self):
        """Initialize the MCP Gateway client."""
        self.config = get_agent_config()
        self.gateway_url = self.config.gateway_url
        self.gateway_id = self.config.gateway_id
        self.timeout = 30.0
        self.max_retries = 3
        
    async def _make_gateway_request(
        self, 
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make a request to the AgentCore Gateway MCP endpoint.
        
        Args:
            tool_name: Name of the tool/lambda to invoke
            parameters: Parameters to pass to the lambda function
            
        Returns:
            Dict[str, Any]: Gateway response
            
        Raises:
            Exception: If request fails after retries
        """
        if not self.gateway_url:
            raise Exception("Gateway URL not configured")
            
        # Format the MCP request according to AgentCore Gateway specification
        mcp_request = {
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": parameters
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._get_auth_token()}"  # IAM-based auth
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    # Sanitize request for logging
                    sanitized_request = sanitize_for_logging(mcp_request)
                    logger.info(f"Making MCP gateway request to {tool_name} (attempt {attempt + 1})")
                    logger.debug(f"Request: {sanitized_request}")
                    
                    response = await client.post(
                        f"{self.gateway_url}/mcp",
                        json=mcp_request,
                        headers=headers
                    )
                    
                    response.raise_for_status()
                    result = response.json()
                    
                    logger.info(f"Gateway request successful: {response.status_code}")
                    return result
                    
                except httpx.HTTPStatusError as e:
                    logger.error(f"HTTP error on attempt {attempt + 1}: {e.response.status_code} - {e.response.text}")
                    if e.response.status_code in [400, 401, 403, 404]:
                        # Don't retry client errors
                        raise Exception(f"Gateway error: {e.response.status_code} - {e.response.text}")
                    
                    if attempt == self.max_retries - 1:
                        raise Exception(f"Gateway request failed after {self.max_retries} attempts: {str(e)}")
                        
                except Exception as e:
                    logger.error(f"Request error on attempt {attempt + 1}: {str(e)}")
                    if attempt == self.max_retries - 1:
                        raise Exception(f"Gateway request failed after {self.max_retries} attempts: {str(e)}")
                
                # Wait before retry
                await asyncio.sleep(2 ** attempt)
    
    def _get_auth_token(self) -> str:
        """
        Get authentication token for gateway requests.
        In production, this would use AWS IAM credentials.
        """
        # For AgentCore Gateway with IAM authentication,
        # this would typically use AWS SigV4 signing
        # For now, return a placeholder
        return "iam-token-placeholder"


# Initialize gateway client
gateway_client = MCPGatewayClient()


async def query_patients_mcp(
    action: str,
    patient_id: Optional[str] = None,
    patient_data: Optional[Dict[str, Any]] = None,
    pagination: Optional[Dict[str, Any]] = None
) -> AgentToolResult:
    """
    Query patient information through MCP Gateway.
    
    Args:
        action: Action to perform (list, get, create, update, delete)
        patient_id: Patient ID for specific operations
        patient_data: Patient data for create/update operations
        pagination: Pagination parameters for list operations
        
    Returns:
        AgentToolResult: Patient information or error
    """
    start_time = datetime.utcnow()
    
    try:
        logger.info(f"Querying patients via MCP Gateway: action={action}")
        
        # Prepare parameters for the lambda function
        parameters = {"action": action}
        
        if patient_id:
            parameters["patient_id"] = patient_id
        if patient_data:
            parameters["patient_data"] = patient_data
        if pagination:
            parameters["pagination"] = pagination
        
        # Make gateway request
        result = await gateway_client._make_gateway_request("patients_api", parameters)
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Check if the MCP call was successful
        if result.get("result"):
            return AgentToolResult(
                tool_name="query_patients_mcp",
                success=True,
                result=result["result"],
                execution_time_ms=execution_time
            )
        else:
            error_message = result.get("error", {}).get("message", "Unknown error")
            return AgentToolResult(
                tool_name="query_patients_mcp",
                success=False,
                error_message=f"MCP Gateway error: {error_message}",
                execution_time_ms=execution_time
            )
            
    except Exception as e:
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        logger.error(f"Error in MCP patients query: {str(e)}")
        
        return AgentToolResult(
            tool_name="query_patients_mcp",
            success=False,
            error_message=f"Gateway error: {str(e)}",
            execution_time_ms=execution_time
        )


async def query_medics_mcp(
    action: str,
    medic_id: Optional[str] = None,
    specialty: Optional[str] = None,
    medic_data: Optional[Dict[str, Any]] = None,
    pagination: Optional[Dict[str, Any]] = None
) -> AgentToolResult:
    """
    Query medic information through MCP Gateway.
    
    Args:
        action: Action to perform (list, get, create, update, delete)
        medic_id: Medic ID for specific operations
        specialty: Specialty filter for list operations
        medic_data: Medic data for create/update operations
        pagination: Pagination parameters for list operations
        
    Returns:
        AgentToolResult: Medic information or error
    """
    start_time = datetime.utcnow()
    
    try:
        logger.info(f"Querying medics via MCP Gateway: action={action}")
        
        parameters = {"action": action}
        
        if medic_id:
            parameters["medic_id"] = medic_id
        if specialty:
            parameters["specialty"] = specialty
        if medic_data:
            parameters["medic_data"] = medic_data
        if pagination:
            parameters["pagination"] = pagination
        
        result = await gateway_client._make_gateway_request("medics_api", parameters)
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        if result.get("result"):
            return AgentToolResult(
                tool_name="query_medics_mcp",
                success=True,
                result=result["result"],
                execution_time_ms=execution_time
            )
        else:
            error_message = result.get("error", {}).get("message", "Unknown error")
            return AgentToolResult(
                tool_name="query_medics_mcp",
                success=False,
                error_message=f"MCP Gateway error: {error_message}",
                execution_time_ms=execution_time
            )
            
    except Exception as e:
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        logger.error(f"Error in MCP medics query: {str(e)}")
        
        return AgentToolResult(
            tool_name="query_medics_mcp",
            success=False,
            error_message=f"Gateway error: {str(e)}",
            execution_time_ms=execution_time
        )


async def query_exams_mcp(
    action: str,
    exam_id: Optional[str] = None,
    exam_type: Optional[str] = None,
    exam_data: Optional[Dict[str, Any]] = None,
    pagination: Optional[Dict[str, Any]] = None
) -> AgentToolResult:
    """
    Query exam information through MCP Gateway.
    
    Args:
        action: Action to perform (list, get, create, update, delete)
        exam_id: Exam ID for specific operations
        exam_type: Exam type filter for list operations
        exam_data: Exam data for create/update operations
        pagination: Pagination parameters for list operations
        
    Returns:
        AgentToolResult: Exam information or error
    """
    start_time = datetime.utcnow()
    
    try:
        logger.info(f"Querying exams via MCP Gateway: action={action}")
        
        parameters = {"action": action}
        
        if exam_id:
            parameters["exam_id"] = exam_id
        if exam_type:
            parameters["exam_type"] = exam_type
        if exam_data:
            parameters["exam_data"] = exam_data
        if pagination:
            parameters["pagination"] = pagination
        
        result = await gateway_client._make_gateway_request("exams_api", parameters)
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        if result.get("result"):
            return AgentToolResult(
                tool_name="query_exams_mcp",
                success=True,
                result=result["result"],
                execution_time_ms=execution_time
            )
        else:
            error_message = result.get("error", {}).get("message", "Unknown error")
            return AgentToolResult(
                tool_name="query_exams_mcp",
                success=False,
                error_message=f"MCP Gateway error: {error_message}",
                execution_time_ms=execution_time
            )
            
    except Exception as e:
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        logger.error(f"Error in MCP exams query: {str(e)}")
        
        return AgentToolResult(
            tool_name="query_exams_mcp",
            success=False,
            error_message=f"Gateway error: {str(e)}",
            execution_time_ms=execution_time
        )


async def query_reservations_mcp(
    action: str,
    reservation_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    medic_id: Optional[str] = None,
    exam_id: Optional[str] = None,
    reservation_date: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    status: Optional[str] = None,
    pagination: Optional[Dict[str, Any]] = None
) -> AgentToolResult:
    """
    Query reservation information through MCP Gateway.
    
    Args:
        action: Action to perform (list, get, create, update, delete, check_availability)
        reservation_id: Reservation ID for specific operations
        patient_id: Patient ID filter
        medic_id: Medic ID filter
        exam_id: Exam ID for create operations
        reservation_date: Reservation date for create operations
        date_from: Start date filter
        date_to: End date filter
        status: Status filter
        pagination: Pagination parameters for list operations
        
    Returns:
        AgentToolResult: Reservation information or error
    """
    start_time = datetime.utcnow()
    
    try:
        logger.info(f"Querying reservations via MCP Gateway: action={action}")
        
        parameters = {"action": action}
        
        if reservation_id:
            parameters["reservation_id"] = reservation_id
        if patient_id:
            parameters["patient_id"] = patient_id
        if medic_id:
            parameters["medic_id"] = medic_id
        if exam_id:
            parameters["exam_id"] = exam_id
        if reservation_date:
            parameters["reservation_date"] = reservation_date
        if date_from:
            parameters["date_from"] = date_from
        if date_to:
            parameters["date_to"] = date_to
        if status:
            parameters["status"] = status
        if pagination:
            parameters["pagination"] = pagination
        
        result = await gateway_client._make_gateway_request("reservations_api", parameters)
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        if result.get("result"):
            return AgentToolResult(
                tool_name="query_reservations_mcp",
                success=True,
                result=result["result"],
                execution_time_ms=execution_time
            )
        else:
            error_message = result.get("error", {}).get("message", "Unknown error")
            return AgentToolResult(
                tool_name="query_reservations_mcp",
                success=False,
                error_message=f"MCP Gateway error: {error_message}",
                execution_time_ms=execution_time
            )
            
    except Exception as e:
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        logger.error(f"Error in MCP reservations query: {str(e)}")
        
        return AgentToolResult(
            tool_name="query_reservations_mcp",
            success=False,
            error_message=f"Gateway error: {str(e)}",
            execution_time_ms=execution_time
        )


async def query_files_mcp(
    action: str,
    file_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    file_type: Optional[str] = None,
    search_query: Optional[str] = None,
    file_data: Optional[Dict[str, Any]] = None,
    pagination: Optional[Dict[str, Any]] = None
) -> AgentToolResult:
    """
    Query file information through MCP Gateway.
    
    Args:
        action: Action to perform (list, get, upload, delete, classify, search)
        file_id: File ID for specific operations
        patient_id: Patient ID filter
        file_type: File type filter
        search_query: Search query for knowledge base operations
        file_data: File data for upload operations
        pagination: Pagination parameters for list operations
        
    Returns:
        AgentToolResult: File information or error
    """
    start_time = datetime.utcnow()
    
    try:
        logger.info(f"Querying files via MCP Gateway: action={action}")
        
        parameters = {"action": action}
        
        if file_id:
            parameters["file_id"] = file_id
        if patient_id:
            parameters["patient_id"] = patient_id
        if file_type:
            parameters["file_type"] = file_type
        if search_query:
            parameters["search_query"] = search_query
        if file_data:
            parameters["file_data"] = file_data
        if pagination:
            parameters["pagination"] = pagination
        
        result = await gateway_client._make_gateway_request("files_api", parameters)
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        if result.get("result"):
            return AgentToolResult(
                tool_name="query_files_mcp",
                success=True,
                result=result["result"],
                execution_time_ms=execution_time
            )
        else:
            error_message = result.get("error", {}).get("message", "Unknown error")
            return AgentToolResult(
                tool_name="query_files_mcp",
                success=False,
                error_message=f"MCP Gateway error: {error_message}",
                execution_time_ms=execution_time
            )
            
    except Exception as e:
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        logger.error(f"Error in MCP files query: {str(e)}")
        
        return AgentToolResult(
            tool_name="query_files_mcp",
            success=False,
            error_message=f"Gateway error: {str(e)}",
            execution_time_ms=execution_time
        )


# Convenience functions for common operations
async def get_patient_by_id_mcp(patient_id: str) -> AgentToolResult:
    """Get a patient by ID through MCP Gateway."""
    return await query_patients_mcp(action="get", patient_id=patient_id)


async def list_patients_mcp(limit: int = 50, offset: int = 0) -> AgentToolResult:
    """List patients with pagination through MCP Gateway."""
    return await query_patients_mcp(
        action="list", 
        pagination={"limit": limit, "offset": offset}
    )


async def create_patient_mcp(patient_data: Dict[str, Any]) -> AgentToolResult:
    """Create a new patient through MCP Gateway."""
    return await query_patients_mcp(action="create", patient_data=patient_data)


async def get_medics_by_specialty_mcp(specialty: str, limit: int = 50) -> AgentToolResult:
    """Get medics by specialty through MCP Gateway."""
    return await query_medics_mcp(
        action="list", 
        specialty=specialty,
        pagination={"limit": limit, "offset": 0}
    )


async def schedule_appointment_mcp(
    patient_id: str,
    medic_id: str,
    exam_id: str,
    reservation_date: str
) -> AgentToolResult:
    """Schedule an appointment through MCP Gateway."""
    return await query_reservations_mcp(
        action="create",
        patient_id=patient_id,
        medic_id=medic_id,
        exam_id=exam_id,
        reservation_date=reservation_date
    )


async def check_availability_mcp(medic_id: str, date: str) -> AgentToolResult:
    """Check medic availability through MCP Gateway."""
    return await query_reservations_mcp(
        action="check_availability",
        medic_id=medic_id,
        reservation_date=date
    )
