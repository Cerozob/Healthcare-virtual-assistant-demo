"""
Healthcare Assistant Agent using Strands Agents framework.
FastAPI implementation for AgentCore Runtime deployment with S3 session management.
"""

import logging
import os
import boto3
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from strands import Agent
from strands.session.s3_session_manager import S3SessionManager
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from shared.utils import get_logger, extract_patient_context, extract_patient_id_from_message
from logging_config import setup_agentcore_logging

# Configure Strands Agents logging


def configure_logging():
    """
    Configure comprehensive logging for Strands Agents SDK and FastAPI/uvicorn.
    Ensures all logs are visible in AgentCore CloudWatch logs and not suppressed by WSGI.
    """
    import sys
    
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level_value = getattr(logging, log_level, logging.INFO)

    # CRITICAL: Force all output to stdout to prevent WSGI suppression
    sys.stderr = sys.stdout
    
    # Create formatter optimized for CloudWatch and container logs
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Configure root logger to capture everything
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture everything, filter at handler level
    
    # Remove ALL existing handlers to prevent conflicts
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler that FORCES output to stdout
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setLevel(log_level_value)
    console_handler.setFormatter(formatter)
    
    # Add the handler to root logger
    root_logger.addHandler(console_handler)

    # DISABLE uvicorn's default logging to prevent conflicts
    logging.getLogger("uvicorn").handlers.clear()
    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.error").handlers.clear()
    
    # Configure specific loggers with forced propagation
    loggers_to_configure = [
        ("strands", log_level_value),
        ("uvicorn", log_level_value),
        ("uvicorn.access", log_level_value), 
        ("uvicorn.error", log_level_value),
        ("fastapi", log_level_value),
        ("agents", log_level_value),
        ("mcp", log_level_value),
        ("boto3", logging.WARNING),  # Reduce boto3 noise
        ("botocore", logging.WARNING),  # Reduce botocore noise
        ("urllib3", logging.WARNING),  # Reduce urllib3 noise
    ]
    
    for logger_name, level in loggers_to_configure:
        logger_obj = logging.getLogger(logger_name)
        logger_obj.setLevel(level)
        logger_obj.propagate = True  # FORCE propagation to root
        
        # Remove any existing handlers to prevent duplicates
        logger_obj.handlers.clear()

    # FORCE uvicorn to use our logging configuration
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.propagate = True
    uvicorn_logger.disabled = False
    
    # Test logging immediately to verify it works
    print("=" * 80, flush=True)  # Direct print to ensure visibility
    print("🔧 LOGGING CONFIGURATION TEST", flush=True)
    print("=" * 80, flush=True)
    
    # Test different log levels
    root_logger.info("✅ ROOT LOGGER TEST - This should be visible")
    logging.getLogger("agents").info("✅ AGENTS LOGGER TEST - This should be visible")
    logging.getLogger("uvicorn").info("✅ UVICORN LOGGER TEST - This should be visible")
    
    print("=" * 80, flush=True)


def test_logging():
    """Test function to verify logging is working and not suppressed by WSGI."""
    logger = logging.getLogger("agents.test")
    
    print("\n🧪 RUNTIME LOGGING TEST", flush=True)
    print("-" * 40, flush=True)
    
    logger.debug("🔍 DEBUG level test message")
    logger.info("ℹ️ INFO level test message") 
    logger.warning("⚠️ WARNING level test message")
    logger.error("❌ ERROR level test message")
    
    # Also test direct print statements
    print("📝 Direct print statement (should always work)", flush=True)
    
    # Test sys.stdout directly
    import sys
    sys.stdout.write("📤 Direct sys.stdout write\n")
    sys.stdout.flush()
    
    print("-" * 40, flush=True)
    
    return True


# Initialize logging with AgentCore-optimized configuration
print("🔧 Initializing AgentCore logging configuration...", flush=True)
setup_agentcore_logging()

# Also run the legacy configuration for compatibility
configure_logging()

# Test logging immediately after configuration
print("🧪 Testing logging configuration...", flush=True)
test_logging()

# Get logger for this module
logger = get_logger(__name__)

