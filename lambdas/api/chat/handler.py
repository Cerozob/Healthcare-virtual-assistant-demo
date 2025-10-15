"""
Chat API Lambda Function.
Handles chat operations and orchestrates communication with Bedrock agents.
Consolidates functionality from both Node.js and Python chat implementations.

Endpoints:
- POST /chat/message - Send message to orchestrator agent
- GET /chat/sessions - List chat sessions
- POST /chat/sessions - Create new chat session
- GET /chat/sessions/{id}/messages - Get message history
"""

import json
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from shared.database import DatabaseManager, DatabaseError
from shared.ssm_config import SSMConfig
from shared.utils import (
    create_response, create_error_response, parse_event_body,
    extract_path_parameters, extract_query_parameters, validate_required_fields,
    validate_pagination_params, handle_exceptions, generate_uuid, get_current_timestamp
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients and managers
db_manager = DatabaseManager()
ssm_config = SSMConfig()
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')


@handle_exceptions
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for chat requests.
    Routes to appropriate handler based on HTTP method and path.
    """
    http_method = event.get('httpMethod', '')
    path = event.get('path', '')
    path_params = extract_path_parameters(event)
    
    # Route to appropriate handler
    if path == '/chat/message' or path.endswith('/chat'):
        if http_method == 'POST':
            return handle_send_message(event)
    elif path == '/chat/sessions':
        if http_method == 'GET':
            return handle_list_sessions(event)
        elif http_method == 'POST':
            return handle_create_session(event)
    elif path.startswith('/chat/sessions/') and path.endswith('/messages') and 'id' in path_params:
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
    - sessionId: Chat session ID (will create new if not provided)
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
        
        session_id = body.get('sessionId')
        message_content = body['content']
        attachments = body.get('attachments', [])
        
        # Create session if not provided
        if not session_id:
            session_id = generate_uuid()
            create_chat_session(session_id)
        
        # Store user message
        user_message_id = save_message(
            session_id=session_id,
            content=message_content,
            message_type='user',
            metadata={'attachments': attachments}
        )
        
        # Get conversation context
        context = build_conversation_context(session_id)
        
        # Invoke orchestrator agent
        agent_response = invoke_orchestrator_agent(message_content, context, attachments)
        
        # Store agent response
        agent_message_id = save_message(
            session_id=session_id,
            content=agent_response['content'],
            message_type='agent',
            agent_type='orchestrator',
            metadata=agent_response.get('metadata', {})
        )
        
        # Update session context
        update_session_context(session_id, context)
        
        return create_response(200, {
            'sessionId': session_id,
            'userMessage': {
                'id': user_message_id,
                'content': message_content,
                'type': 'user',
                'timestamp': get_current_timestamp()
            },
            'agentMessage': {
                'id': agent_message_id,
                'content': agent_response['content'],
                'type': 'agent',
                'agentType': 'orchestrator',
                'timestamp': get_current_timestamp(),
                'metadata': agent_response.get('metadata', {})
            }
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in handle_send_message: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in handle_send_message: {str(e)}")
        return create_error_response(500, "Internal server error")


def handle_list_sessions(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle GET /chat/sessions - List chat sessions.
    
    Query parameters:
    - limit: Number of sessions to return (default: 20, max: 100)
    - offset: Number of sessions to skip (default: 0)
    
    Returns:
        List of chat sessions with message counts
    """
    try:
        query_params = extract_query_parameters(event)
        pagination = validate_pagination_params(query_params)
        
        # Limit max sessions to 100 for chat
        if pagination['limit'] > 100:
            pagination['limit'] = 100
        
        sql = """
        SELECT 
            cs.session_id, cs.title, cs.created_at, cs.updated_at, cs.is_active,
            COUNT(cm.message_id) as message_count
        FROM chat_sessions cs
        LEFT JOIN chat_messages cm ON cs.session_id = cm.session_id
        GROUP BY cs.session_id, cs.title, cs.created_at, cs.updated_at, cs.is_active
        ORDER BY cs.updated_at DESC
        LIMIT :limit OFFSET :offset
        """
        
        parameters = [
            db_manager.create_parameter('limit', pagination['limit'], 'long'),
            db_manager.create_parameter('offset', pagination['offset'], 'long')
        ]
        
        response = db_manager.execute_sql(sql, parameters)
        sessions = db_manager.parse_records(
            response.get('records', []),
            response.get('columnMetadata', [])
        )
        
        # Get total count
        count_sql = "SELECT COUNT(*) as total FROM chat_sessions"
        count_response = db_manager.execute_sql(count_sql)
        total_count = 0
        if count_response.get('records'):
            total_count = count_response['records'][0][0].get('longValue', 0)
        
        return create_response(200, {
            'sessions': sessions,
            'pagination': {
                'limit': pagination['limit'],
                'offset': pagination['offset'],
                'total': total_count,
                'count': len(sessions)
            }
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in handle_list_sessions: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in handle_list_sessions: {str(e)}")
        return create_error_response(500, "Internal server error")


def handle_create_session(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle POST /chat/sessions - Create new chat session.
    
    Optional fields:
    - title: Session title
    - sessionId: Specific session ID (will generate if not provided)
    - context: Initial session context
    
    Returns:
        Created session information
    """
    try:
        body = parse_event_body(event)
        
        session_id = body.get('sessionId', generate_uuid())
        title = body.get('title')
        initial_context = body.get('context', {})
        
        create_chat_session(session_id, title, initial_context)
        
        return create_response(201, {
            'message': 'Chat session created successfully',
            'session': {
                'sessionId': session_id,
                'title': title,
                'createdAt': get_current_timestamp(),
                'isActive': True
            }
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in handle_create_session: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in handle_create_session: {str(e)}")
        return create_error_response(500, "Internal server error")


def handle_get_messages(session_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle GET /chat/sessions/{id}/messages - Get message history.
    
    Args:
        session_id: Chat session ID
        event: Lambda event
    
    Query parameters:
    - limit: Number of messages to return (default: 100, max: 500)
    - offset: Number of messages to skip (default: 0)
    
    Returns:
        List of messages for the session
    """
    try:
        if not session_id:
            return create_error_response(400, "Session ID is required", "MISSING_SESSION_ID")
        
        query_params = extract_query_parameters(event)
        pagination = validate_pagination_params(query_params)
        
        # Limit max messages to 500 for chat
        if pagination['limit'] > 500:
            pagination['limit'] = 500
        
        sql = """
        SELECT 
            message_id, session_id, message_type, content,
            agent_type, metadata, created_at
        FROM chat_messages
        WHERE session_id = :session_id
        ORDER BY created_at ASC
        LIMIT :limit OFFSET :offset
        """
        
        parameters = [
            db_manager.create_parameter('session_id', session_id, 'string'),
            db_manager.create_parameter('limit', pagination['limit'], 'long'),
            db_manager.create_parameter('offset', pagination['offset'], 'long')
        ]
        
        response = db_manager.execute_sql(sql, parameters)
        messages = db_manager.parse_records(
            response.get('records', []),
            response.get('columnMetadata', [])
        )
        
        # Get total message count for session
        count_sql = "SELECT COUNT(*) as total FROM chat_messages WHERE session_id = :session_id"
        count_params = [db_manager.create_parameter('session_id', session_id, 'string')]
        count_response = db_manager.execute_sql(count_sql, count_params)
        total_count = 0
        if count_response.get('records'):
            total_count = count_response['records'][0][0].get('longValue', 0)
        
        return create_response(200, {
            'sessionId': session_id,
            'messages': messages,
            'pagination': {
                'limit': pagination['limit'],
                'offset': pagination['offset'],
                'total': total_count,
                'count': len(messages)
            }
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in handle_get_messages: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in handle_get_messages: {str(e)}")
        return create_error_response(500, "Internal server error")


def invoke_orchestrator_agent(
    message: str,
    context: Dict[str, Any],
    attachments: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Invoke the Bedrock orchestrator agent.
    
    Args:
        message: User message
        context: Conversation context
        attachments: Optional document attachments
        
    Returns:
        Agent response dictionary
    """
    try:
        orchestrator_agent_id = ssm_config.get_orchestrator_agent_id()
        orchestrator_alias_id = ssm_config.get_orchestrator_alias_id()
        
        if not orchestrator_agent_id or not orchestrator_alias_id:
            logger.warning("Orchestrator agent not configured")
            return {
                'content': 'Orchestrator agent not yet configured. Please configure ORCHESTRATOR_AGENT_ID and ORCHESTRATOR_ALIAS_ID in SSM parameters.',
                'metadata': {'error': 'agent_not_configured'}
            }
        
        # Build session attributes for context
        session_attributes = {
            'conversationHistory': json.dumps(context.get('recent_messages', [])),
            'patientContext': json.dumps(context.get('patient_context', {}))
        }
        
        if attachments:
            session_attributes['attachments'] = json.dumps(attachments)
        
        # Invoke agent
        response = bedrock_agent_runtime.invoke_agent(
            agentId=orchestrator_agent_id,
            agentAliasId=orchestrator_alias_id,
            sessionId=context.get('session_id'),
            inputText=message,
            sessionState={
                'sessionAttributes': session_attributes
            },
            enableTrace=True  # For debugging
        )
        
        # Process streaming response
        completion_text = ""
        agent_metadata = {}
        
        for event_item in response.get('completion', []):
            if 'chunk' in event_item:
                chunk = event_item['chunk']
                if 'bytes' in chunk:
                    completion_text += chunk['bytes'].decode('utf-8')
            elif 'trace' in event_item:
                # Extract trace information for debugging
                trace = event_item['trace']
                agent_metadata['trace'] = trace
        
        return {
            'content': completion_text or 'No response from agent',
            'metadata': agent_metadata
        }
        
    except ClientError as e:
        logger.error(f"Error invoking orchestrator agent: {str(e)}")
        return {
            'content': 'I apologize, but I am experiencing technical difficulties. Please try again.',
            'metadata': {'error': str(e)}
        }
    
    except Exception as e:
        logger.error(f"Unexpected error invoking agent: {str(e)}")
        return {
            'content': 'An unexpected error occurred. Please try again.',
            'metadata': {'error': str(e)}
        }


def create_chat_session(session_id: str, title: str = None, initial_context: Dict[str, Any] = None) -> None:
    """
    Create a new chat session in the database.
    
    Args:
        session_id: Session ID
        title: Optional session title
        initial_context: Optional initial context
    """
    try:
        session_title = title or f"Chat Session {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
        
        sql = """
        INSERT INTO chat_sessions (session_id, title, context, is_active, created_at, updated_at)
        VALUES (:session_id, :title, :context, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (session_id) DO UPDATE SET
            title = EXCLUDED.title,
            updated_at = CURRENT_TIMESTAMP
        """
        
        parameters = [
            db_manager.create_parameter('session_id', session_id, 'string'),
            db_manager.create_parameter('title', session_title, 'string'),
            db_manager.create_parameter('context', json.dumps(initial_context or {}), 'string')
        ]
        
        db_manager.execute_sql(sql, parameters)
        logger.info(f"Created chat session: {session_id}")
        
    except Exception as e:
        logger.error(f"Error creating chat session: {str(e)}")
        raise


def save_message(
    session_id: str,
    content: str,
    message_type: str,
    agent_type: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save a message to the database.
    
    Args:
        session_id: Session ID
        content: Message content
        message_type: Type of message ('user', 'agent', 'system')
        agent_type: Type of agent (if message_type is 'agent')
        metadata: Optional metadata
        
    Returns:
        Message ID
    """
    try:
        message_id = generate_uuid()
        
        sql = """
        INSERT INTO chat_messages (
            message_id, session_id, message_type, content, agent_type, metadata, created_at
        ) VALUES (
            :message_id, :session_id, :message_type, :content, :agent_type, :metadata, CURRENT_TIMESTAMP
        )
        """
        
        parameters = [
            db_manager.create_parameter('message_id', message_id, 'string'),
            db_manager.create_parameter('session_id', session_id, 'string'),
            db_manager.create_parameter('message_type', message_type, 'string'),
            db_manager.create_parameter('content', content, 'string'),
            db_manager.create_parameter('agent_type', agent_type, 'string'),
            db_manager.create_parameter('metadata', json.dumps(metadata or {}), 'string')
        ]
        
        db_manager.execute_sql(sql, parameters)
        
        # Update session timestamp
        update_sql = """
        UPDATE chat_sessions
        SET updated_at = CURRENT_TIMESTAMP
        WHERE session_id = :session_id
        """
        update_params = [db_manager.create_parameter('session_id', session_id, 'string')]
        db_manager.execute_sql(update_sql, update_params)
        
        logger.info(f"Saved message: {message_id}")
        return message_id
        
    except Exception as e:
        logger.error(f"Error saving message: {str(e)}")
        raise


def build_conversation_context(session_id: str) -> Dict[str, Any]:
    """
    Build conversation context from session history.
    
    Args:
        session_id: Session ID
        
    Returns:
        Context dictionary with recent messages and session info
    """
    try:
        # Get recent messages (last 10 for context)
        sql = """
        SELECT message_type, content, agent_type, created_at
        FROM chat_messages
        WHERE session_id = :session_id
        ORDER BY created_at DESC
        LIMIT 10
        """
        
        parameters = [db_manager.create_parameter('session_id', session_id, 'string')]
        response = db_manager.execute_sql(sql, parameters)
        
        messages = db_manager.parse_records(
            response.get('records', []),
            response.get('columnMetadata', [])
        )
        messages.reverse()  # Chronological order
        
        # Get session context
        session_sql = """
        SELECT context FROM chat_sessions WHERE session_id = :session_id
        """
        session_response = db_manager.execute_sql(session_sql, parameters)
        session_records = db_manager.parse_records(
            session_response.get('records', []),
            session_response.get('columnMetadata', [])
        )
        
        session_context = {}
        if session_records:
            context_str = session_records[0].get('context', '{}')
            if isinstance(context_str, str):
                try:
                    session_context = json.loads(context_str)
                except json.JSONDecodeError:
                    session_context = {}
            else:
                session_context = context_str or {}
        
        return {
            'session_id': session_id,
            'recent_messages': messages,
            'patient_context': session_context.get('patient_context', {}),
            'conversation_summary': session_context.get('summary', '')
        }
        
    except Exception as e:
        logger.error(f"Error building conversation context: {str(e)}")
        return {
            'session_id': session_id,
            'recent_messages': [],
            'patient_context': {},
            'conversation_summary': ''
        }


def update_session_context(session_id: str, context: Dict[str, Any]) -> None:
    """
    Update session context in the database.
    
    Args:
        session_id: Session ID
        context: Updated context
    """
    try:
        sql = """
        UPDATE chat_sessions
        SET context = :context, updated_at = CURRENT_TIMESTAMP
        WHERE session_id = :session_id
        """
        
        parameters = [
            db_manager.create_parameter('session_id', session_id, 'string'),
            db_manager.create_parameter('context', json.dumps(context), 'string')
        ]
        
        db_manager.execute_sql(sql, parameters)
        
    except Exception as e:
        logger.error(f"Error updating session context: {str(e)}")
