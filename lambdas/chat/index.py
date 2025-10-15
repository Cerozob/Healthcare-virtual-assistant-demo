"""
Chat Lambda Function
Handles chat requests and orchestrates communication with Bedrock agents.

Supports:
- POST /chat/message - Send message to orchestrator agent
- GET /chat/sessions - List chat sessions
- POST /chat/sessions - Create new chat session
- GET /chat/sessions/{id}/messages - Get message history

TODO: Implement WebSocket support for real-time messaging
TODO: Add authentication and authorization
TODO: Implement rate limiting
"""

import json
import os
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from shared.datetime_utils import get_current_iso8601, to_iso8601, generate_timestamp_id

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
DB_CLUSTER_ARN = os.environ.get("DB_CLUSTER_ARN", "")
DB_SECRET_ARN = os.environ.get("DB_SECRET_ARN", "")
DB_NAME = os.environ.get("DB_NAME", "healthcare")
# TODO: Set these after deploying Bedrock agents
ORCHESTRATOR_AGENT_ID = os.environ.get("ORCHESTRATOR_AGENT_ID", "")
ORCHESTRATOR_AGENT_ALIAS_ID = os.environ.get("ORCHESTRATOR_AGENT_ALIAS_ID", "")

# AWS clients
rds_data_client = boto3.client("rds-data")
bedrock_agent_runtime = boto3.client("bedrock-agent-runtime")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for chat requests.
    Routes to appropriate handler based on HTTP method and path.
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        http_method = event.get("httpMethod", "")
        path = event.get("path", "")
        path_parameters = event.get("pathParameters") or {}
        
        # Route to appropriate handler
        if path == "/chat/message" or path.endswith("/chat"):
            # POST /chat/message - Send message to orchestrator
            if http_method == "POST":
                return handle_send_message(event)
        
        elif path == "/chat/sessions":
            # GET /chat/sessions - List sessions
            if http_method == "GET":
                return handle_list_sessions(event)
            # POST /chat/sessions - Create new session
            elif http_method == "POST":
                return handle_create_session(event)
        
        elif "/chat/sessions/" in path and path.endswith("/messages"):
            # GET /chat/sessions/{id}/messages - Get message history
            if http_method == "GET":
                session_id = path_parameters.get("id")
                return handle_get_messages(session_id, event)
        
        # TODO: Add WebSocket support
        # elif event.get("requestContext", {}).get("eventType") == "CONNECT":
        #     return handle_websocket_connect(event)
        # elif event.get("requestContext", {}).get("eventType") == "DISCONNECT":
        #     return handle_websocket_disconnect(event)
        # elif event.get("requestContext", {}).get("eventType") == "MESSAGE":
        #     return handle_websocket_message(event)
        
        return create_response(404, {"error": "Endpoint no encontrado"})

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return create_response(500, {"error": "Error interno del servidor"})


