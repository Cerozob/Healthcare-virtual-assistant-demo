"""
Assistant Stack for Healthcare Workflow System.
"""

from ..constructs.bedrock_knowledge_base_construct import BedrockKnowledgeBaseConstruct
from ..constructs.bedrock_guardrail_construct import BedrockGuardrailConstruct
from ..schemas.lambda_tool_schemas import get_all_tool_schemas
from aws_cdk import Stack, CfnOutput, RemovalPolicy, CustomResource, Duration
from aws_cdk import aws_bedrock as bedrock
from aws_cdk import aws_bedrockagentcore as agentcore
from aws_cdk import aws_bedrock_agentcore_alpha as agentcore_alpha
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_ssm as ssm
from aws_cdk import aws_rds as rds
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_apigateway as apigateway

from aws_cdk import aws_ecr_assets as ecr_assets

from constructs import Construct
from typing import Dict
import json
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
# Removed Cognito OAuth construct - using IAM-based authorization instead


class AssistantStack(Stack):
    """
    Stack for AI assistant and real-time chat functionality with Bedrock AgentCore.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        bedrock_user_secret,
        processed_bucket: s3.Bucket = None,
        database_cluster: rds.DatabaseCluster = None,
        db_init_resource: CustomResource = None,
        lambda_functions: Dict = None,

        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Store references for use in methods
        self.processed_bucket = processed_bucket
        self.database_cluster = database_cluster
        self.db_init_resource = db_init_resource
        self.bedrock_user_secret = bedrock_user_secret
        self.lambda_functions = lambda_functions or {}

        # Note: We no longer directly modify the extraction lambda to avoid cyclic dependencies
        # Instead, we use SSM parameters for configuration

        # Create Bedrock Knowledge Base construct
        self.knowledge_base_construct = BedrockKnowledgeBaseConstruct(
            self,
            "KnowledgeBase",
            processed_bucket=processed_bucket,
            database_cluster=database_cluster,
            bedrock_user_secret=bedrock_user_secret,
            db_init_resource=db_init_resource
        )

        # Create Bedrock Guardrail construct
        self.guardrail_construct = BedrockGuardrailConstruct(
            self,
            "Guardrail"
        )

        # Using IAM-based authorization for AgentCore Gateway (simpler and more appropriate)

        # Note: AgentCore manages its own logging automatically
        # No need to create a separate CloudWatch log group

        print(
            f"building from {str(Path(__file__).parent.parent.parent / "agents")}")
        # Create ECR asset for agent container
        self.agent_runtime_artifact = agentcore_alpha.AgentRuntimeArtifact.from_asset(
            directory=str(Path(__file__).parent.parent.parent / "agents"),
            platform=ecr_assets.Platform.LINUX_ARM64,
        )

        self.inference_profile = "global.anthropic.claude-haiku-4-5-20251001-v1:0"

        agentcore_gateway_role = iam.Role(
            self,
            "AgentcoreGatewayRuntimeRole",
            assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
            description="Role for Healthcare Assistant AgentCore Gateway",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "BedrockAgentCoreFullAccess")
            ]
        )

        # Enhanced Gateway Role permissions for Lambda invocation
        agentcore_gateway_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "lambda:InvokeFunction",
                    "lambda:GetFunction"
                ],
                resources=[
                    f"arn:aws:lambda:{self.region}:{self.account}:function:healthcare-*",
                    f"arn:aws:lambda:{self.region}:{self.account}:function:PatientLookupFunction"
                ]
            )
        )

        # Enhanced Gateway Role permissions for credential management
        agentcore_gateway_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "agent-credential-provider:*",
                    "iam:PassRole"
                ],
                resources=["*"]
            )
        )

        # Required permission for semantic search gateway creation
        agentcore_gateway_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock-agentcore:SynchronizeGatewayTargets"
                ],
                resources=["*"]
            )
        )

        # Additional Gateway permissions for comprehensive functionality
        agentcore_gateway_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:*",
                    "secretsmanager:GetSecretValue",
                    "ssm:GetParameter",
                    "ssm:GetParameters"
                ],
                resources=["*"]
            )
        )

        # Create AgentCore Gateway with IAM-based authorization and semantic search
        # IMPORTANT: Semantic search can only be enabled when creating a gateway, not updated later
        # The gateway role must have bedrock-agentcore:SynchronizeGatewayTargets permission
        self.agentcore_gateway = agentcore.CfnGateway(
            self,
            "Agentcoregateway",
            authorizer_type="AWS_IAM",
            name="agentcoregateway",
            protocol_type="MCP",
            role_arn=agentcore_gateway_role.role_arn,
            exception_level='DEBUG',
            protocol_configuration=agentcore.CfnGateway.GatewayProtocolConfigurationProperty(
                mcp=agentcore.CfnGateway.MCPGatewayConfigurationProperty(

                    search_type="SEMANTIC"
                )
            )
        )

        # Create AgentCore Runtime
        agent_runtime_role = self.create_agent_runtime_role()

        # Create separate gateway targets for each Lambda function (supports semantic search)
        self.lambda_gateway_targets = self._create_individual_lambda_gateway_targets()

        # Get environment variables and log them for debugging
        env_vars = self.get_agent_environment_variables()
        logger.info(
            f"Setting AgentCore environment variables: {list(env_vars.keys())}")

        # Log critical variables for debugging
        critical_vars = ["BEDROCK_MODEL_ID", "BEDROCK_KNOWLEDGE_BASE_ID",
                         "USE_MCP_GATEWAY", "MCP_GATEWAY_URL"]
        for var in critical_vars:
            if var in env_vars:
                logger.info(f"  {var}: {env_vars[var]}")
            else:
                logger.warning(f"  {var}: NOT SET")

        # Create AgentCore Runtime using alpha library with IAM authorization
        self.agent_runtime = agentcore_alpha.Runtime(
            self,
            "HealthcareAssistantRuntime",
            runtime_name="healthcare_assistant",
            agent_runtime_artifact=self.agent_runtime_artifact,
            # Use IAM-based authorization (simpler and more appropriate)
            authorizer_configuration=agentcore_alpha.RuntimeAuthorizerConfiguration.using_iam(),
            execution_role=agent_runtime_role,
            environment_variables=env_vars,
            # Network configuration defaults to PUBLIC
            # Guardrails will be configured via environment variables
            protocol_configuration=agentcore_alpha.ProtocolType.HTTP
        )

        # Add dependency on knowledge base and guardrails
        self.agent_runtime.node.add_dependency(
            self.knowledge_base_construct.knowledge_base)
        self.agent_runtime.node.add_dependency(self.agentcore_gateway)
        self.agent_runtime.node.add_dependency(
            self.guardrail_construct.guardrails)

        # Store Knowledge Base configuration in SSM for extraction lambda to use
        self.knowledge_base_id_param = ssm.StringParameter(
            self,
            "KnowledgeBaseIdParameter",
            parameter_name="/healthcare/knowledge-base/id",
            string_value=self.knowledge_base_construct.knowledge_base_id,
            description="Bedrock Knowledge Base ID for document processing",
        )

        self.knowledge_base_data_source_param = ssm.StringParameter(
            self,
            "KnowledgeBaseDataSourceParameter",
            parameter_name="/healthcare/knowledge-base/data-source-id",
            string_value=self.knowledge_base_construct.data_source.attr_data_source_id,
            description="Bedrock Knowledge Base Data Source ID for document processing",
        )

        logger.info(
            f"Stored Knowledge Base ID in SSM: {self.knowledge_base_construct.knowledge_base_id}")
        logger.info(
            f"Stored Data Source ID in SSM: {self.knowledge_base_construct.data_source.attr_data_source_id}")

        # No OAuth Lambda needed with IAM-based authorization

        self._create_ssm_parameters()

        # Create CloudFormation outputs
        self.create_outputs()

    def _create_individual_lambda_gateway_targets(self) -> Dict[str, agentcore.CfnGatewayTarget]:
        """
        Create separate AgentCore gateway targets for each Lambda function.

        This approach provides:
        - Better observability and monitoring per healthcare domain
        - Granular permissions and separation of concerns
        - Individual tool schemas for each Lambda function
        - Support for semantic search (when gateway is created with semantic search enabled)
        """
        if not self.lambda_functions:
            return {}

        # Import individual tool schema functions
        from ..schemas.lambda_tool_schemas import (
            get_patients_tool_schema,
            get_medics_tool_schema,
            get_exams_tool_schema,
            get_reservations_tool_schema,
            get_files_tool_schema
        )

        # Mapping of Lambda function names to their tool schemas
        lambda_tool_mapping = {
            "patients": get_patients_tool_schema(),
            "medics": get_medics_tool_schema(),
            "exams": get_exams_tool_schema(),
            "reservations": get_reservations_tool_schema(),
            "files": get_files_tool_schema()
        }

        gateway_targets = {}

        for lambda_name, lambda_function in self.lambda_functions.items():
            # Skip if we don't have a tool schema for this Lambda
            if lambda_name not in lambda_tool_mapping:
                logger.warning(
                    f"No tool schema found for Lambda function: {lambda_name}")
                continue

            tool_schema = lambda_tool_mapping[lambda_name]

            # Create individual gateway target for this Lambda
            gateway_target = agentcore.CfnGatewayTarget(
                self,
                f"{lambda_name.title()}GatewayTarget",
                name=f"healthcare-{lambda_name}-api",
                credential_provider_configurations=[
                    agentcore.CfnGatewayTarget.CredentialProviderConfigurationProperty(
                        credential_provider_type="GATEWAY_IAM_ROLE"
                    )
                ],
                target_configuration=agentcore.CfnGatewayTarget.TargetConfigurationProperty(
                    mcp=agentcore.CfnGatewayTarget.McpTargetConfigurationProperty(
                        lambda_=agentcore.CfnGatewayTarget.McpLambdaTargetConfigurationProperty(
                            lambda_arn=lambda_function.function_arn,
                            tool_schema=agentcore.CfnGatewayTarget.ToolSchemaProperty(
                                # Single tool schema per target
                                inline_payload=[tool_schema]
                            )
                        )
                    )
                ),
                gateway_identifier=self.agentcore_gateway.attr_gateway_identifier
            )

            gateway_targets[lambda_name] = gateway_target

            logger.info(
                f"Created gateway target for {lambda_name}: healthcare-{lambda_name}-api")

        return gateway_targets

    def create_agent_runtime_role(self):
        """
        Create IAM role for AgentCore Runtime with enhanced permissions.

        This role includes broad permissions following AWS best practices for AgentCore:
        - Full bedrock-agentcore:* access for gateway operations
        - Full bedrock:* access for model and service interactions  
        - agent-credential-provider:* for credential management
        - iam:PassRole for cross-service operations
        - Enhanced Lambda permissions for healthcare functions
        """
        agent_runtime_role = iam.Role(
            self,
            "HealthcareAssistantRuntimeRole",
            assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
            description="Role for Healthcare Assistant AgentCore Runtime",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonBedrockFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "CloudWatchFullAccess"),
                # Add BedrockAgentCoreFullAccess for comprehensive gateway access
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "BedrockAgentCoreFullAccess")
            ]
        )

        # Bedrock permissions - Enhanced with broader access for full AgentCore functionality
        agent_runtime_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:*"  # Broader permissions for comprehensive Bedrock access
                ],
                # Allow access to all Bedrock resources including cross-region models
                resources=["*"]
            )
        )

        # Bedrock Knowledge Base permissions
        agent_runtime_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:Retrieve",
                    "bedrock:RetrieveAndGenerate"
                ],
                resources=[
                    f"arn:aws:bedrock:{self.region}:{self.account}:knowledge-base/{self.knowledge_base_construct.knowledge_base_id}"
                ]
            )
        )

        # Bedrock Guardrails permissions - including cross-region guardrail profiles
        agent_runtime_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:ApplyGuardrail"
                ],
                resources=[
                    # Local guardrails
                    f"arn:aws:bedrock:{self.region}:{self.account}:guardrail/*",
                    # Cross-region guardrail profiles for global inference
                    f"arn:aws:bedrock:us-east-1:{self.account}:guardrail-profile/us.guardrail.v1:0",
                    f"arn:aws:bedrock:us-east-2:{self.account}:guardrail-profile/us.guardrail.v1:0",
                    f"arn:aws:bedrock:us-west-2:{self.account}:guardrail-profile/us.guardrail.v1:0"
                ]
            )
        )

        # RDS Data API permissions for database access
        agent_runtime_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "rds-data:ExecuteStatement",
                    "rds-data:BatchExecuteStatement",
                    "rds-data:BeginTransaction",
                    "rds-data:CommitTransaction",
                    "rds-data:RollbackTransaction"
                ],
                resources=[
                    self.database_cluster.cluster_arn
                ]
            )
        )

        # Secrets Manager permissions for database credentials
        agent_runtime_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret"
                ],
                resources=[
                    self.database_cluster.secret.secret_arn
                ]
            )
        )

        # S3 permissions for supplemental data storage
        agent_runtime_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:ListBucket"
                ],
                resources=[
                    self.knowledge_base_construct.supplemental_data_storage.bucket_arn,
                    f"{self.knowledge_base_construct.supplemental_data_storage.bucket_arn}/*"
                ]
            )
        )

        # S3 permissions for session management (medical notes storage)
        if self.processed_bucket:
            agent_runtime_role.add_to_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject",
                        "s3:ListBucket",
                        "s3:GetObjectVersion",
                        "s3:PutObjectAcl"
                    ],
                    resources=[
                        self.processed_bucket.bucket_arn,
                        f"{self.processed_bucket.bucket_arn}/*"
                    ]
                )
            )

        # ECR permissions for AgentCore container access
        agent_runtime_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer"
                ],
                resources=[
                    f"arn:aws:ecr:{self.region}:{self.account}:repository/*"
                ]
            )
        )

        # ECR token access (global permission)
        agent_runtime_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ecr:GetAuthorizationToken"
                ],
                resources=["*"]
            )
        )

        # CloudWatch Logs permissions - AgentCore needs to create log groups and streams
        # Pattern matches: /aws/bedrock-agentcore/runtimes/{runtime_name}-{random_suffix}-{variant}
        agent_runtime_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "logs:DescribeLogGroups",
                    "logs:DescribeLogStreams"
                ],
                resources=[
                    f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/bedrock-agentcore/runtimes/*",
                    f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*"
                ]
            )
        )

        # CloudWatch Metrics permissions - Enhanced for comprehensive monitoring
        agent_runtime_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cloudwatch:PutMetricData",
                    "cloudwatch:GetMetricStatistics",
                    "cloudwatch:ListMetrics"
                ],
                resources=["*"]
            )
        )

        # X-Ray tracing permissions for observability - Enhanced for AgentCore
        agent_runtime_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords",
                    "xray:GetSamplingRules",
                    "xray:GetSamplingTargets",
                    "xray:GetTraceGraph",
                    "xray:GetTraceSummaries"
                ],
                resources=["*"]
            )
        )

        # Additional system permissions for comprehensive AgentCore functionality
        agent_runtime_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ssm:GetParameter",
                    "ssm:GetParameters",
                    "ssm:GetParametersByPath",
                    "kms:Decrypt",
                    "kms:DescribeKey"
                ],
                resources=["*"]
            )
        )

        # AgentCore Gateway permissions - Enhanced with broader access
        agent_runtime_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock-agentcore:*"  # Broader permissions for full gateway functionality
                ],
                resources=["*"]  # Allow access to all AgentCore resources
            )
        )

        # Agent Credential Provider permissions - Required for credential management
        agent_runtime_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "agent-credential-provider:*"
                ],
                resources=["*"]
            )
        )

        # IAM PassRole permissions - Required for cross-service operations
        agent_runtime_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "iam:PassRole"
                ],
                resources=[
                    f"arn:aws:iam::{self.account}:role/*bedrock*",
                    f"arn:aws:iam::{self.account}:role/*agentcore*",
                    f"arn:aws:iam::{self.account}:role/*healthcare*"
                ],
                conditions={
                    "StringEquals": {
                        "iam:PassedToService": [
                            "bedrock.amazonaws.com",
                            "bedrock-agentcore.amazonaws.com"
                        ]
                    }
                }
            )
        )

        # AgentCore Workload Access Token permissions - Critical for runtime operation
        agent_runtime_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock-agentcore:GetWorkloadAccessToken",
                    "bedrock-agentcore:GetWorkloadAccessTokenForJWT",
                    "bedrock-agentcore:GetWorkloadAccessTokenForUserId"
                ],
                resources=[
                    f"arn:aws:bedrock-agentcore:{self.region}:{self.account}:workload-identity-directory/default",
                    f"arn:aws:bedrock-agentcore:{self.region}:{self.account}:workload-identity-directory/default/workload-identity/healthcare_assistant-*"
                ]
            )
        )

        # Lambda invoke permissions for gateway targets - Enhanced for flexibility
        agent_runtime_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "lambda:InvokeFunction",
                    "lambda:GetFunction",
                    "lambda:ListFunctions"
                ],
                resources=[
                    f"arn:aws:lambda:{self.region}:{self.account}:function:healthcare-*",
                    f"arn:aws:lambda:{self.region}:{self.account}:function:PatientLookupFunction"
                ]
            )
        )

        # Add specific permission to invoke the gateway (IAM-based authorization)
        agent_runtime_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock-agentcore:InvokeGateway",
                    "bedrock-agentcore:InvokeAgentRuntime"  # Add runtime invocation permission
                ],
                resources=[
                    f"arn:aws:bedrock-agentcore:{self.region}:{self.account}:gateway/*",
                    f"arn:aws:bedrock-agentcore:{self.region}:{self.account}:agent-runtime/*"
                ]
            )
        )

        return agent_runtime_role

    def _create_ssm_parameters(self) -> None:
        """Store AgentCore configuration in SSM Parameter Store."""

        self.agentcore_runtime_id_parameter = ssm.StringParameter(
            self,
            "AgentCoreRuntimeIdParameter",
            parameter_name="/healthcare/agentcore/runtime-id",
            string_value=self.agent_runtime.agent_runtime_id,
            description="AgentCore Runtime ID for direct invocation",
            tier=ssm.ParameterTier.STANDARD
        )

        # Store Gateway ID for IAM-based access
        self.gateway_id_parameter = ssm.StringParameter(
            self,
            "GatewayIdParameter",
            parameter_name="/healthcare/agentcore/gateway-id",
            string_value=self.agentcore_gateway.attr_gateway_identifier,
            description="AgentCore Gateway ID for IAM-based access",
            tier=ssm.ParameterTier.STANDARD
        )

    def get_agent_environment_variables(self) -> dict:
        """
        Return environment variables for agent runtime configuration.
        These match exactly what the agent code expects based on main.py analysis.
        """
        env_vars = {
            # Agent Configuration
            "DEBUG": "false",
            "LOG_LEVEL": "INFO",

            # Model Configuration - agent expects BEDROCK_MODEL_ID
            "BEDROCK_MODEL_ID": self.inference_profile,
            "MODEL_TEMPERATURE": "0.1",
            "MODEL_MAX_TOKENS": "4096",
            "MODEL_TOP_P": "0.9",

            # Knowledge Base Configuration - agent expects BEDROCK_KNOWLEDGE_BASE_ID
            "BEDROCK_KNOWLEDGE_BASE_ID": self.knowledge_base_construct.knowledge_base_id,
            # Used by Strands memory tool
            "STRANDS_KNOWLEDGE_BASE_ID": self.knowledge_base_construct.knowledge_base_id,
            "SUPPLEMENTAL_DATA_BUCKET": self.knowledge_base_construct.supplemental_data_bucket_name,



            # Guardrails Configuration - agent checks both GUARDRAIL_ID and BEDROCK_GUARDRAIL_ID
            "GUARDRAIL_ID": self.guardrail_construct.guardrail_id,
            "GUARDRAIL_VERSION": self.guardrail_construct.guardrail_version_id,
            "BEDROCK_GUARDRAIL_ID": self.guardrail_construct.guardrail_id,
            "BEDROCK_GUARDRAIL_VERSION": self.guardrail_construct.guardrail_version_id,

            # MCP Gateway Configuration - always enabled
            "MCP_GATEWAY_URL": self.agentcore_gateway.attr_gateway_url,
            "GATEWAY_ID": self.agentcore_gateway.attr_gateway_identifier,

            # Session Management Configuration - always required
            "SESSION_BUCKET": self.processed_bucket.bucket_name,

            # Agent Configuration - matches agents/shared/config.py
            "DEFAULT_LANGUAGE": "es-LATAM",

            # Runtime Configuration
            "PORT": "8000",
            "HOST": "0.0.0.0",
            "WORKERS": "1",
            "TIMEOUT": "300",
            "UVICORN_LOG_LEVEL": "info",

            # AWS Configuration - ensure region is set
            "AWS_REGION": self.region,
            "AWS_DEFAULT_REGION": self.region,

            # Observability Configuration - CloudWatch logging enabled
            "ENABLE_TRACING": "true",
            "METRICS_NAMESPACE": "Healthcare/Agents",
        }

        # Log environment variables being set for debugging
        logger.info("=== CDK ENVIRONMENT VARIABLES CONFIGURATION ===")
        for key, value in env_vars.items():
            # Mask sensitive values
            if any(sensitive in key.upper() for sensitive in ["SECRET", "KEY", "TOKEN", "PASSWORD"]):
                masked_value = f"{str(value)[:8]}***" if len(
                    str(value)) > 8 else "***"
                logger.info(f"  {key}: {masked_value}")
            else:
                logger.info(f"  {key}: {value}")
        logger.info("=== END ENVIRONMENT VARIABLES ===")

        return env_vars

    def create_outputs(self):
        """
        Create CloudFormation outputs for the assistant stack.
        """
        CfnOutput(
            self,
            "KnowledgeBaseId",
            value=self.knowledge_base_construct.knowledge_base_id,
            description="Bedrock Knowledge Base ID"
        )

        CfnOutput(
            self,
            "SupplementalDataBucket",
            value=self.knowledge_base_construct.supplemental_data_bucket_name,
            description="S3 bucket for supplemental data storage"
        )

        CfnOutput(
            self,
            "GuardrailId",
            value=self.guardrail_construct.guardrail_id,
            description="Bedrock Guardrail ID for healthcare content filtering"
        )

        CfnOutput(
            self,
            "GuardrailVersion",
            value=self.guardrail_construct.guardrail_version_id,
            description="Bedrock Guardrail Version ID"
        )

        CfnOutput(
            self,
            "AgentRuntimeArn",
            value=self.agent_runtime.agent_runtime_arn,
            description="Healthcare Assistant AgentCore Runtime ARN"
        )

        CfnOutput(
            self, "AgentCoreRuntimeId", value=self.agent_runtime.agent_runtime_id,
            description="Healthcare Assistant AgentCore Runtime ID"
        )

        CfnOutput(
            self, "AgentCoreGatewayUrl", value=self.agentcore_gateway.attr_gateway_url,
            description="AgentCore Gateway URL for MCP tools"
        )

        CfnOutput(
            self, "AgentCoreGatewayId", value=self.agentcore_gateway.attr_gateway_identifier,
            description="AgentCore Gateway Identifier"
        )

        # Output individual gateway target information
        if hasattr(self, 'lambda_gateway_targets') and self.lambda_gateway_targets:
            gateway_targets_info = {}
            for lambda_name, target in self.lambda_gateway_targets.items():
                gateway_targets_info[lambda_name] = f"healthcare-{lambda_name}-api"

            CfnOutput(
                self,
                "GatewayTargets",
                value=json.dumps(gateway_targets_info),
                description="Individual gateway targets for each Lambda function with semantic search support"
            )

        CfnOutput(
            self,
            "AgentCoreDirectAccess",
            value="Use AWS SDK BedrockAgentCore client for direct access with IAM authentication",
            description="AgentCore is accessed directly with IAM authentication"
        )

        CfnOutput(
            self,
            "GatewayInvokePermission",
            value="bedrock-agentcore:InvokeGateway",
            description="IAM permission needed to invoke the AgentCore Gateway"
        )
