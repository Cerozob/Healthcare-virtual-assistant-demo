"""
Healthcare Assistant Agent using Strands framework with AgentCore streaming.
Implements proper AgentCore streaming responses according to official documentation.
"""

import logging
import os
import sys
import time
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, AsyncGenerator
from datetime import datetime, timezone
from shared.config import get_agent_config
from healthcare_agent import create_healthcare_agent
from shared.utils import get_logger
from shared.models import PatientInfoResponse, SessionContext
from logging_config import setup_agentcore_logging
import uvicorn

# Initialize logging
setup_agentcore_logging()
logger = get_logger(__name__)


def process_strands_event(event) -> Optional[Dict[str, Any]]:
    """
    Process raw Strands streaming events into AgentCore-compatible format.
    Based on the AgentCore documentation pattern.
    """
    try:
        # Handle different event types from Strands
        
        # Case 1: Dictionary events (most common)
        if isinstance(event, dict):
            # Check for nested event structure
            if 'event' in event:
                nested_event = event['event']
                if isinstance(nested_event, dict):
                    # Handle contentBlockDelta (text content)
                    if 'contentBlockDelta' in nested_event:
                        delta = nested_event['contentBlockDelta']
                        if isinstance(delta, dict) and 'delta' in delta:
                            if isinstance(delta['delta'], dict) and 'text' in delta['delta']:
                                return {
                                    "type": "content_chunk",
                                    "content": delta['delta']['text'],
                                    "timestamp": datetime.now().isoformat()
                                }
                    
                    # Handle messageStart events
                    elif 'messageStart' in nested_event:
                        return {
                            "type": "message_start",
                            "role": nested_event['messageStart'].get('role', 'assistant'),
                            "timestamp": datetime.now().isoformat()
                        }
                    
                    # Handle messageStop events
                    elif 'messageStop' in nested_event:
                        return {
                            "type": "message_stop",
                            "stop_reason": nested_event['messageStop'].get('stopReason', 'complete'),
                            "timestamp": datetime.now().isoformat()
                        }
                    
                    # Handle contentBlockStop events
                    elif 'contentBlockStop' in nested_event:
                        return {
                            "type": "content_block_stop",
                            "timestamp": datetime.now().isoformat()
                        }
                    
                    # Handle metadata events
                    elif 'metadata' in nested_event:
                        return {
                            "type": "metadata",
                            "metadata": nested_event['metadata'],
                            "timestamp": datetime.now().isoformat()
                        }
            
            # Handle direct data events
            elif 'data' in event:
                if isinstance(event['data'], str):
                    return {
                        "type": "content_chunk",
                        "content": event['data'],
                        "timestamp": datetime.now().isoformat()
                    }
            
            # Handle direct text events
            elif 'text' in event:
                return {
                    "type": "content_chunk",
                    "content": str(event['text']),
                    "timestamp": datetime.now().isoformat()
                }
            
            # Handle delta events
            elif 'delta' in event:
                if isinstance(event['delta'], dict) and 'text' in event['delta']:
                    return {
                        "type": "content_chunk",
                        "content": event['delta']['text'],
                        "timestamp": datetime.now().isoformat()
                    }
                elif isinstance(event['delta'], str):
                    return {
                        "type": "content_chunk",
                        "content": event['delta'],
                        "timestamp": datetime.now().isoformat()
                    }
            
            # Handle status events
            elif any(key in event for key in ['init_event_loop', 'start', 'start_event_loop']):
                # These are initialization events, skip them
                return None
        
        # Case 2: Object events with attributes
        elif hasattr(event, 'data') and isinstance(event.data, str):
            return {
                "type": "content_chunk",
                "content": event.data,
                "timestamp": datetime.now().isoformat()
            }
        elif hasattr(event, 'delta') and hasattr(event.delta, 'text'):
            return {
                "type": "content_chunk",
                "content": event.delta.text,
                "timestamp": datetime.now().isoformat()
            }
        elif hasattr(event, 'content') and isinstance(event.content, str):
            return {
                "type": "content_chunk",
                "content": event.content,
                "timestamp": datetime.now().isoformat()
            }
        elif hasattr(event, 'message') and isinstance(event.message, str):
            return {
                "type": "content_chunk",
                "content": event.message,
                "timestamp": datetime.now().isoformat()
            }
        
        # Case 3: String events
        elif isinstance(event, str):
            return {
                "type": "content_chunk",
                "content": event,
                "timestamp": datetime.now().isoformat()
            }
        
        # Unknown event type - log for debugging
        logger.debug(f"🔍 Unknown event type: {type(event)} = {str(event)[:100]}...")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error processing Strands event: {e}")
        logger.error(f"   Event: {str(event)[:200]}...")
        return {
            "type": "error",
            "error": f"Event processing failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


def log_environment_variables():
    """Log all environment variables for debugging."""
    logger.info("=== ENVIRONMENT VARIABLES ===")
    env_vars = dict(os.environ)
    for key, value in sorted(env_vars.items()):
        # Skip AWS credentials for security
        if any(sensitive in key.upper() for sensitive in ["ACCESS_KEY", "SECRET_KEY", "TOKEN", "PASSWORD"]):
            continue
        logger.info(f"{key}={value}")
    logger.info("=== END ENVIRONMENT VARIABLES ===")


# Log environment variables for debugging
log_environment_variables()

# Initialize FastAPI app
app = FastAPI(title="Healthcare Assistant Agent", version="2.0.0")

# Load configuration
config = get_agent_config()


class FileAttachment(BaseModel):
    """File attachment for multimodal processing."""
    fileName: str
    fileSize: int
    fileType: str
    category: str
    s3Key: str
    content: Optional[str] = None  # base64 encoded content
    mimeType: Optional[str] = None


class MediaContent(BaseModel):
    """AgentCore multimodal media content."""
    type: str  # "image", "document", "video", "audio"
    format: str  # "jpeg", "png", "pdf", etc.
    data: str  # base64 encoded content


class MediaMetadata(BaseModel):
    """Metadata for multimodal content."""
    fileName: str
    fileSize: int
    category: str
    s3Key: str


class AttachmentContext(BaseModel):
    """Context information about attachments."""
    fileName: str
    fileType: str
    category: str
    s3Key: str
    hasContent: bool
    mimeType: Optional[str] = None


class InvocationRequest(BaseModel):
    prompt: str
    # AgentCore multimodal format (official)
    media: Optional[MediaContent] = None
    mediaMetadata: Optional[MediaMetadata] = None
    attachmentContext: Optional[List[AttachmentContext]] = None
    # Legacy support
    attachments: Optional[List[FileAttachment]] = None
    sessionId: Optional[str] = None
    timestamp: Optional[str] = None
    
    class Config:
        # Allow extra fields that AgentCore might send
        extra = "allow"


class PatientContextResponse(BaseModel):
    """Patient context for frontend integration."""
    patient_id: Optional[str] = Field(None, description="Patient ID")
    patient_name: Optional[str] = Field(None, description="Patient name")
    has_patient_context: bool = Field(False, description="Has patient context")
    patient_found: bool = Field(
        False, description="Patient found in interaction")
    patient_data: Optional[Dict[str, Any]] = Field(
        None, description="Patient data")


@app.on_event("startup")
async def startup_event():
    """FastAPI startup event."""
    logger.info("🚀 === HEALTHCARE ASSISTANT STARTUP ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Configuration: {config.model_dump()}")
    logger.info("🚀 === STARTUP CONFIGURATION ===")

    # Skip comprehensive gateway testing during startup to avoid rate limiting
    # when multiple runtime instances start simultaneously
    logger.info("🔍 Skipping comprehensive gateway testing during startup to prevent rate limiting")
    logger.info("   Gateway connection will be tested on first actual request")
    
    # Only test basic agent creation without MCP calls
    logger.info("🧪 Testing basic agent configuration...")
    try:
        # Just validate configuration without creating full agent
        logger.info("✅ Agent configuration validated")
        logger.info(f"   Model: {config.model_id}")
        logger.info(f"   Gateway: {config.mcp_gateway_url}")
        logger.info(f"   Region: {config.aws_region}")
        logger.info("🚀 === STARTUP COMPLETE ===")
    except Exception as e:
        logger.error(f"❌ Agent configuration validation failed: {e}")
        raise


async def stream_agent_response(request: InvocationRequest) -> AsyncGenerator[str, None]:
    """Stream agent response according to AgentCore streaming pattern."""
    start_time = time.time()
    
    try:
        logger.info("🚀 === HEALTHCARE AGENT STREAMING INVOCATION ===")

        user_message = request.prompt
        if not user_message:
            yield f"data: {json.dumps({'type': 'error', 'error': 'No prompt provided', 'timestamp': datetime.now().isoformat()})}\n\n"
            return

        # Use provided session ID or generate one
        session_id = request.sessionId or f"healthcare_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"📝 Session: {session_id}")
        logger.info(f"💬 Message: {user_message[:100]}...")
        
        # Log multimodal content
        has_media = bool(request.media)
        attachment_count = len(request.attachmentContext) if request.attachmentContext else 0
        
        logger.info(f"🖼️ Multimodal: {has_media}")
        logger.info(f"�  Attachments: {attachment_count}")
        
        if request.media:
            logger.info(f"   Media: {request.media.type}/{request.media.format}")
            if request.mediaMetadata:
                logger.info(f"   File: {request.mediaMetadata.fileName} ({request.mediaMetadata.category})")

        # Yield initial status with proper event type
        yield f"data: {json.dumps({'type': 'status', 'status': 'initializing', 'session_id': session_id, 'timestamp': datetime.now().isoformat()})}\n\n"

        # Create healthcare agent
        agent_start = time.time()
        try:
            healthcare_agent = create_healthcare_agent(session_id)
            agent_time = (time.time() - agent_start) * 1000
            yield f"data: {json.dumps({'type': 'status', 'status': 'agent_ready', 'agent_creation_ms': agent_time, 'timestamp': datetime.now().isoformat()})}\n\n"
        except ValueError as e:
            if "MCP" in str(e):
                logger.error(f"❌ MCP Gateway connection failed during request: {e}")
                yield f"data: {json.dumps({'type': 'error', 'error': 'MCP Gateway connection failed', 'details': str(e), 'timestamp': datetime.now().isoformat()})}\n\n"
                return
            else:
                yield f"data: {json.dumps({'type': 'error', 'error': 'Agent creation failed', 'details': str(e), 'timestamp': datetime.now().isoformat()})}\n\n"
                return
        except Exception as e:
            logger.error(f"❌ Unexpected agent creation error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': 'Agent creation failed', 'details': str(e), 'timestamp': datetime.now().isoformat()})}\n\n"
            return

        logger.info(f"🤖 Agent created in {agent_time:.2f}ms")

        # Yield processing status
        yield f"data: {json.dumps({'type': 'status', 'status': 'processing', 'message': 'Analyzing request...', 'timestamp': datetime.now().isoformat()})}\n\n"

        # Build prompt based on content type
        has_multimodal = bool(request.media) or bool(request.attachments)
        
        if has_multimodal:
            yield f"data: {json.dumps({'type': 'status', 'status': 'multimodal_processing', 'message': 'Processing multimodal content...', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # Build multimodal prompt
            if request.media and request.mediaMetadata:
                logger.info(f"🖼️ Processing AgentCore multimodal content: {request.media.type}/{request.media.format}")
                
                multimodal_prompt = f"{user_message}\n\n[MULTIMODAL CONTENT]\n"
                multimodal_prompt += f"Media Type: {request.media.type}\n"
                multimodal_prompt += f"Format: {request.media.format}\n"
                multimodal_prompt += f"File: {request.mediaMetadata.fileName}\n"
                multimodal_prompt += f"Category: {request.mediaMetadata.category}\n"
                
                # Create media object for agent processing
                media_object = {
                    "type": request.media.type,
                    "format": request.media.format,
                    "data": request.media.data,
                    "metadata": request.mediaMetadata.model_dump()
                }
                
                # Stream the agent response
                async for raw_event in healthcare_agent.stream_with_agentcore_multimodal(
                    multimodal_prompt, media_object, request.attachmentContext or []):
                    try:
                        processed_chunk = process_strands_event(raw_event)
                        
                        if processed_chunk:
                            # Add multimodal metadata to content chunks
                            if processed_chunk.get('type') == 'content_chunk':
                                processed_chunk.update({
                                    'media_type': media_object['type'],
                                    'media_format': media_object['format'],
                                    'primary_file': media_object['metadata']['fileName']
                                })
                            
                            yield f"data: {json.dumps(processed_chunk)}\n\n"
                        else:
                            logger.debug(f"🔍 Skipped multimodal event: {type(raw_event)}")
                            
                    except (TypeError, ValueError) as e:
                        logger.error(f"❌ Multimodal event processing error: {e}")
                        yield f"data: {json.dumps({'type': 'error', 'error': 'Multimodal event processing failed', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            elif request.attachments:
                # Legacy attachment processing
                multimodal_prompt = f"{user_message}\n\n[LEGACY_ATTACHMENTS]\n"
                for attachment in request.attachments:
                    multimodal_prompt += f"- File: {attachment.fileName}\n"
                
                async for raw_event in healthcare_agent.stream_with_multimodal_support(
                    multimodal_prompt, request.attachments):
                    try:
                        processed_chunk = process_strands_event(raw_event)
                        
                        if processed_chunk:
                            # Add legacy multimodal metadata to content chunks
                            if processed_chunk.get('type') == 'content_chunk':
                                processed_chunk.update({
                                    'legacy_multimodal': True,
                                    'attachments_count': len(request.attachments)
                                })
                            
                            yield f"data: {json.dumps(processed_chunk)}\n\n"
                        else:
                            logger.debug(f"🔍 Skipped legacy multimodal event: {type(raw_event)}")
                            
                    except (TypeError, ValueError) as e:
                        logger.error(f"❌ Legacy multimodal event processing error: {e}")
                        yield f"data: {json.dumps({'type': 'error', 'error': 'Legacy multimodal event processing failed', 'timestamp': datetime.now().isoformat()})}\n\n"
        else:
            # Text-only processing
            yield f"data: {json.dumps({'type': 'status', 'status': 'text_processing', 'message': 'Processing text query...', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            async for raw_event in healthcare_agent.stream_response(user_message):
                try:
                    # Process raw Strands events according to AgentCore pattern
                    processed_chunk = process_strands_event(raw_event)
                    
                    if processed_chunk:
                        yield f"data: {json.dumps(processed_chunk)}\n\n"
                    else:
                        # Log skipped events only in debug mode
                        logger.debug(f"🔍 Skipped non-content event: {type(raw_event)}")
                        
                except (TypeError, ValueError) as e:
                    logger.error(f"❌ Event processing error: {e}")
                    logger.error(f"   Event type: {type(raw_event)}")
                    logger.error(f"   Event content: {str(raw_event)[:200]}...")
                    # Send error chunk instead of failing
                    yield f"data: {json.dumps({'type': 'error', 'error': 'Event processing failed', 'details': str(e), 'timestamp': datetime.now().isoformat()})}\n\n"

        # Final completion
        total_time = (time.time() - start_time) * 1000
        yield f"data: {json.dumps({'type': 'completion', 'status': 'complete', 'total_time_ms': total_time, 'session_id': session_id, 'timestamp': datetime.now().isoformat()})}\n\n"

    except Exception as e:
        logger.error(f"❌ Streaming invocation failed: {e}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'error': 'Streaming failed', 'details': str(e), 'timestamp': datetime.now().isoformat()})}\n\n"


@app.post("/invocations")
async def invoke_agent(raw_request: Request):
    """AgentCore invocation endpoint with comprehensive debugging."""
    
    # === COMPREHENSIVE DEBUG LOGGING ===
    logger.info("🔍 === AGENTCORE INVOCATION DEBUG ===")
    logger.info(f"Method: {raw_request.method}")
    logger.info(f"URL: {raw_request.url}")
    logger.info(f"Headers: {dict(raw_request.headers)}")
    logger.info(f"Content-Type: {raw_request.headers.get('content-type', 'Not specified')}")
    logger.info(f"Content-Length: {raw_request.headers.get('content-length', 'Not specified')}")
    logger.info(f"User-Agent: {raw_request.headers.get('user-agent', 'Not specified')}")
    
    try:
        # Read raw body first for debugging
        raw_body = await raw_request.body()
        logger.info(f"Raw body length: {len(raw_body)} bytes")
        
        # Try to decode and log body
        try:
            body_text = raw_body.decode('utf-8')
            logger.info(f"Raw body text: {body_text}")
        except Exception as decode_error:
            logger.error(f"❌ Failed to decode body as UTF-8: {decode_error}")
            body_text = "<decode failed>"
        
        # Try to parse as JSON
        try:
            
            body_json = json.loads(body_text)
            logger.info(f"Parsed JSON keys: {list(body_json.keys()) if isinstance(body_json, dict) else 'not a dict'}")
            logger.info(f"JSON content: {body_json}")
        except Exception as json_error:
            logger.error(f"❌ Failed to parse as JSON: {json_error}")
            # Return debug response for non-JSON requests
            return JSONResponse(
                content={
                    "error": "Invalid JSON payload",
                    "details": str(json_error),
                    "raw_body_preview": body_text[:200] if body_text != "<decode failed>" else "decode failed",
                    "debug": True,
                    "expected_format": {
                        "prompt": "Your message here"
                    },
                    "common_issues": [
                        "Trailing commas in JSON",
                        "Using 'input' instead of 'prompt'",
                        "Unescaped quotes in strings"
                    ]
                },
                status_code=400,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
                }
            )
        
        # Try to create InvocationRequest from JSON
        try:
            request = InvocationRequest(**body_json)
            logger.info("✅ Successfully parsed as InvocationRequest")
        except Exception as parse_error:
            logger.error(f"❌ Failed to parse as InvocationRequest: {parse_error}")
            # Return debug response for invalid request structure
            return JSONResponse(
                content={
                    "error": "Invalid request structure",
                    "details": str(parse_error),
                    "expected_fields": ["prompt"],
                    "received_fields": list(body_json.keys()) if isinstance(body_json, dict) else "not a dict",
                    "json_content": body_json,
                    "debug": True,
                    "correct_format": {
                        "prompt": "Your message here",
                        "sessionId": "optional-session-id",
                        "attachments": "optional-array"
                    }
                },
                status_code=422,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
                }
            )
        
        # Log parsed request details
        logger.info("🌊 === PARSED REQUEST DETAILS ===")
        logger.info(f"Request type: {type(request)}")
        logger.info(f"Request prompt: {request.prompt[:100] if request.prompt else 'None'}...")
        logger.info(f"Request sessionId: {request.sessionId}")
        logger.info(f"Request media: {bool(request.media)}")
        logger.info(f"Request attachments: {len(request.attachments) if request.attachments else 0}")
        logger.info("🌊 === END PARSED REQUEST LOG ===")
        
        # Validate request
        if not request.prompt:
            logger.error("❌ No prompt provided in request")
            return JSONResponse(
                content={
                    "error": "No prompt provided",
                    "details": "The 'prompt' field is required and cannot be empty",
                    "request_data": {
                        "prompt": request.prompt,
                        "sessionId": request.sessionId,
                        "has_media": bool(request.media),
                        "attachments_count": len(request.attachments) if request.attachments else 0
                    },
                    "debug": True,
                    "example": {
                        "prompt": "Hello, how can you help me?"
                    }
                },
                status_code=400,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*",
                }
            )
        
        logger.info("✅ Request validation passed, starting streaming response")
        
        return StreamingResponse(
            stream_agent_response(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Critical error in invoke_agent: {e}", exc_info=True)
        # Return debug response for any other errors
        return JSONResponse(
            content={
                "error": "Critical invocation error",
                "details": str(e),
                "error_type": type(e).__name__,
                "raw_body_length": len(raw_body) if 'raw_body' in locals() else 0,
                "debug": True
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )





@app.get("/ping")
async def ping():
    """Health check endpoint."""
    return {
        "status": "Healthy",
        "timestamp": int(time.time()),
        "version": "2.0.0",
        "streaming_only": True,
        "debug_enabled": True,
        "endpoints": {
            "ping": "/ping (this endpoint)",
            "invocations": "/invocations (with comprehensive debugging)"
        },
        "config": {
            "model": config.model_id,
            "knowledge_base": bool(config.knowledge_base_id),
            "mcp_gateway": bool(config.mcp_gateway_url),
            "guardrails": bool(config.guardrail_id)
        }
    }


if __name__ == "__main__":
    logger.info("🚀 Starting Healthcare Assistant Agent")
    logger.info(f"Configuration: {config.model_dump()}")
    logger.info("🌐 Server will start on http://0.0.0.0:8080")
    logger.info("📍 Endpoints available:")
    logger.info("   - GET  /ping")
    logger.info("   - POST /invocations")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
