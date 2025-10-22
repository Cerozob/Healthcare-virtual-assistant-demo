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
from constructs import Construct
import json


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
        bedrock_user_secret = None,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Store references for use in methods
        self.processed_bucket = processed_bucket
        self.database_cluster = database_cluster
        self.db_init_resource = db_init_resource
        self.bedrock_user_secret = bedrock_user_secret

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
                    primary_key_field="id",
                    text_field="chunks",
                    vector_field="embedding",
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

        self.orchestrator_agent = None
        self.information_agent = None
        self.scheduling_agent = None

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
                    "rds-data:RollbackTransaction",
                    "rds:DescribeDBClusters",
                    "rds:DescribeDBInstances",
                    "rds:DescribeDBClusterParameters",
                    "rds:DescribeDBParameters",
                    "rds:DescribeDBSubnetGroups",
                    "rds:ListTagsForResource",
                    "rds:DescribeDBClusterEndpoints"
                ],
                resources=[
                    self.database_cluster.cluster_arn,
                    f"{self.database_cluster.cluster_arn}:*"
                ],
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


