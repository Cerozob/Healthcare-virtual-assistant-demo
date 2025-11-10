"""
Bedrock Knowledge Base Construct for Healthcare Workflow System.
"""

from aws_cdk import RemovalPolicy, CustomResource
from aws_cdk import aws_bedrock as bedrock
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_rds as rds
from constructs import Construct


class BedrockKnowledgeBaseConstruct(Construct):
    """
    Construct for creating Bedrock Knowledge Base with RDS storage and S3 data sources.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        processed_bucket: s3.Bucket,
        database_cluster: rds.DatabaseCluster,
        bedrock_user_secret,
        db_init_resource: CustomResource = None,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.processed_bucket = processed_bucket
        self.database_cluster = database_cluster
        self.bedrock_user_secret = bedrock_user_secret
        self.db_init_resource = db_init_resource


        # Create embeddings model
        self.embeddings_model = bedrock.FoundationModel.from_foundation_model_id(
            self, "EmbeddingsModel",
            bedrock.FoundationModelIdentifier.AMAZON_TITAN_EMBED_TEXT_V2_0
        )

        # Create knowledge base role
        self.knowledge_base_role = self._create_knowledge_base_role()

        # Create knowledge base configuration
        knowledge_base_config = self._create_knowledge_base_configuration()

        # Create storage configuration
        storage_config = self._create_storage_configuration()

        # Create the knowledge base
        self.knowledge_base = bedrock.CfnKnowledgeBase(
            self,
            "HealthcareWorkflowKnowledgeBase",
            knowledge_base_configuration=knowledge_base_config,
            storage_configuration=storage_config,
            name="HealthcareWorkflowKnowledgeBaseV2",
            role_arn=self.knowledge_base_role.role_arn
        )

        # Add dependencies
        if self.db_init_resource:
            self.knowledge_base.node.add_dependency(self.db_init_resource)
        self.knowledge_base.node.add_dependency(self.database_cluster)
        self.knowledge_base.node.add_dependency(self.knowledge_base_role)

        # Create data source
        self.data_source = self._create_data_source()

    def _create_knowledge_base_configuration(self) -> bedrock.CfnKnowledgeBase.KnowledgeBaseConfigurationProperty:
        """Create the knowledge base configuration with vector settings."""
        return bedrock.CfnKnowledgeBase.KnowledgeBaseConfigurationProperty(
            type="VECTOR",
            vector_knowledge_base_configuration=bedrock.CfnKnowledgeBase.VectorKnowledgeBaseConfigurationProperty(
                embedding_model_arn=self.embeddings_model.model_arn,
                embedding_model_configuration=bedrock.CfnKnowledgeBase.EmbeddingModelConfigurationProperty(
                    bedrock_embedding_model_configuration=bedrock.CfnKnowledgeBase.BedrockEmbeddingModelConfigurationProperty(
                        dimensions=1024,
                        embedding_data_type="FLOAT32"
                    )
                ),
                supplemental_data_storage_configuration=None # BDA takes care of this
            )
        )

    def _create_storage_configuration(self) -> bedrock.CfnKnowledgeBase.StorageConfigurationProperty:
        """Create the RDS storage configuration."""
        return bedrock.CfnKnowledgeBase.StorageConfigurationProperty(
            type="RDS",
            rds_configuration=bedrock.CfnKnowledgeBase.RdsConfigurationProperty(
                credentials_secret_arn=self.bedrock_user_secret.secret_arn,
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

    def _create_data_source(self) -> bedrock.CfnDataSource:
        """Create the S3 data source for the knowledge base."""
        return bedrock.CfnDataSource(
            self,
            "HealthcareWorkflowDataSource",
            name="HealthcareWorkflowDataSource",
            knowledge_base_id=self.knowledge_base.attr_knowledge_base_id,
            data_source_configuration=bedrock.CfnDataSource.DataSourceConfigurationProperty(
                type="S3",
                s3_configuration=bedrock.CfnDataSource.S3DataSourceConfigurationProperty(
                    bucket_arn=self.processed_bucket.bucket_arn,
                    bucket_owner_account_id=self.account,
                ),
            ),
            vector_ingestion_configuration=bedrock.CfnDataSource.VectorIngestionConfigurationProperty(
                custom_transformation_configuration=None,
                context_enrichment_configuration=None,
                parsing_configuration=None,
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

    def _create_knowledge_base_role(self) -> iam.Role:
        """
        Create the IAM role for the knowledge base with complete permissions for Aurora and S3.
        Based on: https://docs.aws.amazon.com/bedrock/latest/userguide/kb-permissions.html
        """
        knowledge_base_role = iam.Role(
            self,
            "KnowledgeBaseRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            description="IAM role for Bedrock Knowledge Base with minimal required permissions"
        )

        # Allow Bedrock to invoke specific embedding model (matches working policy)
        knowledge_base_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["bedrock:InvokeModel"],
                resources=[
                    f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v2:0"
                ],
            )
        )

        # RDS Data API permissions (matches working policy exactly)
        knowledge_base_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "rds-data:BatchExecuteStatement",
                    "rds-data:ExecuteStatement"
                ],
                resources=[
                    self.database_cluster.cluster_arn
                ],
            )
        )

        # RDS describe permissions (matches working policy exactly)
        knowledge_base_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "rds:DescribeDBClusters"
                ],
                resources=[
                    self.database_cluster.cluster_arn,
                    # Also allow with wildcard for CloudFormation validation
                    f"arn:aws:rds:{self.region}:{self.account}:cluster/*"
                ],
            )
        )

        # Secrets Manager permissions (matches working policy exactly)
        knowledge_base_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue"
                ],
                resources=[
                    self.bedrock_user_secret.secret_arn
                ],
            )
        )

        # S3 permissions with account conditions (matches working policy exactly)
        knowledge_base_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:ListBucket"
                ],
                resources=[
                    self.processed_bucket.bucket_arn
                ],
                conditions={
                    "StringEquals": {
                        "aws:ResourceAccount": [self.account]
                    }
                }
            )
        )

        knowledge_base_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetObject"
                ],
                resources=[
                    self.processed_bucket.bucket_arn,
                    f"{self.processed_bucket.bucket_arn}/*"
                ],
                conditions={
                    "StringEquals": {
                        "aws:ResourceAccount": [self.account]
                    }
                }
            )
        )


        return knowledge_base_role

    @property
    def knowledge_base_id(self) -> str:
        """Return the knowledge base ID."""
        return self.knowledge_base.attr_knowledge_base_id

    @property
    def region(self) -> str:
        """Return the current region."""
        from aws_cdk import Stack
        return Stack.of(self).region

    @property
    def account(self) -> str:
        """Return the current account."""
        from aws_cdk import Stack
        return Stack.of(self).account