def handle_send_message(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle POST /chat/message - Send message to orchestrator agent.
    """
    try:
        body = json.loads(event.get("body", "{}"))
        session_id = body.get("sessionId")
        message_content = body.get("content")
        attachments = body.get("attachments", [])
        
        if not message_content:
            return create_response(400, {"error": "El contenido del mensaje es obligatorio"})
        
        # Create session if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
            create_chat_session(session_id)
        
        # Save user message to database
        user_message_id = save_message(
            session_id=session_id,
            content=message_content,
            message_type="user",
            metadata={"attachments": attachments}
        )
        
        # Get conversation context
        context = build_conversation_context(session_id)
        
        # TODO: Invoke orchestrator agent (pending agent deployment)
        # agent_response = invoke_orchestrator_agent(message_content, context, attachments)
        
        # Placeholder agent response
        agent_response = {
            "content": "Integración del agente orquestador pendiente. Se necesita configurar el ID del agente y el ID del alias.",
            "metadata": {
                "agent_type": "orchestrator",
                "routed_to": None
            }
        }
        
        # Save agent response to database
        agent_message_id = save_message(
            session_id=session_id,
            content=agent_response["content"],
            message_type="agent",
            agent_type="orchestrator",
            metadata=agent_response.get("metadata", {})
        )
        
        # Update session context
        update_session_context(session_id, context)
        
        return create_response(200, {
            "sessionId": session_id,
            "userMessage": {
                "id": user_message_id,
                "content": message_content,
                "type": "user",
                "timestamp": get_current_iso8601()
            },
            "agentMessage": {
                "id": agent_message_id,
                "content": agent_response["content"],
                "type": "agent",
                "agentType": "orchestrator",
                "timestamp": get_current_iso8601(),
                "metadata": agent_response.get("metadata", {})
            }
        })
        
    except Exception as e:
        logger.error(f"Error handling send message: {str(e)}", exc_info=True)
        return create_response(500, {"error": str(e)})


def handle_list_sessions(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle GET /chat/sessions - List chat sessions.
    """
    try:
        query_params = event.get("queryStringParameters") or {}
        limit = int(query_params.get("limit", 50))
        offset = int(query_params.get("offset", 0))
        
        sql = """
        SELECT 
            session_id, created_at, updated_at, is_active,
            (SELECT COUNT(*) FROM chat_messages WHERE session_id = cs.session_id) as message_count
        FROM chat_sessions cs
        ORDER BY updated_at DESC
        LIMIT :limit OFFSET :offset
        """
        
        params = [
            {"name": "limit", "value": {"longValue": limit}},
            {"name": "offset", "value": {"longValue": offset}}
        ]
        
        response = execute_sql(sql, params)
        sessions = parse_records(response.get("records", []), response.get("columnMetadata", []))
        
        return create_response(200, {
            "sessions": sessions,
            "count": len(sessions)
        })
        
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}", exc_info=True)
        return create_response(500, {"error": str(e)})


def handle_create_session(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle POST /chat/sessions - Create new chat session.
    """
    try:
        body = json.loads(event.get("body", "{}"))
        session_id = body.get("sessionId") or str(uuid.uuid4())
        initial_context = body.get("context", {})
        
        create_chat_session(session_id, initial_context)
        
        return create_response(201, {
            "sessionId": session_id,
            "createdAt": get_current_iso8601(),
            "isActive": True
        })
        
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}", exc_info=True)
        return create_response(500, {"error": str(e)})


def handle_get_messages(session_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle GET /chat/sessions/{id}/messages - Get message history.
    """
    try:
        if not session_id:
            return create_response(400, {"error": "El ID de sesión es obligatorio"})
        
        query_params = event.get("queryStringParameters") or {}
        limit = int(query_params.get("limit", 100))
        offset = int(query_params.get("offset", 0))
        
        sql = """
        SELECT 
            message_id, session_id, message_type, content,
            agent_type, metadata, created_at
        FROM chat_messages
        WHERE session_id = :session_id
        ORDER BY created_at ASC
        LIMIT :limit OFFSET :offset
        """
        
        params = [
            {"name": "session_id", "value": {"stringValue": session_id}},
            {"name": "limit", "value": {"longValue": limit}},
            {"name": "offset", "value": {"longValue": offset}}
        ]
        
        response = execute_sql(sql, params)
        messages = parse_records(response.get("records", []), response.get("columnMetadata", []))
        
        return create_response(200, {
            "sessionId": session_id,
            "messages": messages,
            "count": len(messages)
        })
        
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}", exc_info=True)
        return create_response(500, {"error": str(e)})


