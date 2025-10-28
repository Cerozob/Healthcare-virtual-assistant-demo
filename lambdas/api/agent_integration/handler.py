"""
Agent Integration API Lambda Function.
Handles AgentCore proxy requests only.

Endpoints:
- POST /agentcore/chat - Proxy requests to AgentCore runtime endpoint
- GET /agentcore/health - Health check for AgentCore endpoint
"""

import json
import logging
import uuid
import base64
import traceback
from typing import Dict, Any, Optional
from datetime import datetime
import boto3
from botocore.exceptions import ClientError, BotoCoreError
import os
from shared.utils import (
    create_response, create_error_response, parse_event_body,
    validate_required_fields, handle_exceptions, get_current_timestamp
)

# Configure structured logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create a custom formatter for structured logging


class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'function': record.funcName,
            'line': record.lineno
        }

        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id
        if hasattr(record, 'duration_ms'):
            log_entry['duration_ms'] = record.duration_ms
        if hasattr(record, 'error_code'):
            log_entry['error_code'] = record.error_code
        if hasattr(record, 'agentcore_arn'):
            log_entry['agentcore_arn'] = record.agentcore_arn

        return json.dumps(log_entry)


# Apply structured formatter to the logger
for handler in logger.handlers:
    handler.setFormatter(StructuredFormatter())


def log_with_context(level: str, message: str, **kwargs):
    """Helper function to log with additional context."""
    extra = {k: v for k, v in kwargs.items() if v is not None}
    getattr(logger, level.lower())(message, extra=extra)


# Initialize clients
ssm_client = boto3.client('ssm')
bedrock_agentcore = boto3.client('bedrock-agentcore')