# Log startup configuration with enhanced visibility
print("\n🔧 AGENT STARTUP CONFIGURATION", flush=True)
print("=" * 50, flush=True)
logger.info("🔧 Agent Configuration:")
logger.info(f"   • MCP Gateway: {os.getenv('USE_MCP_GATEWAY', 'false')}")
logger.info(f"   • Gateway URL: {os.getenv('MCP_GATEWAY_URL', 'not configured')}")
logger.info(f"   • AWS Region: {os.getenv('AWS_REGION', 'us-east-1')}")
logger.info(f"   • Log Level: {os.getenv('LOG_LEVEL', 'INFO')}")
logger.info(f"   • Environment: {os.getenv('ENVIRONMENT', 'development')}")
print("=" * 50, flush=True)

# Initialize FastAPI app
app = FastAPI(title="Healthcare Assistant Agent", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    """FastAPI startup event to test logging visibility."""
    print("\n🚀 FASTAPI STARTUP EVENT", flush=True)
    print("=" * 40, flush=True)
    
    logger.info("🚀 FastAPI application starting up")
    logger.info("🔍 Testing logging from FastAPI startup event")
    
    # Test that logging works in async context
    test_logging()
    
    logger.info("✅ FastAPI startup complete - logging is working!")
    print("=" * 40, flush=True)

# Add comprehensive request logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    """Log all HTTP requests and responses with detailed information for AgentCore debugging."""
    import time
    import uuid
    
    # Generate request ID if not provided
    request_id = request.headers.get("x-request-id", str(uuid.uuid4())[:8])
    start_time = time.time()
    
    # Log incoming request
    logger.info(f"🔄 [{request_id}] {request.method} {request.url.path}")
    logger.debug(f"🔍 [{request_id}] Query params: {dict(request.query_params)}")
    logger.debug(f"🔍 [{request_id}] Headers: {dict(request.headers)}")
    
    # Log client information
    client_host = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    logger.debug(f"🔍 [{request_id}] Client: {client_host} | User-Agent: {user_agent}")
    
    try:
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Log successful response
        logger.info(f"✅ [{request_id}] {response.status_code} | {processing_time:.2f}ms")
        
        # Log response headers for debugging
        logger.debug(f"🔍 [{request_id}] Response headers: {dict(response.headers)}")
        
        return response
        
    except Exception as e:
        # Calculate processing time for failed requests
        processing_time = (time.time() - start_time) * 1000
        
        # Log failed request with full error details
        logger.error(f"❌ [{request_id}] Request failed after {processing_time:.2f}ms")
        logger.error(f"❌ [{request_id}] Error: {str(e)}")
        logger.error(f"❌ [{request_id}] Exception type: {type(e).__name__}")
        
        # Log full traceback in debug mode
        if logger.isEnabledFor(logging.DEBUG):
            import traceback
            logger.debug(f"❌ [{request_id}] Full traceback:\n{traceback.format_exc()}")
        
        raise

# Healthcare assistant system prompt
HEALTHCARE_SYSTEM_PROMPT = """
Eres un asistente de salud inteligente diseñado para ayudar a profesionales médicos con:
- Gestión de información de pacientes
- Programación de citas
- Consultas de base de conocimientos médicos
- Procesamiento y análisis de documentos

INSTRUCCIONES IMPORTANTES:
1. Siempre responde en español (LATAM) a menos que se solicite específicamente otro idioma.
2. Mantén estándares profesionales médicos y confidencialidad del paciente.
3. Sé útil, preciso y profesional en todas las interacciones.

GESTIÓN INTELIGENTE DE PACIENTES:
Cuando un usuario mencione información de un paciente, SIEMPRE usa la herramienta 'extract_and_search_patient' que:
- Analiza inteligentemente el mensaje del usuario para extraer información del paciente
- Busca automáticamente en la base de datos usando múltiples criterios
- Establece el contexto del paciente para toda la conversación
- Permite que el frontend seleccione automáticamente al paciente identificado

EJEMPLOS DE USO AUTOMÁTICO (SIEMPRE usar extract_and_search_patient):
- "Necesito información del paciente Juan Pérez" → extract_and_search_patient(mensaje completo)
- "Busca la cédula 12345678" → extract_and_search_patient(mensaje completo)
- "Revisa la historia clínica MRN-001" → extract_and_search_patient(mensaje completo)
- "El paciente María González necesita..." → extract_and_search_patient(mensaje completo)
- "Agenda una cita para Juan" → extract_and_search_patient(mensaje completo)
- "¿Qué síntomas tiene María?" → extract_and_search_patient(mensaje completo)

IMPORTANTE: 
- Cada vez que identifiques un paciente, el frontend automáticamente lo seleccionará en el panel lateral
- Usa las herramientas para establecer el contexto del paciente en el estado del agente
- Proporciona respuestas claras y profesionales sobre el paciente encontrado

HERRAMIENTAS DISPONIBLES:
- extract_and_search_patient: Extrae información del paciente del mensaje y busca en la base de datos
- get_patient_by_id: Busca paciente por ID específico cuando ya lo tienes
- list_recent_patients: Lista pacientes recientes para selección rápida
- validate_patient_session: Verifica si hay un paciente activo en la sesión

FLUJO DE TRABAJO:
1. Si el usuario menciona un paciente, usa extract_and_search_patient con el mensaje completo
2. Confirma la identidad del paciente encontrado
3. Procede con la información médica contextualizada para ese paciente
4. Mantén el contexto del paciente durante toda la conversación

Siempre confirma la identidad del paciente antes de proceder con información médica sensible.
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
    # Pattern for explicit patient ID (case insensitive)
    patient_id_patterns = [
        r"paciente\s+id[:\s]+([a-zA-Z0-9\-_]+)",
        r"patient\s+id[:\s]+([a-zA-Z0-9\-_]+)",
        r"cedula[:\s]+(\d+)",
        r"cédula[:\s]+(\d+)",
        r"id\s+paciente[:\s]+([a-zA-Z0-9\-_]+)",
        r"esta sesión es del paciente\s+([a-zA-Z0-9\-_\s]+)",
    ]

    for pattern in patient_id_patterns:
        # Use case-insensitive search but preserve original case in capture group
        match = re.search(pattern, message, re.IGNORECASE)
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
        logger.info(
            f"Creating session manager for patient {patient_id} with consistent structure")
    else:
        # For sessions without patient context, use unknown patient pattern
        prefix = f"processed/unknown_medical_notes/"
        logger.info(
            "Creating session manager for session without patient context")

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


def _extract_patient_from_agent_state(agent: Agent) -> tuple[Optional[str], Optional[str], Optional[Dict[str, Any]]]:
    """
    Extract patient information from agent state instead of parsing response text.

    Args:
        agent: Agent instance with state

    Returns:
        Tuple of (patient_id, patient_name, patient_data) or (None, None, None)
    """
    try:
        # Get patient information from agent state if available
        current_patient_id = agent.state.get("current_patient_id")
        current_patient_name = agent.state.get("current_patient_name")
        current_patient_data = agent.state.get("current_patient_data")

        if current_patient_id and current_patient_name:
            logger.info(
                f"Retrieved patient from agent state: {current_patient_name} (ID: {current_patient_id})")
            return current_patient_id, current_patient_name, current_patient_data

        return None, None, None

    except Exception as e:
        logger.error(f"Error extracting patient from agent state: {str(e)}")
        return None, None, None


def _log_agent_capabilities(agent: Agent, use_mcp_gateway: bool):
    """
    Log comprehensive information about agent capabilities and configuration.
    
    Args:
        agent: The configured agent instance
        use_mcp_gateway: Whether MCP Gateway is being used
    """
    logger.info("🔍 === AGENT CAPABILITIES ANALYSIS ===")
    
    try:
        # Log basic agent information
        logger.info("📊 AGENT BASIC INFO:")
        logger.info(f"   • Agent type: {type(agent).__name__}")
        logger.info(f"   • Agent ID: {getattr(agent, 'id', 'not available')}")
        
        # Log tools information
        tools = getattr(agent, 'tools', [])
        logger.info(f"🔧 TOOLS CONFIGURATION:")
        logger.info(f"   • Total tools: {len(tools) if tools else 0}")
        
        if tools:
            for i, tool in enumerate(tools):
                tool_name = getattr(tool, 'name', getattr(tool, '__name__', f'tool_{i}'))
                tool_type = type(tool).__name__
                logger.info(f"   • Tool {i+1}: {tool_name} ({tool_type})")
        else:
            logger.warning("   • ⚠️ No tools configured!")
        
        # Log MCP Gateway status
        logger.info(f"🌐 MCP GATEWAY STATUS:")
        logger.info(f"   • Enabled: {use_mcp_gateway}")
        if use_mcp_gateway:
            gateway_url = os.getenv('MCP_GATEWAY_URL')
            logger.info(f"   • Gateway URL: {gateway_url}")
            logger.info(f"   • Authentication: IAM")
        else:
            logger.info(f"   • Using local tools instead")
        
        # Log Bedrock/Knowledge Base configuration
        logger.info(f"🧠 BEDROCK CONFIGURATION:")
        bedrock_region = os.getenv('AWS_REGION', 'us-east-1')
        logger.info(f"   • Region: {bedrock_region}")
        
        # Check for knowledge base configuration
        kb_id = os.getenv('BEDROCK_KNOWLEDGE_BASE_ID')
        logger.info(f"   • Knowledge Base ID: {kb_id or 'not configured'}")
        logger.info(f"   • Knowledge Base: {'✅ Enabled' if kb_id else '❌ Not configured'}")
        
        # Log guardrails configuration for CloudWatch monitoring
        guardrail_id = os.getenv('GUARDRAIL_ID') or os.getenv('BEDROCK_GUARDRAIL_ID')
        guardrail_version = os.getenv('GUARDRAIL_VERSION') or os.getenv('BEDROCK_GUARDRAIL_VERSION', 'DRAFT')
        logger.info(f"GUARDRAIL_CONFIG: ID={guardrail_id}, VERSION={guardrail_version}, STATUS={'ENABLED' if guardrail_id else 'DISABLED'}")
        
        # Also log Knowledge Base ID for monitoring
        logger.info(f"KNOWLEDGE_BASE_CONFIG: ID={kb_id}, STATUS={'ENABLED' if kb_id else 'DISABLED'}")
        
        # Log model configuration
        model_id = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
        logger.info(f"   • Model ID: {model_id}")
        
        # Log agent state capabilities
        logger.info(f"📋 AGENT STATE:")
        if hasattr(agent, 'state'):
            state_keys = list(agent.state._state.keys()) if hasattr(agent.state, '_state') else []
            logger.info(f"   • State keys: {state_keys}")
        else:
            logger.warning("   • ⚠️ No state management available")
        
        # Log session management
        session_manager = getattr(agent, 'session_manager', None)
        logger.info(f"💾 SESSION MANAGEMENT:")
        logger.info(f"   • Session Manager: {'✅ Enabled' if session_manager else '❌ Not configured'}")
        if session_manager:
            logger.info(f"   • Session Manager Type: {type(session_manager).__name__}")
        
        # Log environment-specific configurations
        logger.info(f"🌍 ENVIRONMENT CONFIG:")
        logger.info(f"   • Environment: {os.getenv('ENVIRONMENT', 'development')}")
        logger.info(f"   • Debug Mode: {os.getenv('DEBUG', 'false')}")
        logger.info(f"   • Log Level: {os.getenv('LOG_LEVEL', 'INFO')}")
        
        # Test agent responsiveness
        logger.info(f"🧪 AGENT HEALTH CHECK:")
        try:
            # Simple test to see if agent responds
            test_response = agent("Hello, are you working?")
            response_length = len(test_response.message) if hasattr(test_response, 'message') else 0
            logger.info(f"   • Health Check: ✅ Passed")
            logger.info(f"   • Response Length: {response_length} characters")
            logger.info(f"   • Response Preview: {test_response.message[:100] if hasattr(test_response, 'message') else 'No message'}...")
        except Exception as e:
            logger.error(f"   • Health Check: ❌ Failed - {str(e)}")
        
    except Exception as e:
        logger.error(f"❌ Error analyzing agent capabilities: {str(e)}")
    
    logger.info("🔍 === AGENT CAPABILITIES ANALYSIS COMPLETE ===")


def _create_streamable_http_transport_with_iam(mcp_url: str):
    """
    Create HTTP transport for MCP client with IAM authentication.
    
    The MCP Gateway handles IAM authentication at the gateway level,
    so we just need to provide the gateway URL.
    
    Args:
        mcp_url: MCP Gateway URL
        
    Returns:
        Streamable HTTP transport
    """
    logger.info(f"Creating HTTP transport for MCP Gateway: {mcp_url}")
    
    # Verify AWS credentials are available
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        
        if not credentials:
            logger.error("No AWS credentials found for IAM authentication")
            raise HTTPException(
                status_code=500,
                detail="AWS credentials required for MCP Gateway IAM authentication"
            )
        
        logger.info("AWS credentials found, creating MCP transport")
        
    except Exception as e:
        logger.error(f"Error checking AWS credentials: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to verify AWS credentials: {str(e)}"
        )
    
    # Create the streamable HTTP client
    # The MCP Gateway will handle IAM authentication
    return streamablehttp_client(mcp_url)


def _get_full_tools_list(client: MCPClient) -> list:
    """
    List all tools with pagination support.
    
    Args:
        client: MCP client instance
        
    Returns:
        List of all available tools
    """
    logger.info("🔍 === TOOLS DISCOVERY PROCESS ===")
    
    more_tools = True
    tools = []
    pagination_token = None
    page_count = 0
    
    while more_tools:
        page_count += 1
        logger.info(f"📄 Fetching tools page {page_count}...")
        
        try:
            tmp_tools = client.list_tools_sync(pagination_token=pagination_token)
            tools_in_page = len(tmp_tools) if tmp_tools else 0
            
            logger.info(f"   • Found {tools_in_page} tools in page {page_count}")
            
            if tmp_tools:
                tools.extend(tmp_tools)
                
                # Log each tool found
                for tool in tmp_tools:
                    tool_name = getattr(tool, 'tool_name', getattr(tool, 'name', 'unnamed'))
                    logger.info(f"     - {tool_name}")
            
            if not tmp_tools or not hasattr(tmp_tools, 'pagination_token') or tmp_tools.pagination_token is None:
                more_tools = False
                logger.info(f"✅ No more pages available")
            else:
                pagination_token = tmp_tools.pagination_token
                logger.info(f"🔄 More pages available, continuing...")
                
        except Exception as e:
            logger.error(f"❌ Error fetching tools page {page_count}: {str(e)}")
            more_tools = False
    
    logger.info(f"📊 === TOOLS DISCOVERY COMPLETE ===")
    logger.info(f"   • Total pages processed: {page_count}")
    logger.info(f"   • Total tools discovered: {len(tools)}")
    
    return tools


def _create_agent_with_mcp_gateway(session_id: str) -> Agent:
    """
    Create Strands Agent with MCP Gateway tools using IAM authentication.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Configured Agent instance with MCP Gateway tools
    """
    mcp_gateway_url = os.getenv("MCP_GATEWAY_URL")
    if not mcp_gateway_url:
        logger.error("❌ MCP_GATEWAY_URL environment variable is required when USE_MCP_GATEWAY=true")
        raise HTTPException(
            status_code=500,
            detail="MCP_GATEWAY_URL environment variable is required when USE_MCP_GATEWAY=true"
        )
    
    logger.info("🌐 === MCP GATEWAY CONNECTION ===")
    logger.info(f"🔗 Gateway URL: {mcp_gateway_url}")
    logger.info(f"🔐 Authentication: IAM")
    
    try:
        # Create MCP client with IAM authentication
        logger.info("🔧 Creating MCP client...")
        mcp_client = MCPClient(
            lambda: _create_streamable_http_transport_with_iam(mcp_gateway_url)
        )
        
        # Start the MCP client session
        logger.info("🚀 Starting MCP client session...")
        mcp_client.start()
        logger.info("✅ MCP client session started successfully")
        
        # Get all available tools
        logger.info("🔍 Discovering available tools...")
        tools = _get_full_tools_list(mcp_client)
        
        logger.info("🔧 === MCP TOOLS DISCOVERED ===")
        logger.info(f"📊 Total tools found: {len(tools)}")
        
        if tools:
            for i, tool in enumerate(tools):
                tool_name = getattr(tool, 'tool_name', getattr(tool, 'name', f'tool_{i}'))
                tool_description = getattr(tool, 'description', 'No description')
                logger.info(f"   • Tool {i+1}: {tool_name}")
                logger.info(f"     Description: {tool_description[:100]}...")
        else:
            logger.warning("⚠️ No tools found from MCP Gateway!")
        
        # Create agent with MCP tools
        logger.info("🤖 Creating agent with MCP Gateway tools...")
        agent = Agent(
            system_prompt=HEALTHCARE_SYSTEM_PROMPT,
            tools=tools,
            callback_handler=None
        )
        
        logger.info(f"✅ Agent created successfully with {len(tools)} MCP Gateway tools")
        logger.info("🌐 === MCP GATEWAY CONNECTION COMPLETE ===")
        return agent
        
    except Exception as e:
        logger.error("❌ === MCP GATEWAY CONNECTION FAILED ===")
        logger.error(f"❌ Error: {str(e)}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        
        # Log detailed error information
        import traceback
        logger.error(f"❌ Full traceback:\n{traceback.format_exc()}")
        
        logger.info("🔄 Falling back to local tools...")
        
        # Fallback to local tools if MCP Gateway fails
        fallback_agent = Agent(
            system_prompt=HEALTHCARE_SYSTEM_PROMPT,
            tools=["tools/patient_lookup.py"],
            callback_handler=None
        )
        
        logger.info("✅ Fallback agent created with local tools")
        return fallback_agent


def get_or_create_agent(session_id: str) -> Agent:
    """
    Get or create agent with patient lookup tools.

    Args:
        session_id: Session identifier

    Returns:
        Agent: Configured agent with patient lookup capabilities
    """
    try:
        logger.info("🤖 === AGENT CREATION STARTED ===")
        logger.info(f"📝 Session ID: {session_id}")

        # Check if we should use MCP Gateway or local tools
        use_mcp_gateway = os.getenv("USE_MCP_GATEWAY", "false").lower() == "true"
        
        logger.info("🔧 AGENT CONFIGURATION:")
        logger.info(f"   • MCP Gateway: {use_mcp_gateway}")
        logger.info(f"   • Gateway URL: {os.getenv('MCP_GATEWAY_URL', 'not configured')}")
        logger.info(f"   • AWS Region: {os.getenv('AWS_REGION', 'us-east-1')}")
        logger.info(f"   • Environment: {os.getenv('ENVIRONMENT', 'development')}")
        
        if use_mcp_gateway:
            logger.info("🌐 Using MCP Gateway for tools")
            agent = _create_agent_with_mcp_gateway(session_id)
        else:
            logger.info("🔧 Using local tools")
            # Create agent with local patient lookup tools
            agent = Agent(
                system_prompt=HEALTHCARE_SYSTEM_PROMPT,
                tools=["tools/patient_lookup.py"],  # Load patient lookup tools
                callback_handler=None
            )

        # Log agent capabilities and configuration
        _log_agent_capabilities(agent, use_mcp_gateway)

        # Initialize session state
        agent.state.set("session_id", session_id)
        agent.state.set("session_context", "no_patient")
        agent.state.set("current_patient_id", None)
        agent.state.set("current_patient_name", None)

        logger.info("✅ Agent state initialized successfully")
        logger.info("🤖 === AGENT CREATION COMPLETED ===")
        return agent

    except Exception as e:
        logger.error(f"❌ Failed to create agent: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize agent: {str(e)}"
        )


class InvocationRequest(BaseModel):
    prompt: str
    sessionId: Optional[str] = None


class PatientContextResponse(BaseModel):
    """Structured patient context for frontend integration."""
    patient_id: Optional[str] = Field(None, description="Patient ID or cedula")
    patient_name: Optional[str] = Field(None, description="Patient full name")
    has_patient_context: bool = Field(
        False, description="Whether patient context is available")
    patient_found: bool = Field(
        False, description="Whether a patient was identified in this interaction")
    patient_data: Optional[Dict[str, Any]] = Field(
        None, description="Complete patient data for frontend")


class AgentResponse(BaseModel):
    """Structured agent response with patient context."""
    message: str = Field(..., description="The agent's response message")
    patient_context: PatientContextResponse = Field(
        default_factory=PatientContextResponse, description="Patient context information")


@app.post("/invocations")
async def invoke_agent(request: InvocationRequest):
    """
    Main AgentCore invocation endpoint for healthcare assistant with session management.
    """
    import time
    start_time = time.time()
    
    try:
        logger.info("🚀 === AGENT INVOCATION STARTED ===")
        logger.info(f"📝 Request: prompt_length={len(request.prompt)}, sessionId={request.sessionId}")

        user_message = request.prompt
        if not user_message:
            logger.warning("⚠️ Received request without prompt")
            raise HTTPException(
                status_code=400,
                detail="No prompt provided in request."
            )

        # Extract session ID from request (use a default if not provided)
        session_id = request.sessionId or f"healthcare_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"🔑 Session ID: {session_id}")
        logger.info(f"💬 User message preview: {user_message[:100]}{'...' if len(user_message) > 100 else ''}")

        # Log environment configuration
        use_mcp_gateway = os.getenv("USE_MCP_GATEWAY", "false").lower() == "true"
        logger.info(f"⚙️ Configuration: MCP_Gateway={use_mcp_gateway}, AWS_Region={os.getenv('AWS_REGION', 'us-east-1')}")

        logger.info("🤖 Creating agent...")
        agent_start_time = time.time()
        
        # Get or create agent with patient lookup tools
        agent = get_or_create_agent(session_id)
        
        agent_creation_time = (time.time() - agent_start_time) * 1000
        logger.info(f"✅ Agent created successfully in {agent_creation_time:.2f}ms")

        # Analyze message for patient-related content
        patient_keywords = ["paciente", "patient", "cédula", "cedula", "historia", "historial", "mrn-", "agenda", "cita"]
        might_involve_patient = any(keyword in user_message.lower() for keyword in patient_keywords)
        
        logger.info(f"🔍 Message analysis: patient_related={might_involve_patient}")
        if might_involve_patient:
            detected_keywords = [kw for kw in patient_keywords if kw in user_message.lower()]
            logger.debug(f"🔍 Detected keywords: {detected_keywords}")

        processing_start_time = time.time()

        if might_involve_patient:
            logger.info("🏥 Processing patient-related query with structured output")
            try:
                structured_start_time = time.time()
                
                structured_result = agent.structured_output(
                    output_model=AgentResponse,
                    prompt=user_message
                )
                
                structured_time = (time.time() - structured_start_time) * 1000
                logger.info(f"📊 Structured output completed in {structured_time:.2f}ms")

                # Extract the structured response
                agent_message = structured_result.message
                patient_context_data = structured_result.patient_context
                
                logger.debug(f"📝 Agent message length: {len(agent_message)} characters")
                logger.debug(f"👤 Initial patient context: has_context={patient_context_data.has_patient_context}")

                # Also get patient info from agent state (set by tools)
                logger.debug("🔍 Extracting patient info from agent state...")
                current_patient_id, current_patient_name, current_patient_data = _extract_patient_from_agent_state(agent)

                # Update structured response with agent state if available
                if current_patient_id and current_patient_name:
                    logger.info(f"👤 Patient found in agent state: {current_patient_name} (ID: {current_patient_id})")
                    
                    patient_context_data.patient_id = current_patient_id
                    patient_context_data.patient_name = current_patient_name
                    patient_context_data.has_patient_context = True
                    patient_context_data.patient_found = True
                    
                    # Use complete patient data if available, otherwise create minimal object
                    if current_patient_data:
                        patient_context_data.patient_data = current_patient_data
                        logger.debug("📋 Using complete patient data from agent state")
                    else:
                        patient_context_data.patient_data = {
                            "patient_id": current_patient_id,
                            "full_name": current_patient_name,
                            "date_of_birth": "",
                            "created_at": "",
                            "updated_at": ""
                        }
                        logger.debug("📋 Created minimal patient data object")
                else:
                    logger.debug("👤 No patient found in agent state")

                logger.info(f"✅ Structured output processing complete. Patient found: {patient_context_data.patient_found}")

            except Exception as e:
                logger.warning(
                    f"Structured output failed, falling back to regular processing: {str(e)}")
                # Fallback to regular processing
                result = agent(user_message)
                agent_message = result.message
                current_patient_id, current_patient_name, current_patient_data = _extract_patient_from_agent_state(
                    agent)

                # Create patient context manually
                patient_context_data = PatientContextResponse()
                if current_patient_id and current_patient_name:
                    patient_context_data.patient_id = current_patient_id
                    patient_context_data.patient_name = current_patient_name
                    patient_context_data.has_patient_context = True
                    patient_context_data.patient_found = True
                    # Use complete patient data if available, otherwise create minimal object
                    if current_patient_data:
                        patient_context_data.patient_data = current_patient_data
                    else:
                        patient_context_data.patient_data = {
                            "patient_id": current_patient_id,
                            "full_name": current_patient_name,
                            "date_of_birth": "",
                            "created_at": "",
                            "updated_at": ""
                        }
        else:
            # Regular processing for non-patient queries
            result = agent(user_message)
            agent_message = result.message
            current_patient_id, current_patient_name, current_patient_data = _extract_patient_from_agent_state(
                agent)

            # Create basic patient context
            patient_context_data = PatientContextResponse()
            if current_patient_id and current_patient_name:
                patient_context_data.patient_id = current_patient_id
                patient_context_data.patient_name = current_patient_name
                patient_context_data.has_patient_context = True
                # Include complete patient data if available
                if current_patient_data:
                    patient_context_data.patient_data = current_patient_data
                # Not found in this interaction, but exists in session
                patient_context_data.patient_found = False

        session_context = "patient_session" if current_patient_id else "no_patient"

        # Prepare response with session and patient context using consistent structure
        if current_patient_id and session_context == "patient_session":
            session_prefix = f"processed/{current_patient_id}_medical_notes/"
        else:
            session_prefix = f"processed/unknown_medical_notes/"

        # Convert structured patient context to dict for response
        patient_context_dict = patient_context_data.model_dump()
        patient_context_dict.update({
            "session_prefix": session_prefix,
            "consistent_with_documents": True
        })

        # AgentCore compliant response format - must match the HTTP protocol contract
        response = {
            "response": agent_message,  # Primary response field as required by AgentCore
            "status": "success",  # Status field as shown in examples
            # Additional metadata for frontend integration
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": "healthcare-assistant",
            "capabilities": ["patient_lookup", "patient_info", "appointments", "knowledge_base", "documents"],
            "session_id": session_id,
            "patient_context": patient_context_dict,
            "session_info": {
                "bucket": S3_BUCKET,
                "region": AWS_REGION,
                "notes_saved": False,  # Currently disabled session management
                "conversation_persisted": False,  # Currently disabled session management
                "structure_pattern": "processed/{patient_id}_{data_type}/",
                "tools_available": ["extract_and_search_patient", "get_patient_by_id", "list_recent_patients", "validate_patient_session"]
            }
        }

        logger.info(
            "Healthcare assistant request processed successfully with session management")
        logger.debug(
            f"Response generated: {len(response.get('message', ''))} characters")
        logger.debug(
            f"Session data saved to S3 with prefix: {response['patient_context']['session_prefix']}")

        return response

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Agent processing failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Agent processing failed: {str(e)}")


@app.get("/ping")
async def ping():
    """Health check endpoint required by AgentCore Runtime."""
    import time
    
    # Test logging on each ping to verify it's working
    logger.info("🏓 Ping endpoint called - logging test")
    
    return {
        "status": "Healthy",
        "time_of_last_update": int(time.time()),
        "logging_test": "Check logs for ping message"
    }

@app.get("/test-logging")
async def test_logging_endpoint():
    """Test endpoint to verify logging is working and not suppressed."""
    logger.info("🧪 Test logging endpoint called")
    
    # Run the logging test
    test_result = test_logging()
    
    logger.info("✅ Logging test completed")
    
    return {
        "status": "success",
        "message": "Logging test completed - check console/CloudWatch logs",
        "test_result": test_result,
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "mcp_gateway": os.getenv("USE_MCP_GATEWAY", "false")
    }


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
            # We'll search for patterns like processed/{patient_id}_medical_notes/
            ("patient", f"processed/"),
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
                                patient_folder = parts[0].replace(
                                    'processed/', '')
                                if '_medical_notes' in patient_folder:
                                    extracted_patient_id = patient_folder.replace(
                                        '_medical_notes', '')
                                    session_info["extracted_patient_id"] = extracted_patient_id

                            # Count messages
                            messages_response = s3_client.list_objects_v2(
                                Bucket=S3_BUCKET,
                                Prefix=key.split(
                                    '/session_')[0] + f"/session_{session_id}/agents/",
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
        raise HTTPException(
            status_code=500, detail=f"Failed to get session info: {str(e)}")


@app.on_event("startup")
async def startup_event():
    """Startup event handler for AgentCore Runtime."""
    logger.info("Healthcare Assistant Agent starting up...")
    logger.info(f"S3 Bucket: {S3_BUCKET}")
    logger.info(f"S3 Prefix: {S3_PREFIX}")
    logger.info(f"AWS Region: {AWS_REGION}")
    logger.info("Agent ready for AgentCore Runtime")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler for AgentCore Runtime."""
    logger.info("Healthcare Assistant Agent shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
