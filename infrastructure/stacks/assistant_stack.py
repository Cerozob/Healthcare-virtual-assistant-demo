"""
Assistant Stack for Healthcare Workflow System.
"""

from aws_cdk import Stack, CfnOutput, RemovalPolicy, CustomResource, Duration
from aws_cdk import aws_bedrock as bedrock
from aws_cdk import aws_bedrockagentcore as agentcore
from aws_cdk import aws_bedrock_agentcore_alpha as agentcore_alpha
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_cloudwatch as cloudwatch
from aws_cdk import aws_ssm as ssm
from aws_cdk import aws_rds as rds

from aws_cdk import aws_ecr_assets as ecr_assets

from constructs import Construct
from typing import Dict
import json
import os
from pathlib import Path
from ..schemas.lambda_tool_schemas import get_all_tool_schemas
from ..constructs.bedrock_guardrail_construct import BedrockGuardrailConstruct
from ..constructs.bedrock_knowledge_base_construct import BedrockKnowledgeBaseConstruct


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

        self.agentcore_gateway = agentcore.CfnGateway(
            self, "Agentcoregateway", authorizer_type="AWS_IAM", name="agentcoregateway", protocol_type="MCP", role_arn=agentcore_gateway_role.role_arn
        )

        # Create AgentCore Runtime
        agent_runtime_role = self.create_agent_runtime_role()

        # Create single lambda target gateway with all tool schemas
        self.lambda_gateway_target = self._create_unified_lambda_gateway_target()

        # Create AgentCore Runtime using alpha library
        self.agent_runtime = agentcore_alpha.Runtime(
            self,
            "HealthcareAssistantRuntime",
            runtime_name="healthcare_assistant",
            agent_runtime_artifact=self.agent_runtime_artifact,
            authorizer_configuration=agentcore_alpha.RuntimeAuthorizerConfiguration.using_iam(),
            execution_role=agent_runtime_role,
            environment_variables=self.get_agent_environment_variables(),
            # Network configuration defaults to PUBLIC
            # Guardrails will be configured via environment variables
            protocol_configuration=agentcore_alpha.ProtocolType.HTTP
        )

        self.endpoint = agentcore_alpha.RuntimeEndpoint(self,
            "AgentcoreEndpoint",
            agent_runtime_id=self.agent_runtime.agent_runtime_id,
            endpoint_name="AgentEndpoint",
        )



        # Add dependency on knowledge base and guardrails
        self.agent_runtime.node.add_dependency(self.knowledge_base_construct.knowledge_base)
        self.agent_runtime.node.add_dependency(self.agentcore_gateway)
        self.agent_runtime.node.add_dependency(self.guardrail_construct.guardrails)

        # Store AgentCore endpoint in SSM Parameter Store
        self._create_ssm_parameters()

        # Create CloudFormation outputs
        self.create_outputs()



    def _create_unified_lambda_gateway_target(self) -> agentcore.CfnGatewayTarget:
        """
        Create a single AgentCore gateway target with all Lambda function tools.
        This simplified approach uses one gateway target with multiple tool definitions.
        """
        if not self.lambda_functions:
            return None

        # Get all tool schemas from the separate schemas file
        all_tool_schemas = get_all_tool_schemas()

        # Create a mapping of tool names to Lambda ARNs for the MCP configuration
        # Since we have multiple tools but they all route to different Lambdas,
        # we'll use the first Lambda as the primary target and handle routing in the Lambda
        primary_lambda = list(self.lambda_functions.values())[0]

        return agentcore.CfnGatewayTarget(
            self,
            "UnifiedLambdaGatewayTarget",
            name="healthcare-lambda-tools",
            credential_provider_configurations=[
                agentcore.CfnGatewayTarget.CredentialProviderConfigurationProperty(
                    credential_provider_type="GATEWAY_IAM_ROLE"
                )
            ],
            target_configuration=agentcore.CfnGatewayTarget.TargetConfigurationProperty(
                mcp=agentcore.CfnGatewayTarget.McpTargetConfigurationProperty(
                    lambda_=agentcore.CfnGatewayTarget.McpLambdaTargetConfigurationProperty(
                        lambda_arn=primary_lambda.function_arn,
                        tool_schema=agentcore.CfnGatewayTarget.ToolSchemaProperty(
                            inline_payload=all_tool_schemas
                        )
                    )
                )
            ),
            gateway_identifier=self.agentcore_gateway.attr_gateway_identifier
        )



    def create_agent_runtime_role(self):
        """
        Create IAM role for AgentCore Runtime with necessary permissions.
        """
        agent_runtime_role = iam.Role(
            self,
            "HealthcareAssistantRuntimeRole",
            assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
            description="Role for Healthcare Assistant AgentCore Runtime",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonBedrockFullAccess")
            ]
        )

        # Bedrock model invocation permissions
        agent_runtime_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                resources=[
                    f"arn:aws:bedrock:{self.region}::foundation-model/*"
                ]
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

        # Note: AgentCore handles logging automatically
        # No CloudWatch logs permissions needed

        # CloudWatch Metrics permissions
        agent_runtime_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cloudwatch:PutMetricData"
                ],
                resources=["*"],
                conditions={
                    "StringEquals": {
                        "cloudwatch:namespace": "Healthcare/Agents"
                    }
                }
            )
        )

        # X-Ray tracing permissions for observability
        agent_runtime_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords"
                ],
                resources=["*"]
            )
        )

        # AgentCore Gateway permissions
        agent_runtime_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock-agentcore:InvokeGateway",
                    "bedrock-agentcore:ListGatewayTargets"
                ],
                resources=[
                    f"arn:aws:bedrock-agentcore:{self.region}:{self.account}:gateway/{self.agentcore_gateway.attr_gateway_identifier}",
                    f"arn:aws:bedrock-agentcore:{self.region}:{self.account}:gateway/{self.agentcore_gateway.attr_gateway_identifier}/*"
                ]
            )
        )

        # Lambda invoke permissions for gateway targets
        if self.lambda_functions:
            lambda_arns = [
                func.function_arn for func in self.lambda_functions.values()]
            agent_runtime_role.add_to_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["lambda:InvokeFunction"],
                    resources=lambda_arns
                )
            )

        return agent_runtime_role

    def _create_ssm_parameters(self) -> None:
        """Store AgentCore configuration in SSM Parameter Store."""
        
        # Store the AgentCore runtime ARN
        self.agentcore_endpoint_parameter = ssm.StringParameter(
            self,
            "AgentCoreEndpointParameter",
            parameter_name="/healthcare/agentcore/endpoint-url",
            string_value=self.agent_runtime.agent_runtime_arn,
            description="AgentCore Runtime ARN",
            tier=ssm.ParameterTier.STANDARD
        )

    def get_agent_environment_variables(self) -> dict:
        """
        Return environment variables for agent runtime configuration.
        """
        return {
            # Model Configuration - Using global inference profile
            "MODEL_ID": self.inference_profile,
            "MODEL_TEMPERATURE": "0.1",
            "MODEL_MAX_TOKENS": "4096",
            "MODEL_TOP_P": "0.9",

            # Knowledge Base Configuration - Populated by CDK
            "KNOWLEDGE_BASE_ID": self.knowledge_base_construct.knowledge_base_id,
            "SUPPLEMENTAL_DATA_BUCKET": self.knowledge_base_construct.supplemental_data_bucket_name,


            # Database Configuration - Populated by CDK
            "DATABASE_CLUSTER_ARN": self.database_cluster.cluster_arn,
            "DATABASE_SECRET_ARN": self.database_cluster.secret.secret_arn,

            # Agent Configuration - LATAM healthcare settings
            "DEFAULT_LANGUAGE": "es-LATAM",
            "STREAMING_ENABLED": "true",
            "SESSION_TIMEOUT_MINUTES": "30",

            # Guardrails Configuration - Using created guardrail
            "GUARDRAIL_ID": self.guardrail_construct.guardrail_id,
            "GUARDRAIL_VERSION": self.guardrail_construct.guardrail_version_id,

            # Agentcore gateway
            "GATEWAY_URL": self.agentcore_gateway.attr_gateway_url,
            "GATEWAY_ID": self.agentcore_gateway.attr_gateway_identifier,

            # Session Management Configuration - S3 storage for medical notes
            # Uses consistent structure with document processing: processed/{patient_id}_{data_type}/
            "SESSION_BUCKET": self.processed_bucket.bucket_name if self.processed_bucket else "",
            "SESSION_PREFIX": "processed/",  # Base prefix, actual structure: processed/{patient_id}_{data_type}/
            "ENABLE_SESSION_MANAGEMENT": "true",

            # Observability Configuration - AgentCore handles logging automatically
            "ENABLE_TRACING": "true",
            "METRICS_NAMESPACE": "Healthcare/Agents",
        }

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
            "AgentRuntimeArn",
            value=self.agent_runtime.agent_runtime_arn,
            description="Healthcare Assistant AgentCore Runtime ARN"
        )

        # Note: AgentCore manages logging automatically
        # No log group output needed

        CfnOutput(
            self,
            "AgentCoreEndpointUrl",
            value=self.endpoint.endpoint_id,
            description="AgentCore Runtime endpoint URL"
        )

        CfnOutput(
            self,
            "AgentCoreApiGatewayPath",
            value="/v1/agentcore/chat",
            description="AgentCore chat endpoint path in API Gateway"
        )