@handle_exceptions
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for AgentCore endpoints only.
    Routes to appropriate handler based on HTTP method and path.
    """
    start_time = datetime.now()
    request_id = context.aws_request_id if context else str(uuid.uuid4())

    # Handle both API Gateway v1 and v2 event formats
    http_method = event.get('httpMethod') or event.get(
        'requestContext', {}).get('http', {}).get('method', '')
    path = event.get('path') or event.get(
        'requestContext', {}).get('http', {}).get('path', '')

    # Extract additional request context
    source_ip = event.get('requestContext', {}).get(
        'identity', {}).get('sourceIp', 'unknown')
    user_agent = event.get('headers', {}).get('User-Agent', 'unknown')

    log_with_context('info',
                     f"Request received: {http_method} {path}",
                     request_id=request_id,
                     source_ip=source_ip,
                     user_agent=user_agent,
                     lambda_version=context.function_version if context else 'unknown',
                     memory_limit=context.memory_limit_in_mb if context else 'unknown'
                     )

    # Normalize path by removing stage prefix if present
    normalized_path = path
    if path.startswith('/v1/'):
        normalized_path = path[3:]  # Remove '/v1' prefix
        log_with_context(
            'debug', f"Normalized path from {path} to {normalized_path}", request_id=request_id)

    try:
        # Route to appropriate handler - only AgentCore endpoints
        if normalized_path == '/agentcore/chat' or normalized_path.endswith('/agentcore/chat'):
            if http_method == 'POST':
                response = handle_agentcore_chat(event, request_id)
            else:
                log_with_context(
                    'warning', f"Method {http_method} not allowed for /agentcore/chat", request_id=request_id)
                response = create_error_response(405, "Method not allowed")
        elif normalized_path == '/agentcore/health' or normalized_path.endswith('/agentcore/health'):
            if http_method == 'GET':
                response = handle_agentcore_health(event, request_id)
            else:
                log_with_context(
                    'warning', f"Method {http_method} not allowed for /agentcore/health", request_id=request_id)
                response = create_error_response(405, "Method not allowed")
        else:
            log_with_context(
                'warning', f"Endpoint not found: {normalized_path}", request_id=request_id)
            response = create_error_response(404, "Endpoint not found")

        # Log response details
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        status_code = response.get('statusCode', 'unknown')

        log_with_context('info',
                         f"Request completed: {status_code}",
                         request_id=request_id,
                         duration_ms=round(duration_ms, 2),
                         status_code=status_code
                         )

        return response

    except Exception as e:
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        log_with_context('error',
                         f"Unhandled exception in lambda_handler: {str(e)}",
                         request_id=request_id,
                         duration_ms=round(duration_ms, 2),
                         error_type=type(e).__name__,
                         traceback=traceback.format_exc()
                         )
        return create_error_response(500, "Internal server error")


def handle_agentcore_chat(event: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    """
    Handle POST /agentcore/chat - Invoke AgentCore runtime directly.

    Invokes the AgentCore runtime using AWS SDK and returns the response.
    """
    function_start_time = datetime.now()

    log_with_context(
        'info', "Starting AgentCore chat request processing", request_id=request_id)

    try:
        # Get AgentCore runtime ARN from SSM parameter
        try:
            agentcore_endpoint_parameter = os.environ.get(
                'AGENTCORE_ENDPOINT_PARAMETER', '/healthcare/agentcore/endpoint-url')

            log_with_context('debug',
                             f"Retrieving AgentCore ARN from SSM parameter: {agentcore_endpoint_parameter}",
                             request_id=request_id
                             )

            ssm_start_time = datetime.now()
            response = ssm_client.get_parameter(
                Name=agentcore_endpoint_parameter)
            ssm_duration = (datetime.now() -
                            ssm_start_time).total_seconds() * 1000

            runtime_arn = response['Parameter']['Value']

            log_with_context('info',
                             f"Retrieved AgentCore runtime ARN successfully",
                             request_id=request_id,
                             agentcore_arn=runtime_arn,
                             ssm_duration_ms=round(ssm_duration, 2)
                             )

        except ClientError as ssm_error:
            error_code = ssm_error.response.get(
                'Error', {}).get('Code', 'Unknown')
            error_message = ssm_error.response.get(
                'Error', {}).get('Message', str(ssm_error))

            log_with_context('error',
                             f"Failed to get AgentCore runtime ARN from SSM: {error_code} - {error_message}",
                             request_id=request_id,
                             error_code=error_code,
                             ssm_parameter=agentcore_endpoint_parameter
                             )
            return create_error_response(503, "AgentCore runtime not configured", "AGENTCORE_NOT_CONFIGURED")
        except Exception as ssm_error:
            log_with_context('error',
                             f"Unexpected error retrieving AgentCore ARN: {str(ssm_error)}",
                             request_id=request_id,
                             error_type=type(ssm_error).__name__,
                             ssm_parameter=agentcore_endpoint_parameter
                             )
            return create_error_response(503, "AgentCore runtime not configured", "AGENTCORE_NOT_CONFIGURED")

        # Get request body
        try:
            body = parse_event_body(event)
            log_with_context('debug',
                             f"Parsed request body with {len(body)} fields",
                             request_id=request_id,
                             body_keys=list(body.keys()) if body else []
                             )
        except Exception as parse_error:
            log_with_context('error',
                             f"Failed to parse request body: {str(parse_error)}",
                             request_id=request_id,
                             error_type=type(parse_error).__name__
                             )
            return create_error_response(400, "Invalid request body", "INVALID_BODY")

        # Validate required fields
        validation_error = validate_required_fields(body, ['message'])
        if validation_error:
            log_with_context('warning',
                             f"Validation failed: {validation_error}",
                             request_id=request_id,
                             provided_fields=list(body.keys()) if body else []
                             )
            return create_error_response(400, validation_error, "VALIDATION_ERROR")

        # Prepare the message content
        message_content = body['message']
        message_length = len(str(message_content))

        log_with_context('debug',
                         f"Processing message with length: {message_length}",
                         request_id=request_id,
                         message_length=message_length
                         )

        # Handle session ID - generate if not provided
        session_id = body.get('sessionId')
        if not session_id:
            # Generate a new session ID with minimum 33 characters as required by AgentCore
            session_id = f'agentcore_session_{uuid.uuid4().hex}'
            log_with_context('info',
                             f"Generated new session ID: {session_id}",
                             request_id=request_id,
                             session_id=session_id
                             )
        else:
            log_with_context('info',
                             f"Using existing session ID: {session_id}",
                             request_id=request_id,
                             session_id=session_id
                             )

        # Prepare payload for AgentCore with multi-modal support
        payload_data = {
            "prompt": message_content
        }

        # Handle file attachments if provided
        attachments = body.get('attachments', [])
        if attachments:
            log_with_context('info',
                             f"Processing {len(attachments)} attachments",
                             request_id=request_id,
                             session_id=session_id,
                             attachment_count=len(attachments)
                             )

            # Add attachment info to the prompt
            attachments_context = "\n\nAttached files:\n"
            for i, attachment in enumerate(attachments):
                file_name = attachment.get('fileName', 'Unknown')
                file_category = attachment.get('category', 'uncategorized')
                file_size = attachment.get(
                    'fileSize', attachment.get('size', 'unknown size'))
                mime_type = attachment.get('mimeType', 'unknown')

                attachments_context += f"- {file_name} ({file_category}, {file_size})\n"

                log_with_context('debug',
                                 f"Attachment {i+1}: {file_name}",
                                 request_id=request_id,
                                 session_id=session_id,
                                 file_name=file_name,
                                 mime_type=mime_type,
                                 file_size=file_size,
                                 category=file_category
                                 )

            payload_data["prompt"] += attachments_context

            # Process file attachments for multi-modal support based on Strands Agents format
            for attachment in attachments:
                if attachment.get('content') and attachment.get('mimeType'):
                    mime_type = attachment['mimeType']
                    file_name = attachment.get('fileName', 'unknown')

                    log_with_context('debug',
                                     f"Processing attachment with MIME type: {mime_type}",
                                     request_id=request_id,
                                     session_id=session_id,
                                     file_name=file_name,
                                     mime_type=mime_type
                                     )

                    if mime_type.startswith('image/'):
                        # Handle images using Strands ImageContent format
                        image_format = mime_type.split('/')[-1]
                        if image_format == 'jpg':
                            image_format = 'jpeg'

                        # Convert base64 to bytes for Strands format
                        image_bytes = base64.b64decode(attachment['content'])

                        payload_data["image"] = {
                            "format": image_format,
                            "source": {
                                "bytes": image_bytes
                            }
                        }

                        log_with_context('info',
                                         f"Added image attachment to payload: {file_name} ({image_format})",
                                         request_id=request_id,
                                         session_id=session_id,
                                         file_name=file_name,
                                         image_format=image_format
                                         )
                        break  # Only support one image for now

                    elif mime_type in ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                                       'application/msword', 'text/plain', 'text/markdown', 'text/csv',
                                       'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                       'application/vnd.ms-excel', 'text/html']:
                        # Handle documents using Strands DocumentContent format
                        document_format_map = {
                            'application/pdf': 'pdf',
                            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
                            'application/msword': 'doc',
                            'text/plain': 'txt',
                            'text/markdown': 'md',
                            'text/csv': 'csv',
                            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
                            'application/vnd.ms-excel': 'xls',
                            'text/html': 'html'
                        }

                        document_format = document_format_map.get(mime_type)
                        if document_format:
                            # Convert base64 to bytes for Strands format
                            document_bytes = base64.b64decode(
                                attachment['content'])

                            payload_data["document"] = {
                                "format": document_format,
                                "name": file_name,
                                "source": {
                                    "bytes": document_bytes
                                }
                            }

                            log_with_context('info',
                                             f"Added document attachment to payload: {file_name} ({document_format})",
                                             request_id=request_id,
                                             session_id=session_id,
                                             file_name=file_name,
                                             document_format=document_format
                                             )
                            break  # Only support one document for now
                        else:
                            log_with_context('warning',
                                             f"Unsupported document MIME type: {mime_type}",
                                             request_id=request_id,
                                             session_id=session_id,
                                             mime_type=mime_type
                                             )
                    else:
                        log_with_context('info',
                                         f"Unsupported attachment type: {mime_type}",
                                         request_id=request_id,
                                         session_id=session_id,
                                         mime_type=mime_type
                                         )
                else:
                    log_with_context('info',
                                     f"Attachment {attachment.get('fileName')} has no content - metadata only",
                                     request_id=request_id,
                                     session_id=session_id,
                                     file_name=attachment.get('fileName')
                                     )

        payload = json.dumps(payload_data).encode('utf-8')

        # Invoke AgentCore runtime
        try:
            payload_size = len(payload)
            log_with_context('info',
                             f"Invoking AgentCore runtime",
                             request_id=request_id,
                             session_id=session_id,
                             agentcore_arn=runtime_arn,
                             payload_size_bytes=payload_size
                             )

            agentcore_start_time = datetime.now()

            response = bedrock_agentcore.invoke_agent_runtime(
                agentRuntimeArn=runtime_arn,
                runtimeSessionId=session_id,
                payload=payload
            )

            agentcore_end_time = datetime.now()
            agentcore_response_time_ms = (
                agentcore_end_time - agentcore_start_time).total_seconds() * 1000

            log_with_context('info',
                             f"AgentCore invocation completed successfully",
                             request_id=request_id,
                             session_id=session_id,
                             agentcore_arn=runtime_arn,
                             agentcore_duration_ms=round(
                                 agentcore_response_time_ms, 2)
                             )

            # Process the response
            try:
                response_body = response['response'].read()
                response_size = len(response_body)
                response_data = json.loads(response_body.decode('utf-8'))

                log_with_context('debug',
                                 f"AgentCore response parsed successfully",
                                 request_id=request_id,
                                 session_id=session_id,
                                 response_size_bytes=response_size
                                 )

            except json.JSONDecodeError as json_error:
                log_with_context('error',
                                 f"Failed to parse AgentCore response JSON: {str(json_error)}",
                                 request_id=request_id,
                                 session_id=session_id,
                                 response_body_preview=response_body[:500].decode(
                                     'utf-8', errors='ignore') if response_body else 'empty'
                                 )
                return create_error_response(502, "Invalid response from AgentCore", "AGENTCORE_INVALID_RESPONSE")

            # Extract the agent's response
            agent_response = response_data.get('output', {})
            if isinstance(agent_response, dict):
                response_text = agent_response.get(
                    'message', str(agent_response))
            else:
                response_text = str(agent_response)

            total_duration_ms = (
                datetime.now() - function_start_time).total_seconds() * 1000

            formatted_response = {
                'response': response_text,
                'sessionId': session_id,
                'timestamp': datetime.now().isoformat(),
                'responseTimeMs': round(agentcore_response_time_ms, 2),
                'totalProcessingTimeMs': round(total_duration_ms, 2)
            }

            log_with_context('info',
                             f"Chat request completed successfully",
                             request_id=request_id,
                             session_id=session_id,
                             agentcore_duration_ms=round(
                                 agentcore_response_time_ms, 2),
                             total_duration_ms=round(total_duration_ms, 2),
                             response_length=len(str(response_text))
                             )

            return create_response(200, formatted_response)

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))

            agentcore_duration_ms = (datetime.now() - agentcore_start_time).total_seconds(
            ) * 1000 if 'agentcore_start_time' in locals() else 0

            log_with_context('error',
                             f"AgentCore invocation failed: {error_code} - {error_message}",
                             request_id=request_id,
                             session_id=session_id,
                             agentcore_arn=runtime_arn,
                             error_code=error_code,
                             agentcore_duration_ms=round(
                                 agentcore_duration_ms, 2),
                             aws_error_details=e.response.get('Error', {})
                             )

            return create_error_response(500, f"AgentCore invocation failed: {error_message}", "AGENTCORE_INVOCATION_FAILED")

        except BotoCoreError as e:
            agentcore_duration_ms = (datetime.now() - agentcore_start_time).total_seconds(
            ) * 1000 if 'agentcore_start_time' in locals() else 0

            log_with_context('error',
                             f"BotoCore error during AgentCore invocation: {str(e)}",
                             request_id=request_id,
                             session_id=session_id,
                             agentcore_arn=runtime_arn,
                             error_type=type(e).__name__,
                             agentcore_duration_ms=round(
                                 agentcore_duration_ms, 2)
                             )

            return create_error_response(502, "Network error communicating with AgentCore", "AGENTCORE_NETWORK_ERROR")

        except Exception as e:
            agentcore_duration_ms = (datetime.now() - agentcore_start_time).total_seconds(
            ) * 1000 if 'agentcore_start_time' in locals() else 0

            log_with_context('error',
                             f"Unexpected error during AgentCore invocation: {str(e)}",
                             request_id=request_id,
                             session_id=session_id,
                             agentcore_arn=runtime_arn,
                             error_type=type(e).__name__,
                             agentcore_duration_ms=round(
                                 agentcore_duration_ms, 2),
                             traceback=traceback.format_exc()
                             )

            return create_error_response(500, "Unexpected error during AgentCore invocation", "AGENTCORE_UNEXPECTED_ERROR")

    except Exception as e:
        total_duration_ms = (
            datetime.now() - function_start_time).total_seconds() * 1000

        log_with_context('error',
                         f"Unexpected error in handle_agentcore_chat: {str(e)}",
                         request_id=request_id,
                         session_id=session_id if 'session_id' in locals() else None,
                         error_type=type(e).__name__,
                         total_duration_ms=round(total_duration_ms, 2),
                         traceback=traceback.format_exc()
                         )

        return create_error_response(500, "Internal server error", "CHAT_HANDLER_ERROR")


def handle_agentcore_health(event: Dict[str, Any], request_id: str) -> Dict[str, Any]:
    """
    Handle GET /agentcore/health - Check AgentCore runtime health.

    Performs a health check by attempting a simple invocation of the AgentCore runtime.
    """
    health_start_time = datetime.now()

    log_with_context('info', "Starting AgentCore health check",
                     request_id=request_id)

    try:
        # Get AgentCore runtime ARN from SSM parameter
        try:
            agentcore_endpoint_parameter = os.environ.get(
                'AGENTCORE_ENDPOINT_PARAMETER', '/healthcare/agentcore/endpoint-url')

            log_with_context('debug',
                             f"Retrieving AgentCore ARN for health check from: {agentcore_endpoint_parameter}",
                             request_id=request_id
                             )

            ssm_start_time = datetime.now()
            response = ssm_client.get_parameter(
                Name=agentcore_endpoint_parameter)
            ssm_duration = (datetime.now() -
                            ssm_start_time).total_seconds() * 1000

            runtime_arn = response['Parameter']['Value']

            log_with_context('info',
                             f"Retrieved AgentCore ARN for health check",
                             request_id=request_id,
                             agentcore_arn=runtime_arn,
                             ssm_duration_ms=round(ssm_duration, 2)
                             )

        except Exception as ssm_error:
            log_with_context('error',
                             f"Health check failed - cannot retrieve AgentCore ARN: {str(ssm_error)}",
                             request_id=request_id,
                             error_type=type(ssm_error).__name__,
                             ssm_parameter=agentcore_endpoint_parameter
                             )

            return create_response(503, {
                'status': 'unhealthy',
                'error': 'AgentCore runtime not configured',
                'error_details': str(ssm_error),
                'timestamp': get_current_timestamp().isoformat(),
                'request_id': request_id
            })

        # Perform health check with a simple test message
        try:
            test_payload = json.dumps({
                "prompt": "health check"
            }).encode('utf-8')

            # Generate a session ID with minimum 33 characters as required by AgentCore
            health_session_id = f'agentcore_health_check_{uuid.uuid4().hex}'

            log_with_context('debug',
                             f"Performing health check invocation",
                             request_id=request_id,
                             health_session_id=health_session_id,
                             agentcore_arn=runtime_arn,
                             payload_size=len(test_payload)
                             )

            agentcore_start_time = datetime.now()

            response = bedrock_agentcore.invoke_agent_runtime(
                agentRuntimeArn=runtime_arn,
                runtimeSessionId=health_session_id,
                payload=test_payload
            )

            agentcore_end_time = datetime.now()
            agentcore_response_time_ms = (
                agentcore_end_time - agentcore_start_time).total_seconds() * 1000
            total_health_check_time_ms = (
                agentcore_end_time - health_start_time).total_seconds() * 1000

            # Try to read and validate the response
            try:
                response_body = response['response'].read()
                response_data = json.loads(response_body.decode('utf-8'))

                log_with_context('info',
                                 f"Health check completed successfully",
                                 request_id=request_id,
                                 health_session_id=health_session_id,
                                 agentcore_arn=runtime_arn,
                                 agentcore_duration_ms=round(
                                     agentcore_response_time_ms, 2),
                                 total_duration_ms=round(
                                     total_health_check_time_ms, 2),
                                 response_size=len(response_body)
                                 )

            except Exception as response_error:
                log_with_context('warning',
                                 f"Health check invocation succeeded but response parsing failed: {str(response_error)}",
                                 request_id=request_id,
                                 health_session_id=health_session_id,
                                 agentcore_duration_ms=round(
                                     agentcore_response_time_ms, 2)
                                 )

            # If we get here, the runtime is healthy
            health_data = {
                'status': 'healthy',
                'runtime_arn': runtime_arn,
                'agentcore_response_time_ms': round(agentcore_response_time_ms, 2),
                'total_health_check_time_ms': round(total_health_check_time_ms, 2),
                'timestamp': get_current_timestamp().isoformat(),
                'request_id': request_id,
                'health_session_id': health_session_id
            }

            return create_response(200, health_data)

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))

            agentcore_duration_ms = (datetime.now() - agentcore_start_time).total_seconds(
            ) * 1000 if 'agentcore_start_time' in locals() else 0
            total_duration_ms = (
                datetime.now() - health_start_time).total_seconds() * 1000

            log_with_context('error',
                             f"AgentCore health check failed: {error_code} - {error_message}",
                             request_id=request_id,
                             health_session_id=health_session_id if 'health_session_id' in locals() else None,
                             agentcore_arn=runtime_arn,
                             error_code=error_code,
                             agentcore_duration_ms=round(
                                 agentcore_duration_ms, 2),
                             total_duration_ms=round(total_duration_ms, 2),
                             aws_error_details=e.response.get('Error', {})
                             )

            return create_response(503, {
                'status': 'unhealthy',
                'error': f'AgentCore runtime error: {error_code}',
                'error_message': error_message,
                'error_code': error_code,
                'runtime_arn': runtime_arn,
                'agentcore_duration_ms': round(agentcore_duration_ms, 2),
                'total_duration_ms': round(total_duration_ms, 2),
                'timestamp': get_current_timestamp().isoformat(),
                'request_id': request_id
            })

        except Exception as e:
            agentcore_duration_ms = (datetime.now() - agentcore_start_time).total_seconds(
            ) * 1000 if 'agentcore_start_time' in locals() else 0
            total_duration_ms = (
                datetime.now() - health_start_time).total_seconds() * 1000

            log_with_context('error',
                             f"Unexpected error during AgentCore health check: {str(e)}",
                             request_id=request_id,
                             health_session_id=health_session_id if 'health_session_id' in locals() else None,
                             agentcore_arn=runtime_arn,
                             error_type=type(e).__name__,
                             agentcore_duration_ms=round(
                                 agentcore_duration_ms, 2),
                             total_duration_ms=round(total_duration_ms, 2),
                             traceback=traceback.format_exc()
                             )

            return create_response(503, {
                'status': 'unhealthy',
                'error': 'Unexpected error during health check',
                'error_message': str(e),
                'error_type': type(e).__name__,
                'runtime_arn': runtime_arn,
                'agentcore_duration_ms': round(agentcore_duration_ms, 2),
                'total_duration_ms': round(total_duration_ms, 2),
                'timestamp': get_current_timestamp().isoformat(),
                'request_id': request_id
            })

    except Exception as e:
        total_duration_ms = (
            datetime.now() - health_start_time).total_seconds() * 1000

        log_with_context('error',
                         f"Unexpected error in handle_agentcore_health: {str(e)}",
                         request_id=request_id,
                         error_type=type(e).__name__,
                         total_duration_ms=round(total_duration_ms, 2),
                         traceback=traceback.format_exc()
                         )

        return create_response(503, {
            'status': 'unhealthy',
            'error': 'Health check failed',
            'error_message': str(e),
            'error_type': type(e).__name__,
            'total_duration_ms': round(total_duration_ms, 2),
            'timestamp': get_current_timestamp().isoformat(),
            'request_id': request_id
        })
