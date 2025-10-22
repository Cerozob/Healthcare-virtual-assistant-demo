"""
RDS Data API Database Manager for Healthcare System.
Provides a clean interface for executing SQL queries using AWS RDS Data API.
"""

import boto3
import json
import logging
from typing import Dict, List, Any, Optional, Union
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Custom exception for database operations."""
    
    def __init__(self, message: str, error_code: str = None, original_error: Exception = None):
        super().__init__(message)
        self.error_code = error_code
        self.original_error = original_error


class DatabaseManager:
    """
    Database manager using AWS RDS Data API for Aurora PostgreSQL.
    Handles connection management, query execution, and result parsing.
    """
    
    def __init__(self):
        """Initialize the database manager with RDS Data API client."""
        self.rds_data = boto3.client('rds-data')
        self.ssm = boto3.client('ssm')
        
        # Cache for database configuration
        self._cluster_arn = None
        self._secret_arn = None
        self._database_name = None
        
    def _get_database_config(self) -> Dict[str, str]:
        """Get database configuration from SSM parameters."""
        if not all([self._cluster_arn, self._secret_arn, self._database_name]):
            try:
                # Get all database parameters at once
                response = self.ssm.get_parameters_by_path(
                    Path='/healthcare/database/',
                    Recursive=True
                )
                
                params = {param['Name'].split('/')[-1]: param['Value'] 
                         for param in response['Parameters']}
                
                self._cluster_arn = params.get('cluster-arn')
                self._secret_arn = params.get('secret-arn')
                self._database_name = params.get('name', 'healthcare')
                
                if not self._cluster_arn or not self._secret_arn:
                    raise DatabaseError(
                        "Missing required database configuration in SSM",
                        "MISSING_CONFIG"
                    )
                    
            except ClientError as e:
                logger.error(f"Failed to get database configuration: {e}")
                raise DatabaseError(
                    "Failed to retrieve database configuration",
                    "CONFIG_ERROR",
                    e
                )
        
        return {
            'cluster_arn': self._cluster_arn,
            'secret_arn': self._secret_arn,
            'database_name': self._database_name
        }
    
    def execute_sql(
        self, 
        sql: str, 
        parameters: List[Dict[str, Any]] = None,
        transaction_id: str = None
    ) -> Dict[str, Any]:
        """
        Execute SQL statement using RDS Data API.
        
        Args:
            sql: SQL statement to execute
            parameters: List of parameter dictionaries for the SQL statement
            transaction_id: Optional transaction ID for multi-statement transactions
            
        Returns:
            Dictionary containing query results
            
        Raises:
            DatabaseError: If the query execution fails
        """
        try:
            config = self._get_database_config()
            
            # Prepare the request
            request_params = {
                'resourceArn': config['cluster_arn'],
                'secretArn': config['secret_arn'],
                'database': config['database_name'],
                'sql': sql,
                'includeResultMetadata': True
            }
            
            # Add parameters if provided
            if parameters:
                request_params['parameters'] = parameters
                
            # Add transaction ID if provided
            if transaction_id:
                request_params['transactionId'] = transaction_id
            
            logger.debug(f"Executing SQL: {sql}")
            logger.debug(f"Parameters: {parameters}")
            
            # Execute the statement
            response = self.rds_data.execute_statement(**request_params)
            
            logger.debug(f"Query executed successfully, affected rows: {response.get('numberOfRecordsUpdated', 0)}")
            
            return response
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'UNKNOWN')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            
            logger.error(f"Database query failed: {error_message}")
            logger.error(f"SQL: {sql}")
            logger.error(f"Parameters: {parameters}")
            
            raise DatabaseError(
                f"Database query failed: {error_message}",
                error_code,
                e
            )
        except Exception as e:
            logger.error(f"Unexpected error executing SQL: {e}")
            raise DatabaseError(
                f"Unexpected database error: {str(e)}",
                "UNEXPECTED_ERROR",
                e
            )
    
    def begin_transaction(self) -> str:
        """
        Begin a new database transaction.
        
        Returns:
            Transaction ID string
            
        Raises:
            DatabaseError: If transaction creation fails
        """
        try:
            config = self._get_database_config()
            
            response = self.rds_data.begin_transaction(
                resourceArn=config['cluster_arn'],
                secretArn=config['secret_arn'],
                database=config['database_name']
            )
            
            transaction_id = response['transactionId']
            logger.debug(f"Transaction started: {transaction_id}")
            
            return transaction_id
            
        except ClientError as e:
            error_message = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"Failed to begin transaction: {error_message}")
            raise DatabaseError(
                f"Failed to begin transaction: {error_message}",
                "TRANSACTION_ERROR",
                e
            )
    
    def commit_transaction(self, transaction_id: str) -> None:
        """
        Commit a database transaction.
        
        Args:
            transaction_id: Transaction ID to commit
            
        Raises:
            DatabaseError: If transaction commit fails
        """
        try:
            config = self._get_database_config()
            
            self.rds_data.commit_transaction(
                resourceArn=config['cluster_arn'],
                secretArn=config['secret_arn'],
                transactionId=transaction_id
            )
            
            logger.debug(f"Transaction committed: {transaction_id}")
            
        except ClientError as e:
            error_message = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"Failed to commit transaction: {error_message}")
            raise DatabaseError(
                f"Failed to commit transaction: {error_message}",
                "TRANSACTION_ERROR",
                e
            )
    
    def rollback_transaction(self, transaction_id: str) -> None:
        """
        Rollback a database transaction.
        
        Args:
            transaction_id: Transaction ID to rollback
            
        Raises:
            DatabaseError: If transaction rollback fails
        """
        try:
            config = self._get_database_config()
            
            self.rds_data.rollback_transaction(
                resourceArn=config['cluster_arn'],
                secretArn=config['secret_arn'],
                transactionId=transaction_id
            )
            
            logger.debug(f"Transaction rolled back: {transaction_id}")
            
        except ClientError as e:
            error_message = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"Failed to rollback transaction: {error_message}")
            raise DatabaseError(
                f"Failed to rollback transaction: {error_message}",
                "TRANSACTION_ERROR",
                e
            )
    
    def create_parameter(self, name: str, value: Any, type_hint: str = None) -> Dict[str, Any]:
        """
        Create a parameter dictionary for RDS Data API.
        
        Args:
            name: Parameter name
            value: Parameter value
            type_hint: Optional type hint ('string', 'long', 'double', 'boolean', 'blob')
            
        Returns:
            Parameter dictionary formatted for RDS Data API
        """
        param = {'name': name}
        
        # Auto-detect type if not provided
        if type_hint is None:
            if isinstance(value, str):
                type_hint = 'string'
            elif isinstance(value, int):
                type_hint = 'long'
            elif isinstance(value, float):
                type_hint = 'double'
            elif isinstance(value, bool):
                type_hint = 'boolean'
            elif isinstance(value, bytes):
                type_hint = 'blob'
            else:
                # Default to string for other types
                type_hint = 'string'
                value = str(value)
        
        # Handle None values
        if value is None:
            param['value'] = {'isNull': True}
        else:
            # Set the appropriate value type
            if type_hint == 'string':
                param['value'] = {'stringValue': str(value)}
            elif type_hint == 'long':
                param['value'] = {'longValue': int(value)}
            elif type_hint == 'double':
                param['value'] = {'doubleValue': float(value)}
            elif type_hint == 'boolean':
                param['value'] = {'booleanValue': bool(value)}
            elif type_hint == 'blob':
                param['value'] = {'blobValue': value}
            else:
                # Fallback to string
                param['value'] = {'stringValue': str(value)}
        
        return param
    
    def parse_records(
        self, 
        records: List[List[Dict[str, Any]]], 
        column_metadata: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Parse RDS Data API records into a list of dictionaries.
        
        Args:
            records: Raw records from RDS Data API response
            column_metadata: Column metadata from RDS Data API response
            
        Returns:
            List of dictionaries with column names as keys
        """
        if not records or not column_metadata:
            return []
        
        # Extract column names
        column_names = [col['name'] for col in column_metadata]
        
        parsed_records = []
        for record in records:
            row = {}
            for i, field in enumerate(record):
                column_name = column_names[i] if i < len(column_names) else f'column_{i}'
                
                # Extract the actual value from the field
                if 'isNull' in field and field['isNull']:
                    row[column_name] = None
                elif 'stringValue' in field:
                    row[column_name] = field['stringValue']
                elif 'longValue' in field:
                    row[column_name] = field['longValue']
                elif 'doubleValue' in field:
                    row[column_name] = field['doubleValue']
                elif 'booleanValue' in field:
                    row[column_name] = field['booleanValue']
                elif 'blobValue' in field:
                    row[column_name] = field['blobValue']
                else:
                    # Fallback for unknown field types
                    row[column_name] = str(field)
            
            parsed_records.append(row)
        
        return parsed_records
    
    def execute_query(
        self, 
        sql: str, 
        parameters: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return parsed results.
        
        Args:
            sql: SELECT SQL statement
            parameters: List of parameter dictionaries
            
        Returns:
            List of dictionaries representing the query results
            
        Raises:
            DatabaseError: If the query execution fails
        """
        response = self.execute_sql(sql, parameters)
        
        records = response.get('records', [])
        column_metadata = response.get('columnMetadata', [])
        
        return self.parse_records(records, column_metadata)
    
    def execute_update(
        self, 
        sql: str, 
        parameters: List[Dict[str, Any]] = None
    ) -> int:
        """
        Execute an INSERT, UPDATE, or DELETE statement.
        
        Args:
            sql: SQL statement (INSERT, UPDATE, DELETE)
            parameters: List of parameter dictionaries
            
        Returns:
            Number of affected rows
            
        Raises:
            DatabaseError: If the query execution fails
        """
        response = self.execute_sql(sql, parameters)
        return response.get('numberOfRecordsUpdated', 0)
