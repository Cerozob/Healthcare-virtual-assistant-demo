"""
Assistant Stack for Healthcare Workflow System.
"""

from aws_cdk import Stack, CfnOutput, RemovalPolicy, CustomResource, Duration
from aws_cdk import aws_bedrock as bedrock
from aws_cdk import aws_bedrockagentcore as agentcore
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_cloudwatch as cloudwatch
from aws_cdk import aws_ssm as ssm
from aws_cdk import aws_rds as rds
from aws_cdk import aws_ecr_assets as ecr_assets
from aws_cdk import aws_logs as logs
from constructs import Construct
import json
import os
from pathlib import Path


class AssistantStack(Stack):
    """
    Stack for AI assistant and real-time chat functionality with Bedrock AgentCore.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        processed_bucket: s3.Bucket = None,
        database_cluster: rds.DatabaseCluster = None,
        db_init_resource: CustomResource = None,
        bedrock_user_secret=None,
        api_gateway_endpoint: str = None,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Store references for use in methods
        self.processed_bucket = processed_bucket
        self.database_cluster = database_cluster
        self.db_init_resource = db_init_resource
        self.bedrock_user_secret = bedrock_user_secret
        self.api_gateway_endpoint = api_gateway_endpoint

        self.supplemental_data_storage = s3.Bucket(
            self,
            "SupplementalDataStorage",
            bucket_name=f"ab2-cerozob-supplemental-data-{self.region}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        embeddings_model = bedrock.FoundationModel.from_foundation_model_id(
            self, "Model", bedrock.FoundationModelIdentifier.AMAZON_TITAN_EMBED_TEXT_V2_0)

        knowledge_base_config = bedrock.CfnKnowledgeBase.KnowledgeBaseConfigurationProperty(
            type="VECTOR",
            vector_knowledge_base_configuration=bedrock.CfnKnowledgeBase.VectorKnowledgeBaseConfigurationProperty(
                embedding_model_arn=embeddings_model.model_arn,
                embedding_model_configuration=bedrock.CfnKnowledgeBase.EmbeddingModelConfigurationProperty(

                    bedrock_embedding_model_configuration=bedrock.CfnKnowledgeBase.BedrockEmbeddingModelConfigurationProperty(
                        dimensions=1024,
                        embedding_data_type="FLOAT32"
                    )),
                supplemental_data_storage_configuration=bedrock.CfnKnowledgeBase.SupplementalDataStorageConfigurationProperty(
                    supplemental_data_storage_locations=[
                        bedrock.CfnKnowledgeBase.SupplementalDataStorageLocationProperty(
                            supplemental_data_storage_location_type="S3",
                            s3_location=bedrock.CfnKnowledgeBase.S3LocationProperty(
                                uri=f"s3://{self.supplemental_data_storage.bucket_name}"

                            )
                        )

                    ],

                ),


            )

        )
        knowledge_base_storage_config = bedrock.CfnKnowledgeBase.StorageConfigurationProperty(
            type="RDS",
            rds_configuration=bedrock.CfnKnowledgeBase.RdsConfigurationProperty(
                credentials_secret_arn=self.bedrock_user_secret.secret_arn if self.bedrock_user_secret else self.database_cluster.secret.secret_arn,
                database_name="healthcare",
                resource_arn=self.database_cluster.cluster_arn,
                table_name="ab2_knowledge_base",
                field_mapping=bedrock.CfnKnowledgeBase.RdsFieldMappingProperty(
                    metadata_field="metadata",
                    primary_key_field="pk",
                    text_field="text",
                    vector_field="vector",
                    custom_metadata_field="custom_metadata"
                )
            )
        )

        self.knowledge_base = bedrock.CfnKnowledgeBase(
            self,
            "HealthcareWorkflowKnowledgeBase",
            knowledge_base_configuration=knowledge_base_config,
            storage_configuration=knowledge_base_storage_config,
            name="HealthcareWorkflowKnowledgeBase",
            role_arn=self.create_knowledge_base_role()
        )

        # Ensure database is initialized before creating Knowledge Base
        if self.db_init_resource:
            self.knowledge_base.node.add_dependency(self.db_init_resource)

        # Also ensure the database cluster is fully created
        self.knowledge_base.node.add_dependency(self.database_cluster)

        data_source = bedrock.CfnDataSource(
            self,
            "HealthcareWorkflowDataSource",
            name="HealthcareWorkflowDataSource",
            knowledge_base_id=self.knowledge_base.attr_knowledge_base_id,
            data_source_configuration=bedrock.CfnDataSource.DataSourceConfigurationProperty(
                type="S3",
                s3_configuration=bedrock.CfnDataSource.S3DataSourceConfigurationProperty(
                    bucket_arn=processed_bucket.bucket_arn,
                    bucket_owner_account_id=self.account,
                ),

            ),
            vector_ingestion_configuration=bedrock.CfnDataSource.VectorIngestionConfigurationProperty(
                custom_transformation_configuration=None,
                context_enrichment_configuration=None,
                parsing_configuration=bedrock.CfnDataSource.ParsingConfigurationProperty(
                    parsing_strategy="BEDROCK_DATA_AUTOMATION",
                    bedrock_data_automation_configuration=bedrock.CfnDataSource.BedrockDataAutomationConfigurationProperty(
                        parsing_modality="MULTIMODAL",
                    )
                ),
                chunking_configuration=bedrock.CfnDataSource.ChunkingConfigurationProperty(
                    chunking_strategy="SEMANTIC",
                    semantic_chunking_configuration=bedrock.CfnDataSource.SemanticChunkingConfigurationProperty(
                        breakpoint_percentile_threshold=90,
                        buffer_size=1,
                        max_tokens=512,
                    )
                )
            ),
            data_deletion_policy="DELETE"
        )

        # Create ECR asset for agent container
        self.agent_container_asset = ecr_assets.DockerImageAsset(
            self,
            "HealthcareAssistantContainer",
            directory=str(Path(__file__).parent.parent.parent / "agents"),
            file="Dockerfile",
            platform=ecr_assets.Platform.LINUX_ARM64,
            build_args={
                "BUILDPLATFORM": "linux/arm64",
                "TARGETPLATFORM": "linux/arm64"
            }
        )

        # Create CloudWatch log group for agent runtime
        self.agent_log_group = logs.LogGroup(
            self,
            "HealthcareAssistantLogGroup",
            log_group_name="/aws/bedrock/agentcore/healthcare-assistant",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY
        )

        # # Create AgentCore Runtime
        # self.agent_runtime = self.create_agent_runtime()

        # # Create CloudFormation outputs
        # self.create_outputs()

    def create_knowledge_base_role(self):
        """
        Create the role for the knowledge base with complete permissions for Aurora and S3.
        Based on: https://docs.aws.amazon.com/bedrock/latest/userguide/kb-permissions.html
        """
        knowledge_base_role = iam.Role(
            self,
            "HealthcareWorkflowKnowledgeBaseRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
        )

        # Allow Bedrock to invoke embedding models
        knowledge_base_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["bedrock:InvokeModel"],
                resources=[
                    f"arn:aws:bedrock:{self.region}::foundation-model/*"
                ],
            )
        )

        # Complete RDS permissions for Aurora Serverless v2 with Knowledge Base
        knowledge_base_role.add_to_policy(
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
                    self.database_cluster.cluster_arn,
                    f"{self.database_cluster.cluster_arn}:*"
                ],
            )
        )

        # RDS describe permissions (these require broader resource access)
        knowledge_base_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "rds:DescribeDBClusters",
                    "rds:DescribeDBInstances",
                    "rds:DescribeDBClusterParameters",
                    "rds:DescribeDBParameters",
                    "rds:DescribeDBSubnetGroups",
                    "rds:ListTagsForResource",
                    "rds:DescribeDBClusterEndpoints",
                    "rds:DescribeDBClusterParameterGroups",
                    "rds:DescribeDBParameterGroups"
                ],
                # RDS describe actions require * resource for validation
                resources=["*"],
            )
        )

        # Allow access to Secrets Manager for RDS credentials
        knowledge_base_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret"
                ],
                resources=[
                    self.bedrock_user_secret.secret_arn if self.bedrock_user_secret else self.database_cluster.secret.secret_arn
                ],
            )
        )

        # Complete S3 permissions for data sources and supplemental data
        knowledge_base_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetObject",
                    "s3:GetObjectVersion",
                    "s3:ListBucket",
                    "s3:GetBucketLocation",
                    "s3:GetBucketNotification",
                    "s3:ListBucketVersions"
                ],
                resources=[
                    self.processed_bucket.bucket_arn,
                    f"{self.processed_bucket.bucket_arn}/*",
                    self.supplemental_data_storage.bucket_arn,
                    f"{self.supplemental_data_storage.bucket_arn}/*"
                ],
            )
        )

        # Allow EC2 permissions for VPC and security group validation
        knowledge_base_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ec2:DescribeVpcs",
                    "ec2:DescribeSubnets",
                    "ec2:DescribeSecurityGroups",
                    "ec2:DescribeNetworkInterfaces"
                ],
                resources=["*"],  # EC2 describe actions require * resource
            )
        )

        # Allow CloudWatch Logs for Knowledge Base operations
        knowledge_base_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=[
                    f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/bedrock/*"
                ],
            )
        )

        return knowledge_base_role.role_arn

    def create_agent_runtime(self):
        """
        Create Bedrock AgentCore Runtime for healthcare assistant.
        """
        # Create IAM role for agent runtime
        agent_runtime_role = self.create_agent_runtime_role()

        # Create AgentCore Runtime
        agent_runtime = agentcore.CfnRuntime(
            self,
            "HealthcareAssistantRuntime",
            agent_runtime_name="healthcare-assistant",
            agent_runtime_artifact=agentcore.CfnRuntime.AgentRuntimeArtifactProperty(
                container_configuration=agentcore.CfnRuntime.ContainerConfigurationProperty(
                    container_uri=self.agent_container_asset.image_uri
                )
            ),
            network_configuration=agentcore.CfnRuntime.NetworkConfigurationProperty(
                network_mode="PUBLIC"
            ),
            role_arn=agent_runtime_role.role_arn,
            environment_variables=self.get_agent_environment_variables(),
            # Guardrails configuration for PII/PHI protection
            guardrail_configuration=agentcore.CfnRuntime.GuardrailConfigurationProperty(
                guardrail_identifier="",  # TODO: To be configured during deployment
                guardrail_version=""  # TODO: To be configured during deployment
            )
        )

        # Add dependency on knowledge base
        agent_runtime.node.add_dependency(self.knowledge_base)

        return agent_runtime

    def create_agent_runtime_role(self):
        """
        Create IAM role for AgentCore Runtime with necessary permissions.
        """
        agent_runtime_role = iam.Role(
            self,
            "HealthcareAssistantRuntimeRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            description="Role for Healthcare Assistant AgentCore Runtime"
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
                    f"arn:aws:bedrock:{self.region}:{self.account}:knowledge-base/{self.knowledge_base.attr_knowledge_base_id}"
                ]
            )
        )

        # Bedrock Guardrails permissions
        agent_runtime_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:ApplyGuardrail"
                ],
                resources=[
                    f"arn:aws:bedrock:{self.region}:{self.account}:guardrail/*"
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
                    self.supplemental_data_storage.bucket_arn,
                    f"{self.supplemental_data_storage.bucket_arn}/*"
                ]
            )
        )

        # CloudWatch Logs permissions
        agent_runtime_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=[
                    self.agent_log_group.log_group_arn,
                    f"{self.agent_log_group.log_group_arn}:*"
                ]
            )
        )

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

        return agent_runtime_role

    def get_agent_environment_variables(self) -> dict:
        """
        Return environment variables for agent runtime configuration.
        Values are left empty for manual configuration during deployment.
        """
        return {
            # Model Configuration - Values to be set during deployment
            "MODEL_ID": "",  # TODO: e.g., "anthropic.claude-3-5-sonnet-20241022-v2:0"
            "MODEL_TEMPERATURE": "",  # TODO: e.g., "0.1"
            "MODEL_MAX_TOKENS": "",  # TODO: e.g., "4096"
            "MODEL_TOP_P": "",  # TODO: e.g., "0.9"

            # Knowledge Base Configuration - Populated by CDK
            "KNOWLEDGE_BASE_ID": self.knowledge_base.attr_knowledge_base_id,
            "SUPPLEMENTAL_DATA_BUCKET": self.supplemental_data_storage.bucket_name,

            # API Configuration - Populated by CDK
            "HEALTHCARE_API_ENDPOINT": self.api_gateway_endpoint or "",  # API Gateway endpoint URL

            # Database Configuration - Populated by CDK
            "DATABASE_CLUSTER_ARN": self.database_cluster.cluster_arn,
            "DATABASE_SECRET_ARN": self.database_cluster.secret.secret_arn,

            # Agent Configuration - Values to be set during deployment
            "DEFAULT_LANGUAGE": "",  # TODO: e.g., "es-LATAM"
            "STREAMING_ENABLED": "",  # TODO: e.g., "true"
            "SESSION_TIMEOUT_MINUTES": "",  # TODO: e.g., "30"

            # Guardrails Configuration - Values to be set during deployment
            "GUARDRAIL_ID": "",  # TODO: Bedrock Guardrail ID for PII/PHI protection
            "GUARDRAIL_VERSION": "",  # TODO: Guardrail version

            # Observability Configuration - Values to be set during deployment
            "ENABLE_TRACING": "",  # TODO: e.g., "true"
            "LOG_LEVEL": "",  # TODO: e.g., "INFO"
            "METRICS_NAMESPACE": "",  # TODO: e.g., "Healthcare/Agents"
        }

    def get_guardrail_configuration(self) -> dict:
        """
        Return guardrail configuration for PII/PHI protection.
        Values to be configured during deployment.
        """
        return {
            "guardrail_identifier": "",  # TODO: To be set during deployment
            "guardrail_version": ""  # TODO: To be set during deployment
        }

    def create_outputs(self):
        """
        Create CloudFormation outputs for the assistant stack.
        """
        CfnOutput(
            self,
            "KnowledgeBaseId",
            value=self.knowledge_base.attr_knowledge_base_id,
            description="Bedrock Knowledge Base ID"
        )

        CfnOutput(
            self,
            "SupplementalDataBucket",
            value=self.supplemental_data_storage.bucket_name,
            description="S3 bucket for supplemental data storage"
        )

        CfnOutput(
            self,
            "AgentRuntimeArn",
            value=self.agent_runtime.attr_agent_runtime_arn,
            description="Healthcare Assistant AgentCore Runtime ARN"
        )

        CfnOutput(
            self,
            "AgentContainerImageUri",
            value=self.agent_container_asset.image_uri,
            description="ECR image URI for agent container"
        )

        CfnOutput(
            self,
            "AgentLogGroupName",
            value=self.agent_log_group.log_group_name,
            description="CloudWatch log group for agent runtime"
        )
