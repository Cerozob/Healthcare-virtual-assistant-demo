# Healthcare Virtual Assistant

Multi-agent system using Strands Agents framework for healthcare support with advanced memory capabilities.

## Features

- **Multi-Agent Architecture**: Specialized agents for different healthcare workflows
- **AgentCore Memory Integration**: Automatic conversation context retention
- **Intelligent Retrieval**: Smart context retrieval for healthcare conversations
- **Healthcare-Specific Tools**: Patient lookup, appointment scheduling, medical records

## Agents

- **Orchestrator**: Main coordination and routing
- **Info Retrieval**: Patient data and medical record lookup
- **Appointment Scheduling**: Calendar management and booking

## Memory System

The system uses **AgentCore Memory exclusively** for:

- **Conversation Persistence**: Automatic context retention across conversation turns
- **Healthcare Context**: Remembers patient information, treatments, and medical discussions
- **Intelligent Retrieval**: Smart context retrieval based on conversation relevance

See [AgentCore Memory Integration](docs/agentcore-memory-integration.md) for details.

## Tech Stack

- Python 3.11+, Strands Agents, FastAPI
- AWS Bedrock for AI models and AgentCore Memory
- PostgreSQL for data persistence
- OpenTelemetry for observability

## Quick Start

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your AWS configuration
   ```

3. **Test memory integration**:
   ```bash
   python test_agentcore_memory.py
   ```

4. **Start agent server**:
   ```bash
   python main.py
   # Server runs on http://localhost:8080
   ```

## Configuration

Key environment variables:

```bash
# Bedrock Model Configuration
BEDROCK_MODEL_ID=global.anthropic.claude-haiku-4-5-20251001-v1:0
MODEL_TEMPERATURE=0.1

# Bedrock Knowledge Base
BEDROCK_KNOWLEDGE_BASE_ID=your-knowledge-base-id

# Bedrock Guardrails
BEDROCK_GUARDRAIL_ID=your-guardrail-id
BEDROCK_GUARDRAIL_VERSION=1

# AgentCore Gateway Configuration
MCP_GATEWAY_URL=your-agentcore-gateway-url
GATEWAY_ID=your-gateway-id

# AWS Configuration
AWS_REGION=us-east-1

# AgentCore Memory is used automatically - no additional config needed
```

## Usage

The healthcare agent supports both text-only and multimodal interactions (images, documents).

### Text-Only Interaction

```python
from healthcare_agent import create_healthcare_agent

# Create and initialize agent
agent = create_healthcare_agent("user_session_123")

# Prepare content in Strands format
content_blocks = [
    {"text": "¿Cuáles son los horarios disponibles para citas?"}
]

# Process message
result = agent.process_message(content_blocks)
print(f"Response: {result['response']}")
print(f"Patient context: {result['patientContext']}")
```

### Multimodal Interaction (Images & Documents)

```python
from healthcare_agent import create_healthcare_agent

# Create agent
agent = create_healthcare_agent("user_session_multimodal")

# Prepare multimodal content in Strands format
content_blocks = [
    {"text": "Analiza esta radiografía y el documento médico adjunto. ¿Qué información puedes extraer?"},
    {
        "image": {
            "format": "png",
            "source": {
                "bytes": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB..."  # base64 image data
            }
        }
    },
    {
        "document": {
            "format": "pdf",
            "name": "historia_clinica.pdf",
            "source": {
                "bytes": "JVBERi0xLjQKJcOkw7zDtsO8w6..."  # base64 PDF data
            }
        }
    }
]

# Process multimodal message
result = agent.process_message(content_blocks)
print(f"Response: {result['response']}")
print(f"Patient context: {result['patientContext']}")
```

### Supported Media Formats

**Images:**
- JPEG/JPG (`image/jpeg`)
- PNG (`image/png`) 
- GIF (`image/gif`)
- WebP (`image/webp`)

**Documents:**
- PDF (`application/pdf`)
- Text files (`text/plain`)
- Word documents (`application/msword`, `.docx`)
- Markdown (`text/markdown`)

## Tools

- Patient lookup and medical history
- Appointment scheduling integration
- Document processing workflow
- Automatic context retention with AgentCore Memory
- **Multimodal analysis**: Image and document processing with Strands Agent framework
