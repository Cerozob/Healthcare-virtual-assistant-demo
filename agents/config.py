"""
Configuration management for Healthcare Assistant Agent.
Loads settings from environment variables with proper defaults.
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration class for the Healthcare Assistant Agent."""

   

    # Bedrock Configuration (always required)
    bedrock_model_id: str
    bedrock_knowledge_base_id: str
    bedrock_guardrail_id: str
    bedrock_guardrail_version: str

    # MCP Gateway Configuration (always enabled)
    mcp_gateway_url: str
    gateway_id: str

    # AWS Configuration
    aws_region: str

    # Session Management (always required)
    session_bucket: str

    @classmethod
    def from_env(cls) -> 'AgentConfig':
        """Create configuration from environment variables. No fallbacks - fail fast if missing."""

        def get_required(key: str) -> str:
            """Get required environment variable or raise error."""
            value = os.getenv(key)
            if value is None:
                raise ValueError(
                    f"Required environment variable {key} is not set")
            return value

        def get_bool(key: str) -> bool:
            """Get boolean value from environment variable."""
            value = get_required(key).lower()
            return value in ('true', '1', 'yes', 'on')

        def get_int(key: str) -> int:
            """Get integer value from environment variable."""
            try:
                return int(get_required(key))
            except ValueError as e:
                raise ValueError(f"Invalid integer value for {key}: {e}")

        config = cls(
           
            # Bedrock Configuration (always required)
            bedrock_model_id=get_required("BEDROCK_MODEL_ID"),
            bedrock_knowledge_base_id=get_required(
                "BEDROCK_KNOWLEDGE_BASE_ID"),
            bedrock_guardrail_id=get_required("BEDROCK_GUARDRAIL_ID"),
            bedrock_guardrail_version=get_required(
                "BEDROCK_GUARDRAIL_VERSION"),

            # MCP Gateway Configuration (always enabled)
            mcp_gateway_url=get_required("MCP_GATEWAY_URL"),
            gateway_id=get_required("GATEWAY_ID"),

            # AWS Configuration
            aws_region=get_required("AWS_REGION"),

            # Session Management (always required)
            session_bucket=get_required("SESSION_BUCKET"),

 )

        logger.info(f"Configuration loaded: {config.to_dict()}")
        return config

    def validate(self) -> bool:
        """Validate configuration and return True if valid."""
        # All fields are required, so if we got here, validation passed
        logger.info(
            "Configuration validation passed - all required fields present")
        return True

    @property
    def session_prefix(self) -> str:
        """Session prefix is always 'agents_sessions/'."""
        return "agents_sessions/"

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
           
            "bedrock_model_id": self.bedrock_model_id,
            "bedrock_knowledge_base_id": self.bedrock_knowledge_base_id,
            "bedrock_guardrail_id": self.bedrock_guardrail_id,
            "bedrock_guardrail_version": self.bedrock_guardrail_version,
            "mcp_gateway_url": self.mcp_gateway_url,
            "gateway_id": self.gateway_id,
            "aws_region": self.aws_region,
            "session_bucket": self.session_bucket,
            "session_prefix": "agents_sessions/"
        }


# Global configuration instance
config: Optional[AgentConfig] = None


def get_config() -> AgentConfig:
    """Get the global configuration instance."""
    global config
    if config is None:
        config = AgentConfig.from_env()
        if not config.validate():
            raise ValueError("Invalid configuration")
    return config


def reload_config() -> AgentConfig:
    """Reload configuration from environment variables."""
    global config
    config = AgentConfig.from_env()
    if not config.validate():
        raise ValueError("Invalid configuration")
    return config
