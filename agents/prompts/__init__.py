"""
Prompts module for healthcare agent.
"""

import os
from pathlib import Path


def get_prompt(prompt_name: str) -> str:
    """Load a prompt from the prompts directory."""
    prompt_file = Path(__file__).parent / f"{prompt_name}.md"
    
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    
    return prompt_file.read_text(encoding='utf-8')
