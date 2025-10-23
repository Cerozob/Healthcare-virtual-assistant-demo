"""
SSM Configuration Manager for Healthcare System.
Handles retrieval and caching of configuration parameters from AWS Systems Manager.
"""

import boto3
import logging
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class SSMConfigError(Exception):
    """Custom exception for SSM configuration operations."""
    
    def __init__(self, message: str, parameter_name: str = None, original_error: Exception = None):
        super().__init__(message)
        self.parameter_name = parameter_name
        self.original_error = original_error


class SSMConfig:
    """
    Configuration manager using AWS Systems Manager Parameter Store.
    Provides caching and easy access to application configuration.
    """
    
    def __init__(self, base_path: str = "/healthcare"):
        """
        Initialize the SSM configuration manager.
        
        Args:
            base_path: Base path for all configuration parameters
        """
        self.ssm = boto3.client('ssm')
        self.base_path = base_path.rstrip('/')
        self._cache = {}
        
    def get_parameter(
        self, 
        parameter_name: str, 
        decrypt: bool = False,
        use_cache: bool = True
    ) -> str:
        """
        Get a single parameter value from SSM.
        
        Args:
            parameter_name: Parameter name (without base path)
            decrypt: Whether to decrypt SecureString parameters
            use_cache: Whether to use cached values
            
        Returns:
            Parameter value as string
            
        Raises:
            SSMConfigError: If parameter retrieval fails
        """
        full_path = f"{self.base_path}/{parameter_name.lstrip('/')}"
        
        # Check cache first
        if use_cache and full_path in self._cache:
            logger.debug(f"Using cached value for parameter: {full_path}")
            return self._cache[full_path]
        
        try:
            response = self.ssm.get_parameter(
                Name=full_path,
                WithDecryption=decrypt
            )
            
            value = response['Parameter']['Value']
            
            # Cache the value
            if use_cache:
                self._cache[full_path] = value
            
            logger.debug(f"Retrieved parameter: {full_path}")
            return value
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            
            if error_code == 'ParameterNotFound':
                logger.error(f"Parameter not found: {full_path}")
                raise SSMConfigError(
                    f"Configuration parameter not found: {parameter_name}",
                    parameter_name,
                    e
                )
            else:
                logger.error(f"Failed to retrieve parameter {full_path}: {error_message}")
                raise SSMConfigError(
                    f"Failed to retrieve configuration: {error_message}",
                    parameter_name,
                    e
                )
    
    def get_parameters_by_path(
        self, 
        path: str = "",
        recursive: bool = True,
        decrypt: bool = False,
        use_cache: bool = True
    ) -> Dict[str, str]:
        """
        Get multiple parameters by path from SSM.
        
        Args:
            path: Path under base_path to retrieve (empty for all)
            recursive: Whether to retrieve parameters recursively
            decrypt: Whether to decrypt SecureString parameters
            use_cache: Whether to use cached values
            
        Returns:
            Dictionary mapping parameter names to values
            
        Raises:
            SSMConfigError: If parameter retrieval fails
        """
        full_path = f"{self.base_path}/{path.lstrip('/')}" if path else self.base_path
        cache_key = f"path:{full_path}:recursive:{recursive}"
        
        # Check cache first
        if use_cache and cache_key in self._cache:
            logger.debug(f"Using cached values for path: {full_path}")
            return self._cache[cache_key]
        
        try:
            parameters = {}
            next_token = None
            
            while True:
                request_params = {
                    'Path': full_path,
                    'Recursive': recursive,
                    'WithDecryption': decrypt,
                    'MaxResults': 10  # AWS limit
                }
                
                if next_token:
                    request_params['NextToken'] = next_token
                
                response = self.ssm.get_parameters_by_path(**request_params)
                
                # Process parameters
                for param in response.get('Parameters', []):
                    # Remove base path to get relative name
                    relative_name = param['Name'][len(self.base_path):].lstrip('/')
                    parameters[relative_name] = param['Value']
                
                # Check for more parameters
                next_token = response.get('NextToken')
                if not next_token:
                    break
            
            # Cache the results
            if use_cache:
                self._cache[cache_key] = parameters
                # Also cache individual parameters
                for name, value in parameters.items():
                    param_path = f"{self.base_path}/{name}"
                    self._cache[param_path] = value
            
            logger.debug(f"Retrieved {len(parameters)} parameters from path: {full_path}")
            return parameters
            
        except ClientError as e:
            error_message = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"Failed to retrieve parameters from path {full_path}: {error_message}")
            raise SSMConfigError(
                f"Failed to retrieve configuration from path: {error_message}",
                path,
                e
            )
    
    def get_database_config(self) -> Dict[str, str]:
        """
        Get database configuration parameters.
        
        Returns:
            Dictionary with database configuration
            
        Raises:
            SSMConfigError: If database configuration retrieval fails
        """
        try:
            return self.get_parameters_by_path("database")
        except SSMConfigError:
            logger.error("Failed to retrieve database configuration")
            raise
    
    def get_api_config(self) -> Dict[str, str]:
        """
        Get API configuration parameters.
        
        Returns:
            Dictionary with API configuration
            
        Raises:
            SSMConfigError: If API configuration retrieval fails
        """
        try:
            return self.get_parameters_by_path("api")
        except SSMConfigError:
            logger.error("Failed to retrieve API configuration")
            raise
    
    def get_bedrock_config(self) -> Dict[str, str]:
        """
        Get Bedrock configuration parameters.
        
        Returns:
            Dictionary with Bedrock configuration
            
        Raises:
            SSMConfigError: If Bedrock configuration retrieval fails
        """
        try:
            return self.get_parameters_by_path("bedrock")
        except SSMConfigError:
            logger.error("Failed to retrieve Bedrock configuration")
            raise
    
    def clear_cache(self) -> None:
        """Clear the parameter cache."""
        self._cache.clear()
        logger.debug("Parameter cache cleared")
    
    def get_cached_parameters(self) -> Dict[str, str]:
        """
        Get all cached parameters.
        
        Returns:
            Dictionary of cached parameters
        """
        return self._cache.copy()
    
    def set_cache_value(self, parameter_name: str, value: str) -> None:
        """
        Manually set a cache value (useful for testing).
        
        Args:
            parameter_name: Parameter name
            value: Parameter value
        """
        full_path = f"{self.base_path}/{parameter_name.lstrip('/')}"
        self._cache[full_path] = value
        logger.debug(f"Manually cached parameter: {full_path}")
    
    def get_agent_config(self, agent_name: str) -> Dict[str, str]:
        """
        Get configuration for a specific Bedrock agent.
        
        Args:
            agent_name: Name of the agent (e.g., 'orchestrator', 'info_retrieval')
            
        Returns:
            Dictionary with agent configuration
            
        Raises:
            SSMConfigError: If agent configuration retrieval fails
        """
        try:
            return self.get_parameters_by_path(f"bedrock/agents/{agent_name}")
        except SSMConfigError:
            logger.error(f"Failed to retrieve configuration for agent: {agent_name}")
            raise
    
    def get_vpc_config(self) -> Dict[str, str]:
        """
        Get VPC configuration parameters.
        
        Returns:
            Dictionary with VPC configuration
            
        Raises:
            SSMConfigError: If VPC configuration retrieval fails
        """
        try:
            return self.get_parameters_by_path("vpc")
        except SSMConfigError:
            logger.error("Failed to retrieve VPC configuration")
            raise
    
    # Agent-specific configuration methods
    def get_orchestrator_agent_id(self) -> str:
        """Get orchestrator agent ID."""
        try:
            return self.get_parameter("bedrock/orchestrator-agent-id")
        except SSMConfigError:
            logger.warning("Orchestrator agent ID not configured")
            return ""
    
    def get_orchestrator_alias_id(self) -> str:
        """Get orchestrator agent alias ID."""
        try:
            return self.get_parameter("bedrock/orchestrator-agent-alias-id")
        except SSMConfigError:
            logger.warning("Orchestrator agent alias ID not configured, using default")
            return "TSTALIASID"
    
    def get_scheduling_agent_id(self) -> str:
        """Get scheduling agent ID."""
        try:
            return self.get_parameter("bedrock/scheduling-agent-id")
        except SSMConfigError:
            logger.warning("Scheduling agent ID not configured")
            return ""
    
    def get_scheduling_alias_id(self) -> str:
        """Get scheduling agent alias ID."""
        try:
            return self.get_parameter("bedrock/scheduling-agent-alias-id")
        except SSMConfigError:
            logger.warning("Scheduling agent alias ID not configured, using default")
            return "TSTALIASID"
    
    def get_information_agent_id(self) -> str:
        """Get information retrieval agent ID."""
        try:
            return self.get_parameter("bedrock/information-agent-id")
        except SSMConfigError:
            logger.warning("Information agent ID not configured")
            return ""
    
    def get_information_alias_id(self) -> str:
        """Get information retrieval agent alias ID."""
        try:
            return self.get_parameter("bedrock/information-agent-alias-id")
        except SSMConfigError:
            logger.warning("Information agent alias ID not configured, using default")
            return "TSTALIASID"
