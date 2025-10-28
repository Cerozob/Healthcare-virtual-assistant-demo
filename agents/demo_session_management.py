#!/usr/bin/env python3
"""
Demo script for healthcare assistant session management.
Interactive command-line interface to test the session management functionality.
"""

import os
import asyncio
from datetime import datetime
from main import get_or_create_agent, extract_patient_id_from_message
from shared.utils import get_logger

# Configure logging
logger = get_logger(__name__)

# Configuration
S3_BUCKET = os.getenv("SESSION_BUCKET", "ab2-cerozob-processeddata-us-east-1")
S3_PREFIX = os.getenv("SESSION_PREFIX", "medical-notes/")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")


def print_banner():
    """Print the demo banner."""
    print("=" * 70)
    print("🏥 Healthcare Assistant - Session Management Demo")
    print("=" * 70)
    print(f"S3 Bucket: {S3_BUCKET}")
    print(f"S3 Prefix: {S3_PREFIX}")
    print(f"AWS Region: {AWS_REGION}")
    print()
    print("This demo shows how medical conversations are saved as notes")
    print("with patient context using Strands Agents and S3 storage.")
    print()
    print("Commands:")
    print("  - Type your message to chat with the assistant")
    print("  - Use 'patient: <name>' to set patient context")
    print("  - Use 'session: <id>' to switch sessions")
    print("  - Use 'info' to see current session information")
    print("  - Use 'quit' to exit")
    print("=" * 70)


async def interactive_demo():
    """
    Run an interactive demo of the session management.
    """
    print_banner()
    
    # Initialize session
    current_session_id = f"demo_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    current_patient_id = None
    current_agent = None
    
    print(f"🆔 Session ID: {current_session_id}")
    print("👤 Patient: Not set (use 'patient: <name>' to set)")
    print()
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() == 'quit':
                print("👋 Goodbye! Your conversation has been saved to S3.")
                break
            
            elif user_input.lower() == 'info':
                print(f"\n📊 Current Session Information:")
                print(f"   Session ID: {current_session_id}")
                print(f"   Patient ID: {current_patient_id or 'Not set'}")
                if current_patient_id:
                    print(f"   S3 Path: s3://{S3_BUCKET}/processed/{current_patient_id}_medical_notes/")
                else:
                    print(f"   S3 Path: s3://{S3_BUCKET}/processed/unknown_medical_notes/")
                if current_agent:
                    print(f"   Messages: {len(current_agent.messages)}")
                print()
                continue
            
            elif user_input.lower().startswith('patient:'):
                # Set patient context
                patient_name = user_input[8:].strip()
                if patient_name:
                    current_patient_id = patient_name.replace(' ', '_')
                    current_agent = None  # Reset agent to pick up new patient context
                    print(f"👤 Patient set to: {current_patient_id}")
                    print(f"📁 Notes will be saved to: s3://{S3_BUCKET}/processed/{current_patient_id}_medical_notes/")
                else:
                    print("❌ Please provide a patient name: patient: <name>")
                print()
                continue
            
            elif user_input.lower().startswith('session:'):
                # Switch session
                session_name = user_input[8:].strip()
                if session_name:
                    current_session_id = session_name
                    current_agent = None  # Reset agent for new session
                    print(f"🆔 Session switched to: {current_session_id}")
                else:
                    print("❌ Please provide a session ID: session: <id>")
                print()
                continue
            
            # Check if message contains patient context
            detected_patient_id = extract_patient_id_from_message(user_input)
            if detected_patient_id and detected_patient_id != current_patient_id:
                current_patient_id = detected_patient_id
                current_agent = None  # Reset agent for new patient context
                print(f"👤 Patient context detected: {current_patient_id}")
            
            # Get or create agent
            if current_agent is None:
                print("🤖 Initializing agent with session management...")
                current_agent = get_or_create_agent(current_session_id, current_patient_id)
                
                if current_patient_id:
                    print(f"📝 Notes will be saved for patient: {current_patient_id}")
                else:
                    print("📝 Notes will be saved without patient context")
            
            # Process the message
            print("🤔 Processing...")
            result = current_agent(user_input)
            
            # Display response
            print(f"Assistant: {result.message}")
            
            # Show storage information
            if current_patient_id:
                storage_path = f"s3://{S3_BUCKET}/processed/{current_patient_id}_medical_notes/session_{current_session_id}/"
            else:
                storage_path = f"s3://{S3_BUCKET}/processed/unknown_medical_notes/session_{current_session_id}/"
            
            print(f"💾 Conversation saved to: {storage_path}")
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Demo interrupted. Your conversation has been saved to S3.")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            logger.error(f"Demo error: {str(e)}", exc_info=True)
            print()


def run_example_scenarios():
    """
    Run predefined example scenarios.
    """
    print("\n🎬 Running Example Scenarios")
    print("-" * 40)
    
    scenarios = [
        {
            "name": "Patient Consultation",
            "messages": [
                "Esta sesión es del paciente Maria_Garcia_789. Hola doctor, tengo dolor de garganta.",
                "El dolor empezó hace dos días y empeora al tragar.",
                "¿Qué medicamento me recomienda?"
            ]
        },
        {
            "name": "General Medical Query",
            "messages": [
                "¿Qué es la diabetes tipo 2?",
                "¿Cuáles son los síntomas principales?",
                "¿Cómo se puede prevenir?"
            ]
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 Scenario: {scenario['name']}")
        session_id = f"example_{scenario['name'].lower().replace(' ', '_')}_{datetime.now().strftime('%H%M%S')}"
        
        agent = None
        patient_id = None
        
        for i, message in enumerate(scenario['messages'], 1):
            print(f"\n  Message {i}: {message}")
            
            # Extract patient ID if present
            if agent is None:
                patient_id = extract_patient_id_from_message(message)
                agent = get_or_create_agent(session_id, patient_id)
            
            # Process message
            try:
                result = agent(message)
                print(f"  Response: {result.message[:100]}...")
                
                # Show where it's stored
                if patient_id:
                    storage_path = f"s3://{S3_BUCKET}/processed/{patient_id}_medical_notes/"
                else:
                    storage_path = f"s3://{S3_BUCKET}/processed/unknown_medical_notes/"
                
                print(f"  💾 Saved to: {storage_path}")
                
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
        
        print(f"  ✅ Scenario '{scenario['name']}' completed")


async def main():
    """
    Main demo function.
    """
    print("Welcome to the Healthcare Assistant Session Management Demo!")
    print()
    
    while True:
        print("Choose an option:")
        print("1. Interactive Demo")
        print("2. Run Example Scenarios")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            await interactive_demo()
        elif choice == '2':
            run_example_scenarios()
        elif choice == '3':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")
        
        print()


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())