def invoke_orchestrator_agent(
    message: str,
    context: Dict[str, Any],
    attachments: list = None,
) -> Dict[str, Any]:
    """
    Invoke the Bedrock orchestrator agent.
    
    TODO: Implement after agent deployment
    TODO: Add streaming response handling
    TODO: Add retry logic with exponential backoff
    TODO: Handle agent errors and fallbacks
    TODO: Parse agent response and extract structured data
    TODO: Handle citations and references
    """
    try:
        if not ORCHESTRATOR_AGENT_ID or not ORCHESTRATOR_AGENT_ALIAS_ID:
            logger.warning("Orchestrator agent not configured")
            return {
                "content": "Agente orquestador aún no configurado. Por favor configure las variables de entorno ORCHESTRATOR_AGENT_ID y ORCHESTRATOR_AGENT_ALIAS_ID.",
                "metadata": {"error": "agent_not_configured"}
            }
        
        # Build session attributes for context
        session_attributes = {
            "conversationHistory": json.dumps(context.get("recent_messages", [])),
            "patientContext": json.dumps(context.get("patient_context", {}))
        }
        
        # TODO: Invoke agent with streaming
        response = bedrock_agent_runtime.invoke_agent(
            agentId=ORCHESTRATOR_AGENT_ID,
            agentAliasId=ORCHESTRATOR_AGENT_ALIAS_ID,
            sessionId=context.get("session_id"),
            inputText=message,
            sessionState={
                "sessionAttributes": session_attributes
            },
            enableTrace=True  # For debugging
        )
        
        # TODO: Process streaming response
        # TODO: Extract completion text
        # TODO: Extract trace information
        # TODO: Extract citations
        
        completion_text = ""
        agent_metadata = {}
        
        # Process event stream
        for event in response.get("completion", []):
            if "chunk" in event:
                chunk = event["chunk"]
                if "bytes" in chunk:
                    completion_text += chunk["bytes"].decode("utf-8")
            elif "trace" in event:
                # Extract trace information for debugging
                trace = event["trace"]
                agent_metadata["trace"] = trace
        
        return {
            "content": completion_text or "Sin respuesta del agente",
            "metadata": agent_metadata,
            "context_updates": {}
        }

    except ClientError as e:
        logger.error(f"Error invoking orchestrator agent: {str(e)}")
        return {
            "content": "Disculpe, estoy experimentando dificultades técnicas. Por favor intente nuevamente.",
            "metadata": {"error": str(e)}
        }
    except Exception as e:
        logger.error(f"Unexpected error invoking agent: {str(e)}")
        raise


def create_chat_session(session_id: str, initial_context: Dict[str, Any] = None) -> None:
    """Create a new chat session in the database."""
    try:
        sql = """
        INSERT INTO chat_sessions (session_id, context, is_active)
        VALUES (:session_id, :context::jsonb, true)
        ON CONFLICT (session_id) DO NOTHING
        """
        
        params = [
            {"name": "session_id", "value": {"stringValue": session_id}},
            {"name": "context", "value": {"stringValue": json.dumps(initial_context or {})}}
        ]
        
        execute_sql(sql, params)
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
    """Save a message to the database and return message ID."""
    try:
        message_id = str(uuid.uuid4())
        
        sql = """
        INSERT INTO chat_messages (
            message_id, session_id, message_type, content, agent_type, metadata
        ) VALUES (
            :message_id, :session_id, :message_type, :content, :agent_type, :metadata::jsonb
        )
        RETURNING message_id
        """
        
        params = [
            {"name": "message_id", "value": {"stringValue": message_id}},
            {"name": "session_id", "value": {"stringValue": session_id}},
            {"name": "message_type", "value": {"stringValue": message_type}},
            {"name": "content", "value": {"stringValue": content}},
            {"name": "agent_type", "value": {"stringValue": agent_type} if agent_type else {"isNull": True}},
            {"name": "metadata", "value": {"stringValue": json.dumps(metadata or {})}}
        ]
        
        execute_sql(sql, params)
        logger.info(f"Saved message: {message_id}")
        
        # Update session timestamp
        update_sql = """
        UPDATE chat_sessions
        SET updated_at = CURRENT_TIMESTAMP
        WHERE session_id = :session_id
        """
        execute_sql(update_sql, [{"name": "session_id", "value": {"stringValue": session_id}}])
        
        return message_id
        
    except Exception as e:
        logger.error(f"Error saving message: {str(e)}")
        raise


