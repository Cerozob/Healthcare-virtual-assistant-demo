"""
Knowledge Base integration tools for Strands Agents.
Provides tools for querying Bedrock Knowledge Base and managing conversation data.
"""

import boto3
import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import uuid
from botocore.exceptions import ClientError, BotoCoreError
from .config import get_agent_config
from .models import AgentToolResult, DocumentProcessingStatus
from .utils import get_logger, sanitize_for_logging

logger = get_logger(__name__)


class KnowledgeBaseClient:
    """
    Client for Bedrock Knowledge Base integration with document processing and search capabilities.
    """
    
    def __init__(self):
        """Initialize the Knowledge Base client."""
        self.config = get_agent_config()
        self.knowledge_base_id = self.config.knowledge_base_id
        self.supplemental_bucket = self.config.supplemental_data_bucket
        
        # Initialize AWS clients
        self.bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
        self.s3_client = boto3.client('s3')
        self.rds_data_client = boto3.client('rds-data')
        
    async def _execute_database_query(
        self, 
        sql: str, 
        parameters: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute database query for conversation storage.
        
        Args:
            sql: SQL query string
            parameters: Query parameters
            
        Returns:
            List[Dict[str, Any]]: Query results
        """
        try:
            execute_params = {
                'resourceArn': self.config.database_cluster_arn,
                'secretArn': self.config.database_secret_arn,
                'database': 'healthcare',
                'sql': sql
            }
            
            if parameters:
                execute_params['parameters'] = parameters
            
            response = self.rds_data_client.execute_statement(**execute_params)
            
            # Parse results
            records = []
            if response.get('records'):
                column_metadata = response.get('columnMetadata', [])
                for record in response['records']:
                    row = {}
                    for i, field in enumerate(record):
                        column_name = column_metadata[i]['name'] if i < len(column_metadata) else f'col_{i}'
                        
                        # Extract value based on type
                        if 'stringValue' in field:
                            row[column_name] = field['stringValue']
                        elif 'longValue' in field:
                            row[column_name] = field['longValue']
                        elif 'doubleValue' in field:
                            row[column_name] = field['doubleValue']
                        elif 'booleanValue' in field:
                            row[column_name] = field['booleanValue']
                        elif 'isNull' in field:
                            row[column_name] = None
                        else:
                            row[column_name] = str(field)
                    
                    records.append(row)
            
            return records
            
        except Exception as e:
            logger.error(f"Database query error: {str(e)}")
            raise


# Initialize Knowledge Base client
kb_client = KnowledgeBaseClient()


async def search_knowledge_base(
    query: str,
    max_results: int = 5,
    filter_criteria: Optional[Dict[str, Any]] = None
) -> AgentToolResult:
    """
    Search Bedrock Knowledge Base for relevant documents.
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
        filter_criteria: Optional filters for search
        
    Returns:
        AgentToolResult: Search results or error
    """
    start_time = datetime.utcnow()
    
    try:
        logger.info("Searching knowledge base")
        
        # Prepare search request
        search_params = {
            'knowledgeBaseId': kb_client.knowledge_base_id,
            'retrievalQuery': {
                'text': query
            },
            'retrievalConfiguration': {
                'vectorSearchConfiguration': {
                    'numberOfResults': max_results
                }
            }
        }
        
        # Add filter if provided
        if filter_criteria:
            search_params['retrievalConfiguration']['vectorSearchConfiguration']['filter'] = filter_criteria
        
        # Execute search
        response = kb_client.bedrock_agent_runtime.retrieve(**search_params)
        
        # Process results
        results = []
        for result in response.get('retrievalResults', []):
            content = result.get('content', {})
            metadata = result.get('metadata', {})
            
            processed_result = {
                'content': content.get('text', ''),
                'score': result.get('score', 0.0),
                'source': metadata.get('source', ''),
                'document_id': metadata.get('document_id', ''),
                'metadata': metadata
            }
            results.append(processed_result)
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return AgentToolResult(
            tool_name="search_knowledge_base",
            success=True,
            result={
                'query': query,
                'results': results,
                'total_results': len(results)
            },
            execution_time_ms=execution_time
        )
        
    except ClientError as e:
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        logger.error(f"Knowledge base search error: {error_code} - {str(e)}")
        
        return AgentToolResult(
            tool_name="search_knowledge_base",
            success=False,
            error_message=f"Knowledge base error: {error_code} - {str(e)}",
            execution_time_ms=execution_time
        )
        
    except Exception as e:
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        logger.error(f"Knowledge base search error: {str(e)}")
        
        return AgentToolResult(
            tool_name="search_knowledge_base",
            success=False,
            error_message=f"Search error: {str(e)}",
            execution_time_ms=execution_time
        )


async def store_conversation(
    session_id: str,
    patient_id: Optional[str],
    medic_id: Optional[str],
    conversation_data: Dict[str, Any],
    notes: Optional[str] = None
) -> AgentToolResult:
    """
    Store conversation history and doctor's notes in the database.
    
    Args:
        session_id: Session identifier
        patient_id: Patient identifier (if applicable)
        medic_id: Medic identifier (if applicable)
        conversation_data: Conversation messages and metadata
        notes: Doctor's notes or summary
        
    Returns:
        AgentToolResult: Storage result
    """
    start_time = datetime.utcnow()
    
    try:
        logger.info("Storing conversation data")
        
        # Sanitize conversation data for storage (remove PII from logs only)
        sanitized_data = sanitize_for_logging(conversation_data)
        logger.debug(f"Storing conversation: {sanitized_data}")
        
        # Generate conversation record ID
        conversation_id = str(uuid.uuid4())
        
        # Prepare SQL parameters
        parameters = [
            {'name': 'conversation_id', 'value': {'stringValue': conversation_id}},
            {'name': 'session_id', 'value': {'stringValue': session_id}},
            {'name': 'conversation_data', 'value': {'stringValue': json.dumps(conversation_data)}},
            {'name': 'created_at', 'value': {'stringValue': datetime.utcnow().isoformat()}}
        ]
        
        if patient_id:
            parameters.append({'name': 'patient_id', 'value': {'stringValue': patient_id}})
        
        if medic_id:
            parameters.append({'name': 'medic_id', 'value': {'stringValue': medic_id}})
        
        if notes:
            parameters.append({'name': 'notes', 'value': {'stringValue': notes}})
        
        # Build SQL query dynamically based on available fields
        columns = ['conversation_id', 'session_id', 'conversation_data', 'created_at']
        placeholders = [':conversation_id', ':session_id', ':conversation_data', ':created_at']
        
        if patient_id:
            columns.append('patient_id')
            placeholders.append(':patient_id')
        
        if medic_id:
            columns.append('medic_id')
            placeholders.append(':medic_id')
        
        if notes:
            columns.append('notes')
            placeholders.append(':notes')
        
        sql = f"""
        INSERT INTO conversation_history ({', '.join(columns)})
        VALUES ({', '.join(placeholders)})
        """
        
        # Execute query
        await kb_client._execute_database_query(sql, parameters)
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return AgentToolResult(
            tool_name="store_conversation",
            success=True,
            result={
                'conversation_id': conversation_id,
                'session_id': session_id,
                'stored_at': datetime.utcnow().isoformat()
            },
            execution_time_ms=execution_time
        )
        
    except Exception as e:
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        logger.error(f"Error storing conversation: {str(e)}")
        
        return AgentToolResult(
            tool_name="store_conversation",
            success=False,
            error_message=f"Storage error: {str(e)}",
            execution_time_ms=execution_time
        )


async def process_document_upload(
    document_content: bytes,
    filename: str,
    content_type: str,
    session_id: str
) -> AgentToolResult:
    """
    Process document upload for immediate analysis and async ingestion.
    
    Args:
        document_content: Document binary content
        filename: Original filename
        content_type: MIME content type
        session_id: Current session ID
        
    Returns:
        AgentToolResult: Processing result with immediate analysis
    """
    start_time = datetime.utcnow()
    
    try:
        logger.info(f"Processing document upload: {filename}")
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Upload to S3 for async processing
        s3_key = f"documents/{session_id}/{document_id}/{filename}"
        
        kb_client.s3_client.put_object(
            Bucket=kb_client.supplemental_bucket,
            Key=s3_key,
            Body=document_content,
            ContentType=content_type,
            Metadata={
                'session_id': session_id,
                'document_id': document_id,
                'original_filename': filename,
                'upload_timestamp': datetime.utcnow().isoformat()
            }
        )
        
        # Immediate content analysis for supported formats
        immediate_content = None
        if content_type == 'text/plain':
            immediate_content = document_content.decode('utf-8')
        elif content_type == 'application/json':
            try:
                immediate_content = json.loads(document_content.decode('utf-8'))
            except json.JSONDecodeError:
                immediate_content = "JSON document uploaded (parsing error)"
        
        # Store document metadata in database
        parameters = [
            {'name': 'document_id', 'value': {'stringValue': document_id}},
            {'name': 'session_id', 'value': {'stringValue': session_id}},
            {'name': 'filename', 'value': {'stringValue': filename}},
            {'name': 'content_type', 'value': {'stringValue': content_type}},
            {'name': 's3_key', 'value': {'stringValue': s3_key}},
            {'name': 'status', 'value': {'stringValue': 'uploaded'}},
            {'name': 'created_at', 'value': {'stringValue': datetime.utcnow().isoformat()}}
        ]
        
        sql = """
        INSERT INTO document_uploads 
        (document_id, session_id, filename, content_type, s3_key, status, created_at)
        VALUES (:document_id, :session_id, :filename, :content_type, :s3_key, :status, :created_at)
        """
        
        await kb_client._execute_database_query(sql, parameters)
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        result = {
            'document_id': document_id,
            'filename': filename,
            'status': 'uploaded',
            's3_location': f"s3://{kb_client.supplemental_bucket}/{s3_key}",
            'immediate_content': immediate_content,
            'async_processing': True,
            'message': 'Document uploaded successfully. Processing for knowledge base ingestion...'
        }
        
        return AgentToolResult(
            tool_name="process_document_upload",
            success=True,
            result=result,
            execution_time_ms=execution_time
        )
        
    except Exception as e:
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        logger.error(f"Error processing document upload: {str(e)}")
        
        return AgentToolResult(
            tool_name="process_document_upload",
            success=False,
            error_message=f"Upload processing error: {str(e)}",
            execution_time_ms=execution_time
        )


async def get_document_status(document_id: str) -> AgentToolResult:
    """
    Get document processing status.
    
    Args:
        document_id: Document identifier
        
    Returns:
        AgentToolResult: Document status information
    """
    start_time = datetime.utcnow()
    
    try:
        logger.info(f"Getting document status: {document_id}")
        
        parameters = [
            {'name': 'document_id', 'value': {'stringValue': document_id}}
        ]
        
        sql = """
        SELECT document_id, filename, status, created_at, updated_at, error_message
        FROM document_uploads
        WHERE document_id = :document_id
        """
        
        results = await kb_client._execute_database_query(sql, parameters)
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        if results:
            document_info = results[0]
            return AgentToolResult(
                tool_name="get_document_status",
                success=True,
                result=document_info,
                execution_time_ms=execution_time
            )
        else:
            return AgentToolResult(
                tool_name="get_document_status",
                success=False,
                error_message="Document not found",
                execution_time_ms=execution_time
            )
        
    except Exception as e:
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        logger.error(f"Error getting document status: {str(e)}")
        
        return AgentToolResult(
            tool_name="get_document_status",
            success=False,
            error_message=f"Status retrieval error: {str(e)}",
            execution_time_ms=execution_time
        )


async def retrieve_conversation_history(
    session_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    medic_id: Optional[str] = None,
    limit: int = 10
) -> AgentToolResult:
    """
    Retrieve conversation history with optional filters.
    
    Args:
        session_id: Filter by session ID
        patient_id: Filter by patient ID
        medic_id: Filter by medic ID
        limit: Maximum number of records
        
    Returns:
        AgentToolResult: Conversation history
    """
    start_time = datetime.utcnow()
    
    try:
        logger.info("Retrieving conversation history")
        
        # Build query with filters
        where_conditions = []
        parameters = [
            {'name': 'limit', 'value': {'longValue': limit}}
        ]
        
        if session_id:
            where_conditions.append("session_id = :session_id")
            parameters.append({'name': 'session_id', 'value': {'stringValue': session_id}})
        
        if patient_id:
            where_conditions.append("patient_id = :patient_id")
            parameters.append({'name': 'patient_id', 'value': {'stringValue': patient_id}})
        
        if medic_id:
            where_conditions.append("medic_id = :medic_id")
            parameters.append({'name': 'medic_id', 'value': {'stringValue': medic_id}})
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        sql = f"""
        SELECT conversation_id, session_id, patient_id, medic_id, 
               conversation_data, notes, created_at
        FROM conversation_history
        {where_clause}
        ORDER BY created_at DESC
        LIMIT :limit
        """
        
        results = await kb_client._execute_database_query(sql, parameters)
        
        # Parse conversation data
        conversations = []
        for record in results:
            conversation = record.copy()
            if conversation.get('conversation_data'):
                try:
                    conversation['conversation_data'] = json.loads(conversation['conversation_data'])
                except json.JSONDecodeError:
                    conversation['conversation_data'] = {}
            conversations.append(conversation)
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return AgentToolResult(
            tool_name="retrieve_conversation_history",
            success=True,
            result={
                'conversations': conversations,
                'total_retrieved': len(conversations)
            },
            execution_time_ms=execution_time
        )
        
    except Exception as e:
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        logger.error(f"Error retrieving conversation history: {str(e)}")
        
        return AgentToolResult(
            tool_name="retrieve_conversation_history",
            success=False,
            error_message=f"Retrieval error: {str(e)}",
            execution_time_ms=execution_time
        )


async def notify_document_ingestion_complete(
    document_id: str,
    success: bool,
    message: str
) -> AgentToolResult:
    """
    Update document status after async ingestion completion.
    
    Args:
        document_id: Document identifier
        success: Whether ingestion was successful
        message: Status message
        
    Returns:
        AgentToolResult: Update result
    """
    start_time = datetime.utcnow()
    
    try:
        logger.info(f"Updating document ingestion status: {document_id}")
        
        status = "completed" if success else "failed"
        
        parameters = [
            {'name': 'document_id', 'value': {'stringValue': document_id}},
            {'name': 'status', 'value': {'stringValue': status}},
            {'name': 'message', 'value': {'stringValue': message}},
            {'name': 'updated_at', 'value': {'stringValue': datetime.utcnow().isoformat()}}
        ]
        
        sql = """
        UPDATE document_uploads
        SET status = :status, error_message = :message, updated_at = :updated_at
        WHERE document_id = :document_id
        """
        
        await kb_client._execute_database_query(sql, parameters)
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return AgentToolResult(
            tool_name="notify_document_ingestion_complete",
            success=True,
            result={
                'document_id': document_id,
                'status': status,
                'message': message,
                'updated_at': datetime.utcnow().isoformat()
            },
            execution_time_ms=execution_time
        )
        
    except Exception as e:
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        logger.error(f"Error updating document status: {str(e)}")
        
        return AgentToolResult(
            tool_name="notify_document_ingestion_complete",
            success=False,
            error_message=f"Status update error: {str(e)}",
            execution_time_ms=execution_time
        )
