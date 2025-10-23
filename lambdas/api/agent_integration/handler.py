"""
Agent Integration API Lambda Function.
Handles direct agent queries, health checks, and monitoring.
Consolidates functionality from both Node.js and Python agent integration implementations.

Endpoints:
- POST /agent/query - Direct agent query for testing
- GET /agent/health - Health check for all agents and services
- GET /agent/metrics - Agent interaction metrics
"""

import json
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError
from shared.database import DatabaseManager, DatabaseError
from shared.ssm_config import SSMConfig
from shared.utils import (
    create_response, create_error_response, parse_event_body,
    extract_path_parameters, extract_query_parameters, validate_required_fields,
    handle_exceptions, get_current_timestamp
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients and managers
db_manager = DatabaseManager()
ssm_config = SSMConfig()
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
cloudwatch = boto3.client('cloudwatch')


@handle_exceptions
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for agent integration endpoints.
    Routes to appropriate handler based on HTTP method and path.
    """
    # Handle both API Gateway v1 and v2 event formats
    http_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method', '')
    path = event.get('path') or event.get('requestContext', {}).get('http', {}).get('path', '')
    
    # Log the event for debugging
    logger.info(f"Received request: method={http_method}, path={path}")
    
    # Normalize path by removing stage prefix if present
    normalized_path = path
    if path.startswith('/v1/'):
        normalized_path = path[3:]  # Remove '/v1' prefix
    
    # Route to appropriate handler
    if normalized_path == '/agent/query' or normalized_path.endswith('/agent/query'):
        if http_method == 'POST':
            return handle_agent_query(event)
    elif normalized_path == '/agent/health' or normalized_path.endswith('/agent/health'):
        if http_method == 'GET':
            return handle_health_check(event)
    elif normalized_path == '/agent/metrics' or normalized_path.endswith('/agent/metrics'):
        if http_method == 'GET':
            return handle_get_metrics(event)
    elif normalized_path == '/agent' or normalized_path.endswith('/agent'):
        if http_method == 'GET':
            return handle_agent_info(event)
        elif http_method == 'POST':
            return handle_agent_query(event)
    
    return create_error_response(404, "Endpoint not found")


def handle_agent_info(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle GET /agent - Get agent system information.
    
    Returns:
        Agent system information and status
    """
    try:
        # Get basic agent configuration info
        agent_types = ['orchestrator', 'scheduling', 'information']
        agent_info = {}
        
        for agent_type in agent_types:
            agent_config = get_agent_config(agent_type)
            agent_info[agent_type] = {
                'configured': bool(agent_config['agent_id'] and agent_config['alias_id']),
                'agent_id': agent_config['agent_id'] if agent_config['agent_id'] else 'Not configured',
                'alias_id': agent_config['alias_id'] if agent_config['alias_id'] else 'Not configured'
            }
        
        return create_response(200, {
            'system': 'Healthcare Agent Integration',
            'version': '1.0.0',
            'agents': agent_info,
            'endpoints': {
                'query': '/agent/query',
                'health': '/agent/health',
                'metrics': '/agent/metrics'
            },
            'timestamp': get_current_timestamp()
        })
        
    except Exception as e:
        logger.error(f"Error in handle_agent_info: {str(e)}")
        return create_error_response(500, "Internal server error")


def handle_agent_query(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle POST /agent/query - Direct agent query for testing orchestrator routing.
    
    Required fields:
    - query: Query text to send to agent
    
    Optional fields:
    - agentType: Type of agent ('orchestrator', 'scheduling', 'information') - default: 'orchestrator'
    - sessionId: Session ID for conversation context - default: generated
    
    Returns:
        Agent response with routing information
    """
    try:
        body = parse_event_body(event)
        
        # Validate required fields
        validation_error = validate_required_fields(body, ['query'])
        if validation_error:
            return create_error_response(400, validation_error, "VALIDATION_ERROR")
        
        query = body['query']
        agent_type = body.get('agentType', 'orchestrator')
        session_id = body.get('sessionId', f'test-session-{datetime.now().timestamp()}')
        
        # Validate agent type
        valid_agent_types = ['orchestrator', 'scheduling', 'information']
        if agent_type not in valid_agent_types:
            return create_error_response(400, f"Invalid agent type. Must be one of: {', '.join(valid_agent_types)}", "INVALID_AGENT_TYPE")
        
        # Get agent configuration
        agent_config = get_agent_config(agent_type)
        if not agent_config['agent_id'] or not agent_config['alias_id']:
            return create_error_response(503, f"Agent {agent_type} not configured", "AGENT_NOT_CONFIGURED")
        
        # Invoke agent
        start_time = datetime.now()
        
        try:
            response = bedrock_agent_runtime.invoke_agent(
                agentId=agent_config['agent_id'],
                agentAliasId=agent_config['alias_id'],
                sessionId=session_id,
                inputText=query,
                enableTrace=True
            )
            
            # Process response
            completion_text = ""
            trace_info = []
            
            for event_item in response.get('completion', []):
                if 'chunk' in event_item:
                    chunk = event_item['chunk']
                    if 'bytes' in chunk:
                        completion_text += chunk['bytes'].decode('utf-8')
                elif 'trace' in event_item:
                    trace_info.append(event_item['trace'])
            
            end_time = datetime.now()
            response_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Log agent interaction for monitoring
            log_agent_interaction(
                agent_type=agent_type,
                query=query,
                response_time_ms=response_time_ms,
                success=True
            )
            
            return create_response(200, {
                'agentType': agent_type,
                'query': query,
                'response': completion_text or 'No response from agent',
                'responseTimeMs': response_time_ms,
                'sessionId': session_id,
                'trace': trace_info if trace_info else None,
                'timestamp': get_current_timestamp()
            })
            
        except ClientError as e:
            end_time = datetime.now()
            response_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Log failed interaction
            log_agent_interaction(
                agent_type=agent_type,
                query=query,
                response_time_ms=response_time_ms,
                success=False,
                error=str(e)
            )
            
            return create_error_response(500, f"Agent invocation failed: {str(e)}", "AGENT_INVOCATION_FAILED")
        
    except DatabaseError as e:
        logger.error(f"Database error in handle_agent_query: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in handle_agent_query: {str(e)}")
        return create_error_response(500, "Internal server error")


def handle_health_check(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle GET /agent/health - Health check for all agents and services.
    
    Returns:
        Health status of all system components
    """
    try:
        health_status = {
            'timestamp': get_current_timestamp(),
            'overall': 'healthy',
            'components': {}
        }
        
        # Check database connectivity
        try:
            sql = "SELECT 1 as health_check"
            db_manager.execute_sql(sql)
            health_status['components']['database'] = {
                'status': 'healthy',
                'message': 'Database connection successful'
            }
        except Exception as e:
            health_status['components']['database'] = {
                'status': 'unhealthy',
                'message': f'Database connection failed: {str(e)}'
            }
            health_status['overall'] = 'degraded'
        
        # Check all agents
        agent_types = ['orchestrator', 'scheduling', 'information']
        for agent_type in agent_types:
            agent_health = check_agent_health(agent_type)
            health_status['components'][f'{agent_type}_agent'] = agent_health
            
            if agent_health['status'] == 'unhealthy':
                health_status['overall'] = 'degraded'
        
        # Determine overall status
        unhealthy_components = [
            name for name, status in health_status['components'].items()
            if status['status'] == 'unhealthy'
        ]
        
        if unhealthy_components:
            health_status['overall'] = 'unhealthy' if len(unhealthy_components) > 1 else 'degraded'
            health_status['unhealthy_components'] = unhealthy_components
        
        status_code = 200 if health_status['overall'] == 'healthy' else 503
        
        return create_response(status_code, health_status)
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return create_error_response(500, {
            'overall': 'unhealthy',
            'error': str(e),
            'timestamp': get_current_timestamp()
        })


def handle_get_metrics(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle GET /agent/metrics - Get agent interaction metrics.
    
    Query parameters:
    - hours: Time range in hours (default: 24, max: 168)
    
    Returns:
        Agent interaction statistics and metrics
    """
    try:
        query_params = extract_query_parameters(event)
        hours = min(int(query_params.get('hours', 24)), 168)  # Max 1 week
        
        # Since we don't store chat messages in database, return CloudWatch-based metrics
        # or mock metrics for now
        metrics = {
            'total_messages': 0,
            'unique_sessions': 0,
            'orchestrator_calls': 0,
            'scheduling_calls': 0,
            'information_calls': 0,
            'avg_response_time_seconds': 0
        }
        
        # Try to get CloudWatch metrics if available
        try:
            from datetime import datetime, timedelta
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            # Get invocation metrics from CloudWatch
            invocation_stats = get_metric_statistics(
                'Healthcare/Agents',
                'Invocations',
                start_time,
                end_time,
                'Sum'
            )
            
            response_time_stats = get_metric_statistics(
                'Healthcare/Agents',
                'ResponseTime',
                start_time,
                end_time,
                'Average'
            )
            
            metrics['total_messages'] = int(invocation_stats.get('value', 0))
            metrics['avg_response_time_seconds'] = response_time_stats.get('value', 0) / 1000  # Convert ms to seconds
            
        except Exception as cw_error:
            logger.warning(f"Could not retrieve CloudWatch metrics: {str(cw_error)}")
            # Keep default zero values
        
        # Since we don't store chat messages, set error count to 0
        error_count = 0
        
        return create_response(200, {
            'time_range_hours': hours,
            'timestamp': get_current_timestamp(),
            'metrics': metrics,
            'error_count': error_count
        })
        
    except DatabaseError as e:
        logger.error(f"Database error in handle_get_metrics: {str(e)}")
        return create_error_response(500, "Database error", e.error_code)
    
    except Exception as e:
        logger.error(f"Error in handle_get_metrics: {str(e)}")
        return create_error_response(500, "Internal server error")


def get_agent_config(agent_type: str) -> Dict[str, str]:
    """
    Get agent configuration from SSM.
    
    Args:
        agent_type: Type of agent ('orchestrator', 'scheduling', 'information')
        
    Returns:
        Dictionary with agent_id and alias_id
    """
    if agent_type == 'orchestrator':
        return {
            'agent_id': ssm_config.get_orchestrator_agent_id(),
            'alias_id': ssm_config.get_orchestrator_alias_id()
        }
    elif agent_type == 'scheduling':
        return {
            'agent_id': ssm_config.get_scheduling_agent_id(),
            'alias_id': ssm_config.get_scheduling_alias_id()
        }
    elif agent_type == 'information':
        return {
            'agent_id': ssm_config.get_information_agent_id(),
            'alias_id': ssm_config.get_information_alias_id()
        }
    else:
        return {'agent_id': '', 'alias_id': ''}


def check_agent_health(agent_type: str) -> Dict[str, Any]:
    """
    Check health of a specific agent.
    
    Args:
        agent_type: Type of agent ('orchestrator', 'scheduling', 'information')
        
    Returns:
        Health status dictionary
    """
    agent_config = get_agent_config(agent_type)
    agent_id = agent_config['agent_id']
    alias_id = agent_config['alias_id']
    
    if not agent_id or not alias_id:
        return {
            'status': 'not_configured',
            'message': f'{agent_type} agent not configured (missing ID or Alias ID)'
        }
    
    try:
        # Simple health check query with timeout
        response = bedrock_agent_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=alias_id,
            sessionId=f'health-check-{datetime.now().timestamp()}',
            inputText='health check',
            enableTrace=False
        )
        
        # If we get a response, agent is healthy
        return {
            'status': 'healthy',
            'message': f'{agent_type} agent responding',
            'agent_id': agent_id
        }
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        return {
            'status': 'unhealthy',
            'message': f'{agent_type} agent error: {error_code}',
            'error': str(e)
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': f'{agent_type} agent error',
            'error': str(e)
        }


def log_agent_interaction(
    agent_type: str,
    query: str,
    response_time_ms: float,
    success: bool,
    error: str = None
) -> None:
    """
    Log agent interaction for monitoring and debugging.
    
    Args:
        agent_type: Type of agent
        query: User query
        response_time_ms: Response time in milliseconds
        success: Whether the interaction was successful
        error: Error message if failed
    """
    try:
        # Log to CloudWatch Logs
        log_entry = {
            'timestamp': get_current_timestamp(),
            'agent_type': agent_type,
            'query_length': len(query),
            'response_time_ms': response_time_ms,
            'success': success
        }
        
        if error:
            log_entry['error'] = error
        
        logger.info(f"Agent interaction: {json.dumps(log_entry)}")
        
        # Publish custom CloudWatch metrics
        try:
            cloudwatch.put_metric_data(
                Namespace='Healthcare/Agents',
                MetricData=[
                    {
                        'MetricName': 'ResponseTime',
                        'Value': response_time_ms,
                        'Unit': 'Milliseconds',
                        'Dimensions': [
                            {'Name': 'AgentType', 'Value': agent_type}
                        ],
                        'Timestamp': datetime.utcnow()
                    },
                    {
                        'MetricName': 'Invocations',
                        'Value': 1,
                        'Unit': 'Count',
                        'Dimensions': [
                            {'Name': 'AgentType', 'Value': agent_type},
                            {'Name': 'Success', 'Value': str(success)}
                        ],
                        'Timestamp': datetime.utcnow()
                    }
                ]
            )
        except Exception as metric_error:
            logger.warning(f"Failed to publish CloudWatch metrics: {str(metric_error)}")
        
    except Exception as e:
        logger.error(f"Error logging agent interaction: {str(e)}")


def get_metric_statistics(
    namespace: str,
    metric_name: str,
    start_time: datetime,
    end_time: datetime,
    statistic: str,
    dimensions: List[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Get CloudWatch metric statistics.
    
    Args:
        namespace: CloudWatch namespace
        metric_name: Metric name
        start_time: Start time
        end_time: End time
        statistic: Statistic type
        dimensions: Optional dimensions
        
    Returns:
        Metric statistics
    """
    try:
        params = {
            'Namespace': namespace,
            'MetricName': metric_name,
            'StartTime': start_time,
            'EndTime': end_time,
            'Period': 3600,  # 1 hour
            'Statistics': [statistic]
        }
        
        if dimensions:
            params['Dimensions'] = dimensions
        
        response = cloudwatch.get_metric_statistics(**params)
        
        datapoints = response.get('Datapoints', [])
        if not datapoints:
            return {'value': 0, 'unit': 'None'}
        
        # Get latest datapoint
        latest_datapoint = sorted(datapoints, key=lambda x: x['Timestamp'], reverse=True)[0]
        
        return {
            'value': latest_datapoint.get(statistic, 0),
            'unit': latest_datapoint.get('Unit', 'None'),
            'timestamp': latest_datapoint.get('Timestamp')
        }
        
    except Exception as e:
        logger.error(f"Failed to get metric statistics for {metric_name}: {str(e)}")
        return {'value': 0, 'unit': 'None', 'error': str(e)}
