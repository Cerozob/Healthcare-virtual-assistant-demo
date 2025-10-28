#!/usr/bin/env python3
"""
Migration script to add cedula field to patients table.
This script safely adds the new field without affecting existing data.
"""

import boto3
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_database_config() -> Dict[str, str]:
    """Get database configuration from SSM parameters."""
    ssm = boto3.client('ssm')
    
    try:
        response = ssm.get_parameters_by_path(
            Path='/healthcare/database/',
            Recursive=True
        )
        
        params = {param['Name'].split('/')[-1]: param['Value'] 
                 for param in response['Parameters']}
        
        return {
            'cluster_arn': params.get('cluster-arn'),
            'secret_arn': params.get('secret-arn'),
            'database_name': params.get('name', 'healthcare')
        }
    except Exception as e:
        logger.error(f"Failed to get database configuration: {e}")
        raise


def add_cedula_field():
    """Add cedula field to patients table if it doesn't exist."""
    rds_data = boto3.client('rds-data')
    config = get_database_config()
    
    # Check if cedula column already exists
    check_column_sql = """
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'patients' 
    AND column_name = 'cedula';
    """
    
    try:
        # Check if column exists
        response = rds_data.execute_statement(
            resourceArn=config['cluster_arn'],
            secretArn=config['secret_arn'],
            database=config['database_name'],
            sql=check_column_sql
        )
        
        if response['records']:
            logger.info("Cedula column already exists in patients table")
            return
        
        # Add the column
        add_column_sql = """
        ALTER TABLE patients 
        ADD COLUMN cedula VARCHAR(50) UNIQUE;
        """
        
        logger.info("Adding cedula column to patients table...")
        rds_data.execute_statement(
            resourceArn=config['cluster_arn'],
            secretArn=config['secret_arn'],
            database=config['database_name'],
            sql=add_column_sql
        )
        
        # Add index for performance
        add_index_sql = """
        CREATE INDEX IF NOT EXISTS idx_patients_cedula ON patients(cedula);
        """
        
        logger.info("Creating index on cedula column...")
        rds_data.execute_statement(
            resourceArn=config['cluster_arn'],
            secretArn=config['secret_arn'],
            database=config['database_name'],
            sql=add_index_sql
        )
        
        logger.info("Successfully added cedula field to patients table")
        
    except Exception as e:
        logger.error(f"Failed to add cedula field: {e}")
        raise


if __name__ == "__main__":
    add_cedula_field()
