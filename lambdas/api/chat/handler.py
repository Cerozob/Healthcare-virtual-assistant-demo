"""
Chat API Lambda Function.
Handles chat interactions with the orchestrator agent.
No database storage - agents handle conversation state.

Endpoints:
- POST /chat/message - Send message to orchestrator agent
- GET /chat/sessions - Return empty list (no storage)
- POST /chat/sessions - Create session ID (no storage)
- GET /chat/sessions/{id}/messages - Return empty list (no storage)
"""

import logging
import boto3
from typing import Dict, Any
from shared.database import DatabaseManager, DatabaseError
from shared.utils import (
    create_response, create_error_response, parse_event_body,
    extract_path_parameters, extract_query_parameters, validate_required_fields,
    handle_exceptions, generate_uuid, get_current_timestamp
)
from shared.ssm_config import SSMConfig

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients and managers
ssm_config = SSMConfig()
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')


@handle_exceptions
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for chat requests.
    Routes to appropriate handler based on HTTP method and path.
    """
    # Handle both API Gateway v1 and v2 event formats
    http_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method', '')
    path = event.get('path') or event.get('requestContext', {}).get('http', {}).get('path', '')
    path_params = event.get('pathParameters') or {}
    
    # Log the event for debugging
    logger.info(f"Received request: method={http_method}, path={path}")
    
    # Normalize path by removing stage prefix if present
    normalized_path = path
    if path.startswith('/v1/'):
        normalized_path = path[3:]  # Remove '/v1' prefix
    
    # Route to appropriate handler
    if normalized_path == '/chat/message':
        if http_method == 'POST':
            return handle_send_message(event)
    elif normalized_path == '/chat/sessions':
        if http_method == 'GET':
            return handle_list_sessions(event)
        elif http_method == 'POST':
            return handle_create_session(event)
    elif normalized_path.startswith('/chat/sessions/') and normalized_path.endswith('/messages') and path_params and 'id' in path_params:
        session_id = path_params['id']
        if http_method == 'GET':
            return handle_get_messages(session_id, event)
    
    return create_error_response(404, "Endpoint not found")


def handle_send_message(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle POST /chat/message - Send message to orchestrator agent.
    
    Required fields:
    - content: Message content
    
    Optional fields:
    - sessionId: Chat session ID (for frontend tracking only)
    - attachments: List of document attachments
    
    Returns:
        User message and agent response
    """
    try:
        body = parse_event_body(event)
        
        # Validate required fields
        validation_error = validate_required_fields(body, ['content'])
        if validation_error:
            return create_error_response(400, validation_error, "VALIDATION_ERROR")
        
        session_id = body.get('sessionId', generate_uuid())
        message_content = body['content']
        attachments = body.get('attachments', [])
        
        # Invoke orchestrator agent directly (no database storage)
        agent_response = invoke_orchestrator_agent(message_content, attachments)
        
        return create_response(200, {
            'sessionId': session_id,
            'userMessage': {
                'content': message_content,
                'timestamp': get_current_timestamp().isoformat(),
                'attachments': attachments
            },
            'agentResponse': {
                'content': agent_response['content'],
                'timestamp': get_current_timestamp().isoformat(),
                'metadata': agent_response.get('metadata', {})
            }
        })
        
    except Exception as e:
        logger.error(f"Error in handle_send_message: {str(e)}")
        return create_error_response(500, "Internal server error")


def handle_list_sessions(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle GET /chat/sessions - Return empty list since we don't store sessions.
    """
    try:
        return create_response(200, {
            'sessions': [],
            'pagination': {
                'limit': 20,
                'offset': 0,
                'total': 0,
                'count': 0
            }
        })
        
    except Exception as e:
        logger.error(f"Error in handle_list_sessions: {str(e)}")
        return create_error_response(500, "Internal server error")


def handle_create_session(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle POST /chat/sessions - Create a new session ID (no storage).
    """
    try:
        body = parse_event_body(event)
        session_id = generate_uuid()
        
        return create_response(201, {
            'sessionId': session_id,
            'title': body.get('title', 'New Chat'),
            'created_at': get_current_timestamp().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in handle_create_session: {str(e)}")
        return create_error_response(500, "Internal server error")


def handle_get_messages(session_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle GET /chat/sessions/{id}/messages - Return empty list since we don't store messages.
    """
    try:
        return create_response(200, {
            'messages': [],
            'sessionId': session_id,
            'pagination': {
                'limit': 50,
                'offset': 0,
                'total': 0,
                'count': 0
            }
        })
        
    except Exception as e:
        logger.error(f"Error in handle_get_messages: {str(e)}")
        return create_error_response(500, "Internal server error")


def invoke_orchestrator_agent(message: str, attachments: list = None) -> Dict[str, Any]:
    """
    Invoke the orchestrator agent with the user message.
    
    Args:
        message: User message content
        attachments: Optional list of document attachments
        
    Returns:
        Agent response dictionary
    """
    try:
        # Get agent configuration from SSM
        agent_id = ssm_config.get_parameter('/healthcare/bedrock/orchestrator-agent-id')
        agent_alias_id = ssm_config.get_parameter('/healthcare/bedrock/orchestrator-agent-alias-id', 'TSTALIASID')
        
        # Prepare the request
        request_params = {
            'agentId': agent_id,
            'agentAliasId': agent_alias_id,
            'sessionId': generate_uuid(),  # Each request gets a new session
            'inputText': message
        }
        
        # Add attachments if provided
        if attachments:
            # Convert attachments to agent format
            request_params['sessionState'] = {
                'sessionAttributes': {
                    'attachments': str(attachments)
                }
            }
        
        logger.info(f"Invoking orchestrator agent with message: {message[:100]}...")
        
        # Invoke the agent
        response = bedrock_agent_runtime.invoke_agent(**request_params)
        
        # Process the response
        agent_response = ""
        metadata = {}
        
        # Handle streaming response
        if 'completion' in response:
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        agent_response += chunk['bytes'].decode('utf-8')
                elif 'trace' in event:
                    # Extract metadata from trace
                    trace = event['trace']
                    if 'orchestrationTrace' in trace:
                        metadata.update(trace['orchestrationTrace'])
        
        return {
            'content': agent_response.strip() if agent_response else "I'm sorry, I couldn't process your request at the moment.",
            'metadata': metadata
        }
        
    except Exception as e:
        logger.error(f"Error invoking orchestrator agent: {str(e)}")
        return {
            'content': "I'm sorry, I'm experiencing technical difficulties. Please try again later.",
            'metadata': {'error': str(e)}
        }
