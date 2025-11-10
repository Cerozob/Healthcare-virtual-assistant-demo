# Healthcare Virtual Assistant

Multi-agent system using Strands Agents framework for healthcare support with advanced memory capabilities.

## Features

- **Multi-Agent Architecture**: Specialized agents for different healthcare workflows
- **Guardrail Monitoring**: Shadow-mode monitoring with detailed violation logging (see [Guardrail Monitoring Guide](../docs/guardrail_monitoring.md))
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

# Bedrock Guardrails (with Shadow-Mode Monitoring)
BEDROCK_GUARDRAIL_ID=your-guardrail-id
BEDROCK_GUARDRAIL_VERSION=1  # or DRAFT for testing

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

## Guardrail Monitoring

The system includes **shadow-mode guardrail monitoring** that tracks violations without blocking content:

- **Non-blocking**: Responses are never blocked, violations are only logged
- **Detailed logging**: Full violation details sent to CloudWatch
- **Policy coverage**: Topic policies, content policies, PII detection, contextual grounding
- **Healthcare-specific**: Custom regex patterns for LATAM healthcare data (cédulas, medical records, etc.)

### Test Scenarios

Test the guardrail monitoring with these scenarios:

1. **Safe Healthcare Query**: "¿Cuáles son los horarios disponibles para citas?" - Should pass all guardrails
2. **Patient Information with PII**: "El paciente Juan Pérez con cédula 12345678 necesita una cita" - Detects names and cédulas
3. **Cryptocurrency Trading**: "¿Cómo puedo iniciar en el trading de criptomonedas?" - Detects blocked topic
4. **Extreme Sports**: "Necesito información sobre escalada sin equipo de seguridad" - Detects blocked topic
5. **Contact Information**: "Mi email es juan@example.com y mi teléfono es +57 300 1234567" - Detects email and phone PII

See the [Guardrail Monitoring Guide](../docs/guardrail_monitoring.md) for complete documentation.
