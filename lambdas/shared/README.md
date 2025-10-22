# Shared Lambda Utilities

This module provides shared utilities for Lambda functions in the healthcare management system, including database access using AWS RDS Data API.

## Database Manager

The `DatabaseManager` class provides a clean interface for executing SQL queries using AWS RDS Data API instead of traditional database connections.

### Key Benefits of RDS Data API

1. **No Connection Management**: No need to manage database connections, connection pools, or handle connection timeouts
2. **Serverless-Friendly**: Perfect for Lambda functions - no persistent connections required
3. **Automatic Scaling**: AWS handles scaling and connection management
4. **Security**: Uses IAM roles and Secrets Manager for authentication
5. **Cost-Effective**: Pay per request, no idle connection costs

### Usage Example

```python
from shared.database import DatabaseManager, DatabaseError
from shared.utils import create_response, create_error_response

# Initialize database manager
db_manager = DatabaseManager()

try:
    # Execute a SELECT query
    sql = "SELECT * FROM patients WHERE status = :status"
    parameters = [
        db_manager.create_parameter('status', 'active', 'string')
    ]
    
    patients = db_manager.execute_query(sql, parameters)
    
    # Execute an INSERT/UPDATE/DELETE
    sql = "INSERT INTO patients (patient_id, name) VALUES (:id, :name)"
    parameters = [
        db_manager.create_parameter('id', patient_id, 'string'),
        db_manager.create_parameter('name', patient_name, 'string')
    ]
    
    affected_rows = db_manager.execute_update(sql, parameters)
    
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    return create_error_response(500, "Database error", e.error_code)
```

### Parameter Types

The RDS Data API supports these parameter types:
- `string`: Text values
- `long`: Integer values  
- `double`: Floating point values
- `boolean`: Boolean values
- `blob`: Binary data

### Transaction Support

```python
# Begin transaction
transaction_id = db_manager.begin_transaction()

try:
    # Execute multiple statements in transaction
    db_manager.execute_sql(sql1, params1, transaction_id)
    db_manager.execute_sql(sql2, params2, transaction_id)
    
    # Commit transaction
    db_manager.commit_transaction(transaction_id)
    
except Exception as e:
    # Rollback on error
    db_manager.rollback_transaction(transaction_id)
    raise
```

## Configuration Manager

The `SSMConfig` class provides easy access to configuration parameters stored in AWS Systems Manager Parameter Store.

### Usage Example

```python
from shared.ssm_config import SSMConfig, SSMConfigError

# Initialize config manager
config = SSMConfig()

try:
    # Get database configuration
    db_config = config.get_database_config()
    cluster_arn = db_config['cluster-arn']
    
    # Get individual parameter
    api_endpoint = config.get_parameter('api/endpoint')
    
    # Get agent configuration
    agent_config = config.get_agent_config('orchestrator')
    
except SSMConfigError as e:
    logger.error(f"Configuration error: {e}")
```

## Utilities

The `utils` module provides common functions for Lambda request/response handling:

- `create_response()`: Create standardized API Gateway responses
- `create_error_response()`: Create standardized error responses  
- `parse_event_body()`: Parse JSON request bodies
- `validate_required_fields()`: Validate required fields in requests
- `validate_pagination_params()`: Handle pagination parameters
- `handle_exceptions()`: Decorator for exception handling

## Database Schema

See `schema.sql` for the expected database schema. Tables will be created automatically when first accessed by the application.

## Configuration Requirements

The Lambda functions expect these SSM parameters to be configured:

- `/healthcare/database/cluster-arn`: RDS Aurora cluster ARN
- `/healthcare/database/secret-arn`: RDS Aurora secret ARN  
- `/healthcare/database/name`: Database name (default: healthcare)

These are automatically created by the `BackendStack` in the CDK infrastructure.
