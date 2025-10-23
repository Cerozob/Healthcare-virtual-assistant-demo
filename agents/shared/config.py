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
    Agent configuration loaded from environment variables.
    No hardcoded values - all configuration comes from deployment.
    """
    
    # Model Configuration
    model_id: str = Field(description="Bedrock model ID")
    model_temperature: float = Field(default=0.1, description="Model temperature")
    model_max_tokens: int = Field(default=4096, description="Maximum tokens")
    model_top_p: float = Field(default=0.9, description="Top-p sampling")
    
    # Knowledge Base Configuration
    knowledge_base_id: str = Field(description="Bedrock Knowledge Base ID")
    supplemental_data_bucket: str = Field(description="S3 bucket for supplemental data")
    
    # API Configuration
    healthcare_api_endpoint: str = Field(description="Healthcare API base URL")
    database_cluster_arn: str = Field(description="Aurora cluster ARN")
    database_secret_arn: str = Field(description="Database secret ARN")
    
    # Agent Configuration
    default_language: str = Field(default="es-LATAM", description="Default language")
    streaming_enabled: bool = Field(default=True, description="Enable streaming responses")
    session_timeout_minutes: int = Field(default=30, description="Session timeout")
    
    # Guardrails Configuration
    guardrail_id: Optional[str] = Field(default=None, description="Bedrock Guardrail ID")
    guardrail_version: Optional[str] = Field(default=None, description="Guardrail version")
    
    # Observability Configuration
    enable_tracing: bool = Field(default=True, description="Enable OpenTelemetry tracing")
    log_level: str = Field(default="INFO", description="Logging level")
    metrics_namespace: str = Field(default="Healthcare/Agents", description="CloudWatch metrics namespace")
    
    class Config:
        env_file = None  # No .env files - configuration from deployment only
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
