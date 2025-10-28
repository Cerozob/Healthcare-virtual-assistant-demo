"""
Healthcare Assistant Agent using Strands Agents framework.
FastAPI implementation for AgentCore Runtime deployment with S3 session management.
"""

import logging
import os
import boto3
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from strands import Agent
from strands.session.s3_session_manager import S3SessionManager
from shared.utils import get_logger, extract_patient_context

# Configure Strands Agents logging
def configure_logging():
    """Configure logging for Strands Agents SDK following best practices."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Configure the root strands logger following Strands best practices
    strands_logger = logging.getLogger("strands")
    strands_logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Configure basic logging format as recommended by Strands documentation
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler()]
    )
    
    # Log configuration
    strands_logger.info(f"Strands Agents logging configured at {log_level} level")
    strands_logger.debug("Logging configuration complete - ready for AgentCore deployment")

# Initialize logging
configure_logging()

# Get logger for this module
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Healthcare Assistant Agent", version="1.0.0")

# Healthcare assistant system prompt
HEALTHCARE_SYSTEM_PROMPT = """
You are a healthcare assistant designed to help medical professionals with:
- Patient information management
- Appointment scheduling
- Medical knowledge base queries
- Document processing and analysis

Always respond in Spanish (LATAM) unless specifically requested otherwise.
Maintain professional medical standards and patient confidentiality.
Be helpful, accurate, and professional in all interactions.