def build_conversation_context(session_id: str) -> Dict[str, Any]:
    """
    Build conversation context from session history.
    Retrieves recent messages for context window.
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
        
        params = [{"name": "session_id", "value": {"stringValue": session_id}}]
        response = execute_sql(sql, params)
        
        messages = parse_records(response.get("records", []), response.get("columnMetadata", []))
        messages.reverse()  # Chronological order
        
        # Get session context
        session_sql = """
        SELECT context FROM chat_sessions WHERE session_id = :session_id
        """
        session_response = execute_sql(session_sql, params)
        session_records = parse_records(
            session_response.get("records", []),
            session_response.get("columnMetadata", [])
        )
        
        session_context = {}
        if session_records:
            context_str = session_records[0].get("context", "{}")
            if isinstance(context_str, str):
                session_context = json.loads(context_str)
            else:
                session_context = context_str or {}
        
        return {
            "session_id": session_id,
            "recent_messages": messages,
            "patient_context": session_context.get("patient_context", {}),
            "conversation_summary": session_context.get("summary", "")
        }
        
    except Exception as e:
        logger.error(f"Error building conversation context: {str(e)}")
        return {
            "session_id": session_id,
            "recent_messages": [],
            "patient_context": {},
            "conversation_summary": ""
        }


def update_session_context(session_id: str, context: Dict[str, Any]) -> None:
    """Update session context in the database."""
    try:
        sql = """
        UPDATE chat_sessions
        SET context = :context::jsonb, updated_at = CURRENT_TIMESTAMP
        WHERE session_id = :session_id
        """
        
        params = [
            {"name": "session_id", "value": {"stringValue": session_id}},
            {"name": "context", "value": {"stringValue": json.dumps(context)}}
        ]
        
        execute_sql(sql, params)
        
    except Exception as e:
        logger.error(f"Error updating session context: {str(e)}")


def execute_sql(sql: str, parameters: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Execute SQL statement using RDS Data API."""
    try:
        kwargs = {
            "resourceArn": DB_CLUSTER_ARN,
            "secretArn": DB_SECRET_ARN,
            "database": DB_NAME,
            "sql": sql
        }
        
        if parameters:
            kwargs["parameters"] = parameters
        
        response = rds_data_client.execute_statement(**kwargs)
        return response
        
    except ClientError as e:
        logger.error(f"Database error: {str(e)}")
        raise


def parse_records(records: List[List[Dict[str, Any]]], column_metadata: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Parse RDS Data API records into dictionaries."""
    result = []
    
    for record in records:
        parsed = {}
        for i, field in enumerate(record):
            # Get column name if metadata available
            col_name = f"field_{i}"
            if column_metadata and i < len(column_metadata):
                col_name = column_metadata[i].get("name", col_name)
            
            # Extract value
            if "stringValue" in field:
                value = field["stringValue"]
            elif "longValue" in field:
                value = field["longValue"]
            elif "doubleValue" in field:
                value = field["doubleValue"]
            elif "booleanValue" in field:
                value = field["booleanValue"]
            elif "isNull" in field and field["isNull"]:
                value = None
            else:
                value = None
            
            # Try to parse JSON strings
            if isinstance(value, str) and (value.startswith("{") or value.startswith("[")):
                try:
                    value = json.loads(value)
                except:
                    pass
            
            parsed[col_name] = value
        
        result.append(parsed)
    
    return result


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create HTTP response with CORS headers"""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",  # TODO: Configure proper CORS
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
        "body": json.dumps(body),
    }


# TODO: Add WebSocket handler functions
def handle_websocket_connect(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle WebSocket connection.
    
    TODO: Authenticate connection
    TODO: Store connection ID
    TODO: Initialize session
    """
    pass


def handle_websocket_disconnect(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle WebSocket disconnection.
    
    TODO: Clean up connection
    TODO: Archive session if needed
    """
    pass


def handle_websocket_message(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle WebSocket message.
    
    TODO: Process message
    TODO: Stream response back to client
    TODO: Handle typing indicators
    """
    pass


def send_websocket_message(connection_id: str, message: Dict[str, Any]):
    """
    Send message to WebSocket client.
    
    TODO: Implement using API Gateway Management API
    TODO: Handle connection errors
    TODO: Implement retry logic
    """
    pass
