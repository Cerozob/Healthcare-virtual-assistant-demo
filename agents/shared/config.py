"""
Configuration management for Strands Agents system.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class ModelConfig(BaseModel):
    """Model configuration settings."""
    
    model_id: str = Field(description="Bedrock model identifier")
    temperature: float = Field(default=0.1, description="Model temperature")
    max_tokens: int = Field(default=4096, description="Maximum tokens")
    top_p: float = Field(default=0.9, description="Top-p sampling")


class AgentConfig(BaseSettings):
    """
    Simplified agent configuration using managed AWS services.
    """
    
    # Model Configuration
    model_id: str = Field(alias="BEDROCK_MODEL_ID", description="Bedrock model ID")
    model_temperature: float = Field(default=0.1, alias="MODEL_TEMPERATURE", description="Model temperature")
    model_max_tokens: int = Field(default=4096, alias="MODEL_MAX_TOKENS", description="Maximum tokens")
    model_top_p: float = Field(default=0.9, alias="MODEL_TOP_P", description="Top-p sampling")
    
    # Managed Services Configuration
    knowledge_base_id: str = Field(alias="BEDROCK_KNOWLEDGE_BASE_ID", description="Bedrock Knowledge Base ID")
    guardrail_id: Optional[str] = Field(default=None, alias="BEDROCK_GUARDRAIL_ID", description="Bedrock Guardrail ID")
    guardrail_version: Optional[str] = Field(default="DRAFT", alias="BEDROCK_GUARDRAIL_VERSION", description="Guardrail version")
    
    # AgentCore Gateway Configuration
    mcp_gateway_url: str = Field(alias="MCP_GATEWAY_URL", description="AgentCore Gateway URL")
    gateway_id: str = Field(alias="GATEWAY_ID", description="AgentCore Gateway ID")
    aws_region: str = Field(alias="AWS_REGION", description="AWS region")
    
    # Session Management Configuration (always S3, always persisted)
    session_bucket: str = Field(alias="SESSION_BUCKET", description="S3 bucket for session storage")
    
    # Agent Configuration
    default_language: str = Field(default="es-LATAM", description="Default language")
    
    # Observability Configuration
    enable_tracing: bool = Field(default=True, alias="ENABLE_TRACING", description="Enable OpenTelemetry tracing")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL", description="Logging level")
    
    class Config:
        env_file = ".env"  # Load from .env file for local development
        case_sensitive = False
        env_prefix = ""


def get_agent_config() -> AgentConfig:
    """
    Get agent configuration from environment variables.
    
    Returns:
        AgentConfig: Configuration instance
        
    Raises:
        ValueError: If required configuration is missing
    """
    try:
        return AgentConfig()
    except Exception as e:
        raise ValueError(f"Failed to load agent configuration: {e}")


def get_model_config() -> ModelConfig:
    """
    Get model configuration from agent config.
    
    Returns:
        ModelConfig: Model configuration instance
    """
    config = get_agent_config()
    return ModelConfig(
        model_id=config.model_id,
        temperature=config.model_temperature,
        max_tokens=config.model_max_tokens,
        top_p=config.model_top_p,
    )
