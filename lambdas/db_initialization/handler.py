import json
import boto3
import logging
import uuid
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def wait_for_database_ready(rds_data, cluster_arn: str, secret_arn: str, database_name: str, max_retries: int = 5):
    """
    Quick check that database is ready to accept connections.
    Since this is triggered by EventBridge after RDS events, we only need a short wait.
    """
    for attempt in range(max_retries):
        try:
            # Simple query to test database readiness
            rds_data.execute_statement(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database=database_name,
                sql="SELECT 1;"
            )
            logger.info(f"Database ready after {attempt + 1} attempts")
            return
        except Exception as e:
            error_str = str(e)
            if any(phrase in error_str for phrase in ["DatabaseResumingException", "resuming", "Cannot find DBInstance", "DatabaseNotFoundException"]):
                wait_time = 5
                logger.info(f"Database not ready yet, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                logger.error(f"Unexpected error checking database readiness: {e}")
                raise

    raise Exception(f"Database did not become ready after {max_retries} attempts")


def lambda_handler(event, context):
    """
    Lambda handler for database initialization.
    Can be triggered by:
    1. EventBridge RDS events (RDS-EVENT-0005 or RDS-EVENT-0170)
    2. Manual invocation for testing
    """
    try:
        logger.info(f"Database initialization triggered. Event: {json.dumps(event)}")
        
        # Get database connection details from environment variables
        cluster_arn = os.environ.get('DATABASE_CLUSTER_ARN')
        secret_arn = os.environ.get('DATABASE_SECRET_ARN')
        database_name = os.environ.get('DATABASE_NAME', 'healthcare')
        table_name = os.environ.get('TABLE_NAME', 'ab2_knowledge_base')
        
        if not all([cluster_arn, secret_arn]):
            raise ValueError("Missing required environment variables: DATABASE_CLUSTER_ARN, DATABASE_SECRET_ARN")
        
        # Check if this is an EventBridge event
        event_source = event.get('source', '')
        is_rds_event = event_source == 'aws.rds'
        
        if is_rds_event:
            event_id = event.get('detail', {}).get('EventID', '')
            source_arn = event.get('detail', {}).get('SourceArn', '')
            logger.info(f"RDS Event received: {event_id} from {source_arn}")
            
            # Only process if it's our cluster
            if cluster_arn not in source_arn:
                logger.info(f"Event is not for our cluster, ignoring")
                return {
                    'statusCode': 200,
                    'body': json.dumps({'message': 'Event not for this cluster'})
                }
        
        # Use RDS Data API
        rds_data = boto3.client('rds-data')

        # Wait for database to be ready (shorter wait since EventBridge already waited)
        wait_for_database_ready(rds_data, cluster_arn, secret_arn, database_name, max_retries=5)

        # Enable pgvector extension with retry logic
        try:
            rds_data.execute_statement(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database=database_name,
                sql="CREATE EXTENSION IF NOT EXISTS vector;"
            )
            logger.info("pgvector extension enabled")
        except Exception as e:
            logger.warning(f"pgvector extension may already exist: {e}")

        # Create all healthcare system tables
        create_healthcare_tables(rds_data, cluster_arn, secret_arn, database_name)

        # Create Bedrock integration schema and user
        setup_bedrock_integration(rds_data, cluster_arn, secret_arn, database_name)

        # Create the knowledge base table
        create_knowledge_base_table(rds_data, cluster_arn, secret_arn, database_name, table_name)

        logger.info(f"Successfully initialized database with tables and indexes")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Database initialization completed successfully',
                'table_name': table_name
            })
        }

    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }


