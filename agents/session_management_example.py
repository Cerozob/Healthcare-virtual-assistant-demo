#!/usr/bin/env python3
"""
Example script demonstrating S3 session management for healthcare assistant.
This shows how medical notes are saved with patient context using Strands Agents.
"""

import os
import asyncio
from datetime import datetime
from strands import Agent
from strands.session.s3_session_manager import S3SessionManager
from shared.utils import get_logger, extract_patient_id_from_message, create_session_metadata

# Configure logging
logger = get_logger(__name__)

# Configuration
S3_BUCKET = os.getenv("SESSION_BUCKET", "ab2-cerozob-processeddata-us-east-1")
S3_PREFIX = os.getenv("SESSION_PREFIX", "medical-notes/")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

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


def create_session_manager_for_patient(session_id: str, patient_id: str = None) -> S3SessionManager:
    """
    Create S3SessionManager with patient-specific prefix consistent with document processing.
    
    Uses the same pattern as document extraction: processed/{patient_id}_{data_type}/
    
    Args:
        session_id: Session identifier
        patient_id: Patient identifier for organizing notes
        
    Returns:
        S3SessionManager: Configured session manager
    """
    # Create patient-specific prefix consistent with document processing structure
    if patient_id:
        # Use the same pattern as document extraction: processed/{patient_id}_{data_type}/
        prefix = f"processed/{patient_id}_medical_notes/"
        logger.info(f"Creating session manager for patient {patient_id} with consistent structure")
    else:
        # For sessions without patient context, use unknown patient pattern
        prefix = f"processed/unknown_medical_notes/"
        logger.info("Creating session manager for session without patient context")
    
    session_manager = S3SessionManager(
        session_id=session_id,
        bucket=S3_BUCKET,
        prefix=prefix,
        region_name=AWS_REGION
    )
    
    logger.debug(f"Session manager created with prefix: {prefix}")
    return session_manager


def create_healthcare_agent(session_id: str, patient_id: str = None) -> Agent:
    """
    Create healthcare agent with session management.
    
    Args:
        session_id: Session identifier
        patient_id: Patient identifier
        
    Returns:
        Agent: Configured agent with session management
    """
    session_manager = create_session_manager_for_patient(session_id, patient_id)
    
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
        agent.state["metadata"] = create_session_metadata(patient_id)
        logger.info(f"Agent initialized with patient context: {patient_id}")
    else:
        agent.state["session_context"] = "no_patient"
        agent.state["metadata"] = create_session_metadata()
        logger.info("Agent initialized without patient context")
    
    return agent


async def example_patient_session():
    """
    Example of a patient session with medical notes.
    """
    print("\n=== Example: Patient Session with Medical Notes ===")
    
    # Example messages with patient context
    messages = [
        "Esta sesión es del paciente Juan_Perez_123. Hola doctor, tengo dolor de cabeza desde ayer.",
        "El dolor es constante y se intensifica con la luz.",
        "También tengo un poco de náuseas.",
        "¿Qué medicamento me recomienda?"
    ]
    
    session_id = f"patient_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Process first message to extract patient ID
    first_message = messages[0]
    patient_id = extract_patient_id_from_message(first_message)
    
    print(f"Session ID: {session_id}")
    print(f"Patient ID extracted: {patient_id}")
    print(f"S3 Storage path: s3://{S3_BUCKET}/processed/{patient_id}_medical_notes/")
    
    # Create agent with patient context
    agent = create_healthcare_agent(session_id, patient_id)
    
    # Process each message
    for i, message in enumerate(messages, 1):
        print(f"\n--- Message {i} ---")
        print(f"User: {message}")
        
        # Process message with agent (this automatically saves to S3)
        result = agent(message)
        
        print(f"Assistant: {result.message[:200]}...")
        print(f"Notes saved to: s3://{S3_BUCKET}/processed/{patient_id}_medical_notes/session_{session_id}/")
    
    print(f"\n✅ Session completed. All conversation history saved to S3 with patient context.")
    return session_id, patient_id


async def example_no_patient_session():
    """
    Example of a session without patient context.
    """
    print("\n=== Example: General Session (No Patient Context) ===")
    
    # Example messages without patient context
    messages = [
        "Hola, ¿puedes explicarme qué es la hipertensión?",
        "¿Cuáles son los síntomas más comunes?",
        "¿Qué medidas preventivas recomiendas?"
    ]
    
    session_id = f"general_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print(f"Session ID: {session_id}")
    print(f"Patient ID: no_patient")
    print(f"S3 Storage path: s3://{S3_BUCKET}/processed/unknown_medical_notes/")
    
    # Create agent without patient context
    agent = create_healthcare_agent(session_id, None)
    
    # Process each message
    for i, message in enumerate(messages, 1):
        print(f"\n--- Message {i} ---")
        print(f"User: {message}")
        
        # Process message with agent (this automatically saves to S3)
        result = agent(message)
        
        print(f"Assistant: {result.message[:200]}...")
        print(f"Notes saved to: s3://{S3_BUCKET}/processed/unknown_medical_notes/session_{session_id}/")
    
    print(f"\n✅ Session completed. All conversation history saved to S3 without patient context.")
    return session_id


async def demonstrate_session_retrieval(session_id: str, patient_id: str = None):
    """
    Demonstrate how to retrieve and continue a previous session.
    """
    print(f"\n=== Example: Retrieving Previous Session ===")
    
    # Create new agent instance with same session ID
    # This will automatically restore the previous conversation
    agent = create_healthcare_agent(session_id, patient_id)
    
    print(f"Restored session: {session_id}")
    print(f"Previous messages count: {len(agent.messages)}")
    
    # Continue the conversation
    follow_up_message = "¿Puedes hacer un resumen de nuestra conversación anterior?"
    print(f"\nUser: {follow_up_message}")
    
    result = agent(follow_up_message)
    print(f"Assistant: {result.message[:300]}...")
    
    print(f"\n✅ Session continued successfully with full conversation history.")


async def main():
    """
    Main example function demonstrating session management.
    """
    print("Healthcare Assistant - S3 Session Management Examples")
    print("=" * 60)
    
    try:
        # Example 1: Patient session
        session_id, patient_id = await example_patient_session()
        
        # Example 2: General session
        general_session_id = await example_no_patient_session()
        
        # Example 3: Session retrieval
        await demonstrate_session_retrieval(session_id, patient_id)
        
        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print(f"Patient session stored at: s3://{S3_BUCKET}/processed/{patient_id}_medical_notes/")
        print(f"General session stored at: s3://{S3_BUCKET}/processed/unknown_medical_notes/")
        
    except Exception as e:
        logger.error(f"Example failed: {str(e)}", exc_info=True)
        print(f"❌ Example failed: {str(e)}")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