When saving notes or information about patients, always include the patient context in your responses.
"""

# S3 Configuration for session management
# Uses consistent structure with document processing: processed/{patient_id}_{data_type}/
S3_BUCKET = os.getenv("SESSION_BUCKET", "ab2-cerozob-processeddata-us-east-1")
S3_PREFIX = os.getenv("SESSION_PREFIX", "processed/")  # Base prefix only
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

def extract_patient_id_from_message(message: str) -> Optional[str]:
    """
    Extract patient ID from user message using various patterns.
    
    Args:
        message: User message
        
    Returns:
        Optional[str]: Extracted patient ID or None
    """
    # Pattern for explicit patient ID
    patient_id_patterns = [
        r"paciente\s+id[:\s]+([a-zA-Z0-9\-_]+)",
        r"patient\s+id[:\s]+([a-zA-Z0-9\-_]+)",
        r"cedula[:\s]+(\d+)",
        r"cédula[:\s]+(\d+)",
        r"id\s+paciente[:\s]+([a-zA-Z0-9\-_]+)",
        r"esta sesión es del paciente\s+([a-zA-Z0-9\-_\s]+)",
    ]
    
    message_lower = message.lower()
    
    for pattern in patient_id_patterns:
        match = re.search(pattern, message_lower)
        if match:
            patient_id = match.group(1).strip()
            # Clean up patient ID (remove spaces, normalize)
            patient_id = re.sub(r'\s+', '_', patient_id)
            return patient_id
    
    return None

def create_session_manager(session_id: str, patient_id: Optional[str] = None) -> S3SessionManager:
    """
    Create S3SessionManager with patient-specific prefix consistent with document processing structure.
    
    Uses the same pattern as document extraction: processed/{patient_id}_{session_type}/
    
    Args:
        session_id: Session identifier
        patient_id: Patient identifier for organizing notes
        
    Returns:
        S3SessionManager: Configured session manager
    """
    # Create patient-specific prefix consistent with document processing structure
    if patient_id:
        # Use the same pattern as document extraction: processed/{patient_id}_{session_type}/
        clean_patient_id = patient_id
        prefix = f"processed/{clean_patient_id}_medical_notes/"
        logger.info(f"Creating session manager for patient {patient_id} with consistent structure")
    else:
        # For sessions without patient context, use unknown patient pattern
        prefix = f"processed/unknown_medical_notes/"
        logger.info("Creating session manager for session without patient context")
    
    try:
        session_manager = S3SessionManager(
            session_id=session_id,
            bucket=S3_BUCKET,
            prefix=prefix,
            region_name=AWS_REGION
        )
        logger.debug(f"Session manager created with prefix: {prefix}")
        return session_manager
    except Exception as e:
        logger.error(f"Failed to create session manager: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize session management: {str(e)}"
        )

def get_or_create_agent(session_id: str, patient_id: Optional[str] = None) -> Agent:
    """
    Get or create agent with session management.
    
    Args:
        session_id: Session identifier
        patient_id: Patient identifier
        
    Returns:
        Agent: Configured agent with session management
    """
    try:
        session_manager = create_session_manager(session_id, patient_id)
        
        # Create agent with session management
        agent = Agent(
            system_prompt=HEALTHCARE_SYSTEM_PROMPT,
            session_manager=session_manager,
            callback_handler=None  # Prevent streaming output pollution
        )
        
        # Add patient context to agent state if available
        if patient_id:
            agent.state["patient_id"] = patient_id
            agent.state["session_context"] = "patient_session"
            logger.info(f"Agent initialized with patient context: {patient_id}")
        else:
            agent.state["session_context"] = "no_patient"
            logger.info("Agent initialized without patient context")
        
        return agent
        
    except Exception as e:
        logger.error(f"Failed to create agent with session management: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize agent: {str(e)}"
        )


class InvocationRequest(BaseModel):
    input: Dict[str, Any]


class InvocationResponse(BaseModel):
    output: Dict[str, Any]


@app.post("/invocations", response_model=InvocationResponse)
async def invoke_agent(request: InvocationRequest):
    """
    Main AgentCore invocation endpoint for healthcare assistant with session management.
    """
    try:
        user_message = request.input.get("prompt", "")
        if not user_message:
            logger.warning("Received request without prompt")
            raise HTTPException(
                status_code=400,
                detail="No prompt found in input. Please provide a 'prompt' key in the input."
            )

        # Extract session ID from request (use a default if not provided)
        session_id = request.input.get("sessionId", f"healthcare_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # Extract patient ID from message
        patient_id = extract_patient_id_from_message(user_message)
        
        logger.debug(f"Processing message for session: {session_id}")
        if patient_id:
            logger.info(f"Patient context detected: {patient_id}")
        else:
            logger.info("No patient context detected in message")
        
        # Get or create agent with session management
        agent = get_or_create_agent(session_id, patient_id)
        
        logger.debug(f"Processing user message: {user_message[:100]}...")
        logger.info("Healthcare assistant processing user request with session management")
        
        # Process the message with the agent
        result = agent(user_message)
        
        # Prepare response with session and patient context using consistent structure
        if patient_id:
            session_prefix = f"processed/{patient_id}_medical_notes/"
        else:
            session_prefix = f"processed/unknown_medical_notes/"
        
        response = {
            "message": result.message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": "healthcare-assistant",
            "capabilities": ["patient_info", "appointments", "knowledge_base", "documents", "session_management"],
            "session_id": session_id,
            "patient_context": {
                "patient_id": patient_id if patient_id else "unknown",
                "has_patient_context": patient_id is not None,
                "session_prefix": session_prefix,
                "consistent_with_documents": True  # Indicates this follows the same structure as document processing
            },
            "session_info": {
                "bucket": S3_BUCKET,
                "region": AWS_REGION,
                "notes_saved": True,
                "conversation_persisted": True,
                "structure_pattern": "processed/{patient_id}_{data_type}/"
            }
        }

        logger.info("Healthcare assistant request processed successfully with session management")
        logger.debug(f"Response generated: {len(response.get('message', ''))} characters")
        logger.debug(f"Session data saved to S3 with prefix: {response['patient_context']['session_prefix']}")
        
        return InvocationResponse(output=response)

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Agent processing failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")


@app.get("/ping")
async def ping():
    """Health check endpoint required by AgentCore Runtime."""
    return {"status": "healthy"}


@app.get("/sessions/{session_id}/info")
async def get_session_info(session_id: str):
    """
    Get information about a specific session.
    """
    try:
        # Try to determine if this is a patient session by checking S3 structure
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        
        # Check for patient sessions
        patient_prefix = f"{S3_PREFIX}patients/"
        no_patient_prefix = f"{S3_PREFIX}no-patient/"
        
        session_info = {
            "session_id": session_id,
            "bucket": S3_BUCKET,
            "region": AWS_REGION,
            "found": False,
            "patient_context": None,
            "message_count": 0
        }
        
        # Check both patient and unknown prefixes using consistent structure
        prefixes_to_check = [
            ("patient", f"processed/"),  # We'll search for patterns like processed/{patient_id}_medical_notes/
            ("unknown", f"processed/unknown_medical_notes/")
        ]
        
        for prefix_type, base_prefix in prefixes_to_check:
            try:
                if prefix_type == "patient":
                    # For patient sessions, we need to search for any patient ID pattern
                    # List all objects that match the pattern processed/*_medical_notes/session_{session_id}/
                    response = s3_client.list_objects_v2(
                        Bucket=S3_BUCKET,
                        Prefix=base_prefix,
                        MaxKeys=1000  # Increase to find patient sessions
                    )
                    
                    # Look for session in any patient's medical notes
                    for obj in response.get('Contents', []):
                        key = obj['Key']
                        if f"_medical_notes/session_{session_id}/" in key:
                            session_info["found"] = True
                            session_info["patient_context"] = "patient"
                            
                            # Extract patient ID from the key
                            parts = key.split('/')
                            if len(parts) > 0:
                                patient_folder = parts[0].replace('processed/', '')
                                if '_medical_notes' in patient_folder:
                                    extracted_patient_id = patient_folder.replace('_medical_notes', '')
                                    session_info["extracted_patient_id"] = extracted_patient_id
                            
                            # Count messages
                            messages_response = s3_client.list_objects_v2(
                                Bucket=S3_BUCKET,
                                Prefix=key.split('/session_')[0] + f"/session_{session_id}/agents/",
                            )
                            
                            message_count = 0
                            for msg_obj in messages_response.get('Contents', []):
                                if 'messages/message_' in msg_obj['Key']:
                                    message_count += 1
                            
                            session_info["message_count"] = message_count
                            break
                else:
                    # For unknown patient sessions
                    response = s3_client.list_objects_v2(
                        Bucket=S3_BUCKET,
                        Prefix=f"{base_prefix}session_{session_id}/",
                        MaxKeys=1
                    )
                    
                    if response.get('Contents'):
                        session_info["found"] = True
                        session_info["patient_context"] = "unknown"
                        
                        # Count messages
                        messages_response = s3_client.list_objects_v2(
                            Bucket=S3_BUCKET,
                            Prefix=f"{base_prefix}session_{session_id}/agents/",
                        )
                        
                        message_count = 0
                        for obj in messages_response.get('Contents', []):
                            if 'messages/message_' in obj['Key']:
                                message_count += 1
                        
                        session_info["message_count"] = message_count
                        break
                
                if session_info["found"]:
                    break
                    
            except Exception as e:
                logger.debug(f"Error checking prefix {base_prefix}: {str(e)}")
                continue
        
        return session_info
        
    except Exception as e:
        logger.error(f"Failed to get session info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get session info: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
