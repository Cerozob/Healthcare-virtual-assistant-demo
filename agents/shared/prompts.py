"""
Simple prompt management for Strands Agents.
"""

from pathlib import Path
from typing import Dict

def load_prompt(prompt_name: str) -> str:
    """Load a system prompt from the prompts directory."""
    agents_dir = Path(__file__).parent.parent
    prompt_path = agents_dir / "prompts" / f"{prompt_name}.md"
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read().strip()


# Simple cache for loaded prompts
_prompt_cache: Dict[str, str] = {}


def get_prompt(prompt_name: str) -> str:
    """Get a system prompt with caching."""
    if prompt_name not in _prompt_cache:
        _prompt_cache[prompt_name] = load_prompt(prompt_name)
    
    return _prompt_cache[prompt_name]
