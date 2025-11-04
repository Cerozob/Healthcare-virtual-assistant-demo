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

    # Managed Services Configuration
    knowledge_base_id: str = Field(
        alias="BEDROCK_KNOWLEDGE_BASE_ID", description="Bedrock Knowledge Base ID")
    guardrail_id: Optional[str] = Field(
        default=None, alias="BEDROCK_GUARDRAIL_ID", description="Bedrock Guardrail ID")
    guardrail_version: Optional[str] = Field(
        default="DRAFT", alias="BEDROCK_GUARDRAIL_VERSION", description="Guardrail version")

    # AgentCore Gateway Configuration
    mcp_gateway_url: str = Field(
        alias="MCP_GATEWAY_URL", description="AgentCore Gateway URL")
    gateway_id: str = Field(
        alias="GATEWAY_ID", description="AgentCore Gateway ID")
    aws_region: str = Field(alias="AWS_REGION", description="AWS region")

    # AgentCore Memory Configuration
    agentcore_memory_id: str = Field(
        alias="AGENTCORE_MEMORY_ID", description="AgentCore Memory ID")

    # S3 Configuration for file reference tools
    raw_bucket_name: Optional[str] = Field(
        default=None, alias="RAW_BUCKET_NAME", description="S3 bucket for raw uploaded files")
    session_bucket: Optional[str] = Field(
        default=None, alias="SESSION_BUCKET", description="S3 bucket for processed session data")

    # AgentCore Memory is used exclusively - no additional configuration needed

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
        max_tokens=4096,  # Default value since we removed this from config
        top_p=0.9,  # Default value since we removed this from config
    )