def setup_bedrock_integration(rds_data, cluster_arn: str, secret_arn: str, database_name: str):
    """Create Bedrock integration schema and user following AWS best practices."""
    
    try:
        # Create bedrock_integration schema
        rds_data.execute_statement(
            resourceArn=cluster_arn,
            secretArn=secret_arn,
            database=database_name,
            sql="CREATE SCHEMA IF NOT EXISTS bedrock_integration;"
        )
        logger.info("Created bedrock_integration schema")
    except Exception as e:
        if "already exists" in str(e).lower():
            logger.info("Bedrock schema already exists")
        else:
            logger.error(f"Failed to create bedrock schema: {e}")

    try:
        # Create bedrock_user role
        rds_data.execute_statement(
            resourceArn=cluster_arn,
            secretArn=secret_arn,
            database=database_name,
            sql="CREATE ROLE bedrock_user LOGIN;"
        )
        logger.info("Created bedrock_user role")
    except Exception as e:
        if "already exists" in str(e).lower():
            logger.info("Bedrock user already exists")
        else:
            logger.error(f"Failed to create bedrock user: {e}")

    try:
        # Set password for bedrock_user using the dedicated secret
        bedrock_secret_arn = os.environ.get('BEDROCK_USER_SECRET_ARN')
        if bedrock_secret_arn:
            secretsmanager = boto3.client('secretsmanager')
            bedrock_secret_response = secretsmanager.get_secret_value(
                SecretId=bedrock_secret_arn)
            bedrock_secret_data = json.loads(
                bedrock_secret_response['SecretString'])
            bedrock_password = bedrock_secret_data['password']

            rds_data.execute_statement(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database=database_name,
                sql=f"ALTER USER bedrock_user PASSWORD '{bedrock_password}';"
            )
            logger.info("Set password for bedrock_user using dedicated secret")
        else:
            logger.warning("BEDROCK_USER_SECRET_ARN not provided, skipping password setup")
    except Exception as e:
        logger.warning(f"Failed to set bedrock_user password: {e}")

    try:
        # Grant permissions to bedrock_user
        rds_data.execute_statement(
            resourceArn=cluster_arn,
            secretArn=secret_arn,
            database=database_name,
            sql="GRANT ALL ON SCHEMA bedrock_integration TO bedrock_user;"
        )
        logger.info("Granted bedrock_integration schema permissions to bedrock_user")

        rds_data.execute_statement(
            resourceArn=cluster_arn,
            secretArn=secret_arn,
            database=database_name,
            sql="GRANT USAGE ON SCHEMA public TO bedrock_user;"
        )
        logger.info("Granted public schema usage to bedrock_user")

        rds_data.execute_statement(
            resourceArn=cluster_arn,
            secretArn=secret_arn,
            database=database_name,
            sql="GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO bedrock_user;"
        )
        logger.info("Granted table permissions on public schema to bedrock_user")

        rds_data.execute_statement(
            resourceArn=cluster_arn,
            secretArn=secret_arn,
            database=database_name,
            sql="ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO bedrock_user;"
        )
        logger.info("Granted default privileges on future tables to bedrock_user")

        rds_data.execute_statement(
            resourceArn=cluster_arn,
            secretArn=secret_arn,
            database=database_name,
            sql="GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO bedrock_user;"
        )
        logger.info("Granted sequence usage to bedrock_user")

        rds_data.execute_statement(
            resourceArn=cluster_arn,
            secretArn=secret_arn,
            database=database_name,
            sql="ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE ON SEQUENCES TO bedrock_user;"
        )
        logger.info("Granted default sequence privileges to bedrock_user")

    except Exception as e:
        logger.warning(f"Failed to grant permissions: {e}")


