# Healthcare Assistant Prompts

This directory contains all system prompts and prompt templates used by the healthcare assistant agents.

## Available Prompts

### Main Agent Prompts
- `healthcare.md` - Main healthcare assistant system prompt
- `orchestrator.md` - Multi-agent orchestrator prompt
- `information_retrieval.md` - Information retrieval agent prompt
- `appointment_scheduling.md` - Appointment scheduling agent prompt

### Tool Prompts
- `patient_extraction.md` - Patient information extraction system prompt
- `patient_analysis.md` - Patient analysis prompt template

## Usage

Prompts are loaded using the `get_prompt()` function from `shared/prompts.py`:

```python
from shared.prompts import get_prompt

# Load a system prompt
system_prompt = get_prompt("healthcare")

# Load a template prompt and format it
analysis_prompt = get_prompt("patient_analysis").format(user_message="...")
```

## Guidelines

1. **Keep prompts in markdown files** - Don't hardcode prompts in Python files
2. **Use descriptive names** - Prompt files should clearly indicate their purpose
3. **Include examples** - Add usage examples in prompts when helpful
4. **Use templates** - Use `{variable}` placeholders for dynamic content
5. **Document changes** - Update this README when adding new prompts

## Prompt Organization

- **System prompts**: Complete prompts for agent initialization
- **Template prompts**: Prompts with placeholders that need formatting
- **Specialized prompts**: Domain-specific prompts for tools and specialized agents