def create_knowledge_base_table(rds_data, cluster_arn: str, secret_arn: str, database_name: str, table_name: str):
    """Create the knowledge base table following AWS documentation structure."""
    
    try:
        # First check if vector extension is available
        vector_check = rds_data.execute_statement(
            resourceArn=cluster_arn,
            secretArn=secret_arn,
            database=database_name,
            sql="SELECT 1 FROM pg_extension WHERE extname = 'vector';"
        )

        if not vector_check.get('records'):
            logger.error("Vector extension is not installed - knowledge base table creation will fail")
            raise Exception("Vector extension not available")

        logger.info("Vector extension confirmed available")

        # Check if table exists with wrong schema and drop it
        try:
            check_old_columns = rds_data.execute_statement(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database=database_name,
                sql=f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}' AND column_name IN ('id', 'embedding', 'chunks');"
            )

            check_pk_type = rds_data.execute_statement(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database=database_name,
                sql=f"SELECT data_type FROM information_schema.columns WHERE table_name = '{table_name}' AND column_name = 'pk' AND data_type != 'uuid';"
            )

            if check_old_columns.get('records') or check_pk_type.get('records'):
                logger.info(f"Table {table_name} exists with incorrect schema, dropping and recreating")
                rds_data.execute_statement(
                    resourceArn=cluster_arn,
                    secretArn=secret_arn,
                    database=database_name,
                    sql=f"DROP TABLE IF EXISTS {table_name};"
                )
                logger.info(f"Dropped existing table {table_name} with incorrect schema")
        except Exception as e:
            logger.info(f"Table schema check failed (table may not exist): {e}")

        create_table_sql = f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            pk uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            vector vector(1024),
            text text,
            metadata jsonb,
            custom_metadata jsonb
        );
        '''

        logger.info(f"Creating knowledge base table with SQL: {create_table_sql}")

        rds_data.execute_statement(
            resourceArn=cluster_arn,
            secretArn=secret_arn,
            database=database_name,
            sql=create_table_sql
        )
        logger.info(f"Knowledge base table {table_name} created successfully")

        # Verify table was created with correct columns
        verify_sql = f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}' ORDER BY ordinal_position;"
        verify_result = rds_data.execute_statement(
            resourceArn=cluster_arn,
            secretArn=secret_arn,
            database=database_name,
            sql=verify_sql
        )

        columns = []
        for record in verify_result.get('records', []):
            column_name = record[0].get('stringValue', '')
            data_type = record[1].get('stringValue', '')
            columns.append(f"{column_name}({data_type})")

        logger.info(f"Knowledge base table columns verified: {', '.join(columns)}")

        # Grant specific permissions on the knowledge base table to bedrock_user
        try:
            rds_data.execute_statement(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database=database_name,
                sql=f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table_name} TO bedrock_user;"
            )
            logger.info(f"Granted permissions on {table_name} to bedrock_user")
        except Exception as e:
            logger.warning(f"Failed to grant table permissions: {e}")

        # Create required indexes as per AWS documentation
        # 1. HNSW index for vector similarity search (required)
        try:
            vector_index_sql = f"CREATE INDEX IF NOT EXISTS {table_name}_vector_hnsw_idx ON {table_name} USING hnsw (vector vector_cosine_ops);"
            rds_data.execute_statement(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database=database_name,
                sql=vector_index_sql
            )
            logger.info("HNSW vector index created (required)")
        except Exception as e:
            logger.warning(f"Failed to create vector index: {e}")

        # 2. GIN index for text search (required)
        try:
            text_index_sql = f"CREATE INDEX IF NOT EXISTS {table_name}_text_gin_idx ON {table_name} USING gin (to_tsvector('simple', text));"
            rds_data.execute_statement(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database=database_name,
                sql=text_index_sql
            )
            logger.info("GIN text index created (required)")
        except Exception as e:
            logger.warning(f"Failed to create text index: {e}")

        # 3. GIN index for custom metadata (optional but recommended)
        try:
            metadata_index_sql = f"CREATE INDEX IF NOT EXISTS {table_name}_custom_metadata_gin_idx ON {table_name} USING gin (custom_metadata);"
            rds_data.execute_statement(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database=database_name,
                sql=metadata_index_sql
            )
            logger.info("GIN custom metadata index created (optional)")
        except Exception as e:
            logger.warning(f"Failed to create custom metadata index: {e}")

    except Exception as e:
        if "type \"vector\" does not exist" in str(e) or "does not exist" in str(e):
            logger.error(f"Vector extension not available. Knowledge base table creation failed: {e}")
            raise
        else:
            logger.warning(f"Knowledge base table creation failed: {e}")


def create_healthcare_tables(rds_data, cluster_arn: str, secret_arn: str, database_name: str):
    """Create all healthcare system tables by reading and parsing the schema.sql file."""

    try:
        # Read the schema.sql file from the shared module
        schema_content = None

        # Try different possible paths for the schema file in Lambda environment
        possible_paths = [
            "/var/task/shared/schema.sql",    # Lambda function package
            "shared/schema.sql",              # Relative path
            "/opt/python/shared/schema.sql"   # Lambda layer (if used)
        ]

        for path in possible_paths:
            try:
                with open(path, 'r') as f:
                    schema_content = f.read()
                logger.info(f"Successfully read schema from: {path}")
                break
            except FileNotFoundError:
                logger.debug(f"Schema file not found at: {path}")
                continue

        if not schema_content:
            logger.error(
                "Could not find schema.sql file in any expected location")
            raise FileNotFoundError("schema.sql not found")

        # Run schema migrations first (before creating new tables)
        run_schema_migrations(rds_data, cluster_arn, secret_arn, database_name)

        # Parse the schema content into individual SQL statements
        statements = parse_sql_statements(schema_content)

        logger.info(f"Parsed {len(statements)} SQL statements from schema.sql")

        # Separate CREATE TABLE and CREATE INDEX statements
        table_statements = []
        index_statements = []

        for statement in statements:
            if not statement.strip() or statement.strip().startswith('--'):
                continue

            statement_upper = statement.strip().upper()
            if statement_upper.startswith('CREATE TABLE'):
                table_statements.append(statement)
            elif statement_upper.startswith('CREATE INDEX'):
                index_statements.append(statement)
            else:
                # Other statements like extensions
                table_statements.append(statement)

        # Execute table creation first
        executed_count = 0
        logger.info(f"Creating {len(table_statements)} tables...")

        for i, statement in enumerate(table_statements, 1):
            try:
                logger.debug(
                    f"Executing table statement {i}: {statement[:100]}...")

                rds_data.execute_statement(
                    resourceArn=cluster_arn,
                    secretArn=secret_arn,
                    database=database_name,
                    sql=statement
                )

                executed_count += 1
                logger.info(f"Successfully executed table statement {i}")

            except Exception as e:
                error_msg = str(e).lower()
                if any(phrase in error_msg for phrase in ["already exists", "duplicate"]):
                    logger.info(
                        f"Table statement {i} - object already exists, skipping")
                elif "type \"vector\" does not exist" in error_msg:
                    logger.warning(
                        f"Vector type not available, skipping knowledge base table")
                else:
                    logger.error(f"Failed to execute table statement {i}: {e}")
                    logger.error(f"Statement was: {statement}")
                    # Continue with other statements
                    continue

        # Execute index creation after tables
        logger.info(f"Creating {len(index_statements)} indexes...")

        for i, statement in enumerate(index_statements, 1):
            try:
                logger.debug(
                    f"Executing index statement {i}: {statement[:100]}...")

                rds_data.execute_statement(
                    resourceArn=cluster_arn,
                    secretArn=secret_arn,
                    database=database_name,
                    sql=statement
                )

                executed_count += 1
                logger.info(f"Successfully executed index statement {i}")

            except Exception as e:
                error_msg = str(e).lower()
                if any(phrase in error_msg for phrase in ["already exists", "duplicate"]):
                    logger.info(
                        f"Index statement {i} - object already exists, skipping")
                elif "does not exist" in error_msg:
                    logger.warning(
                        f"Index statement {i} - table doesn't exist yet, skipping")
                else:
                    logger.error(f"Failed to execute index statement {i}: {e}")
                    logger.error(f"Statement was: {statement}")
                    # Continue with other statements
                    continue

        logger.info(
            f"Healthcare tables creation completed - executed {executed_count} statements")

        # Run migrations again after table creation (for new deployments)
        # This ensures that if tables were just created, they get the latest schema
        run_post_creation_migrations(rds_data, cluster_arn, secret_arn, database_name)

    except Exception as e:
        logger.error(f"Failed to create healthcare tables: {e}")
        raise


def run_post_creation_migrations(rds_data, cluster_arn: str, secret_arn: str, database_name: str):
    """Run migrations after table creation for new deployments."""
    
    logger.info("Running post-creation schema migrations...")
    
    try:
        # Check if patients table exists and add cedula if missing
        check_table_sql = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name = 'patients';
        """
        
        response = rds_data.execute_statement(
            resourceArn=cluster_arn,
            secretArn=secret_arn,
            database=database_name,
            sql=check_table_sql
        )
        
        if response.get('records'):
            # Table exists, check for cedula field
            check_cedula_sql = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'patients' 
            AND column_name = 'cedula';
            """
            
            cedula_response = rds_data.execute_statement(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database=database_name,
                sql=check_cedula_sql
            )
            
            if not cedula_response.get('records'):
                logger.info("Adding cedula field to existing patients table...")
                
                add_cedula_sql = """
                ALTER TABLE patients 
                ADD COLUMN cedula VARCHAR(50) UNIQUE;
                """
                
                rds_data.execute_statement(
                    resourceArn=cluster_arn,
                    secretArn=secret_arn,
                    database=database_name,
                    sql=add_cedula_sql
                )
                
                # Add index
                add_cedula_index_sql = """
                CREATE INDEX IF NOT EXISTS idx_patients_cedula ON patients(cedula);
                """
                
                rds_data.execute_statement(
                    resourceArn=cluster_arn,
                    secretArn=secret_arn,
                    database=database_name,
                    sql=add_cedula_index_sql
                )
                
                logger.info("Successfully added cedula field and index")
            else:
                logger.info("Cedula field already exists")
        
        logger.info("Post-creation migrations completed")
        
    except Exception as e:
        logger.warning(f"Post-creation migration failed (non-critical): {e}")
        # Don't raise - this is non-critical


def run_schema_migrations(rds_data, cluster_arn: str, secret_arn: str, database_name: str):
    """Run schema migrations to update existing tables with new fields."""
    
    logger.info("Running schema migrations...")
    
    try:
        # Migration 1: Add cedula field to patients table if it doesn't exist
        check_cedula_sql = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'patients' 
        AND column_name = 'cedula';
        """
        
        response = rds_data.execute_statement(
            resourceArn=cluster_arn,
            secretArn=secret_arn,
            database=database_name,
            sql=check_cedula_sql
        )
        
        if not response.get('records'):
            # Cedula column doesn't exist, add it
            logger.info("Adding cedula field to patients table...")
            
            add_cedula_sql = """
            ALTER TABLE patients 
            ADD COLUMN cedula VARCHAR(50) UNIQUE;
            """
            
            rds_data.execute_statement(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database=database_name,
                sql=add_cedula_sql
            )
            
            logger.info("Successfully added cedula field to patients table")
            
            # Add index for the new field
            add_cedula_index_sql = """
            CREATE INDEX IF NOT EXISTS idx_patients_cedula ON patients(cedula);
            """
            
            rds_data.execute_statement(
                resourceArn=cluster_arn,
                secretArn=secret_arn,
                database=database_name,
                sql=add_cedula_index_sql
            )
            
            logger.info("Successfully created index on cedula field")
        else:
            logger.info("Cedula field already exists in patients table")
            
        # Add more migrations here as needed in the future
        # Migration 2: Example for future use
        # check_future_field_sql = "SELECT ..."
        # if not response.get('records'):
        #     logger.info("Adding future field...")
        #     # Add migration logic
        
        logger.info("Schema migrations completed successfully")
        
    except Exception as e:
        # Check if the error is because the patients table doesn't exist yet
        if "relation \"patients\" does not exist" in str(e).lower():
            logger.info("Patients table doesn't exist yet, migrations will run after table creation")
        else:
            logger.error(f"Schema migration failed: {e}")
            # Don't raise the exception - let table creation continue
            # This ensures that new deployments still work even if migrations fail


def parse_sql_statements(sql_content: str) -> list:
    """Parse SQL content into individual executable statements."""

    statements = []
    current_statement = []
    in_comment_block = False

    for line in sql_content.split('\n'):
        # Handle multi-line comments
        if '/*' in line:
            in_comment_block = True
        if '*/' in line:
            in_comment_block = False
            continue
        if in_comment_block:
            continue

        # Remove inline comments (-- comments after SQL code)
        if '--' in line:
            line = line.split('--')[0]
        
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Add line to current statement
        current_statement.append(line)

        # If line ends with semicolon, it's the end of a statement
        if line.endswith(';'):
            statement = ' '.join(current_statement)
            if statement.strip():
                statements.append(statement)
            current_statement = []

    # Handle any remaining statement without semicolon
    if current_statement:
        statement = ' '.join(current_statement)
        if statement.strip():
            statements.append(statement)

    return statements





















