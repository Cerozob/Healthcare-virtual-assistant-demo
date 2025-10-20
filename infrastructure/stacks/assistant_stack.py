"""
Assistant Stack for Healthcare Workflow System.
"""

from aws_cdk import Stack, CfnOutput, RemovalPolicy
from aws_cdk import aws_bedrock as bedrock
from aws_cdk import aws_bedrockagentcore as agentcore
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
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
        processed_bucket: s3.IBucket = None,
        database_cluster: rds.DatabaseCluster = None,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

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
                credentials_secret_arn=database_cluster.secret.secret_arn,
                database_name=database_cluster.cluster_resource_identifier,
                resource_arn=database_cluster.cluster_arn,
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
                        parsing_modality="MULTI_MODAL",
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
        Create the role for the knowledge base.
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

        # Allow access to RDS cluster for vector storage
        knowledge_base_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "rds-data:ExecuteStatement",
                    "rds-data:BatchExecuteStatement",
                ],
                resources=[
                    f"arn:aws:rds:{self.region}:{self.account}:cluster:*"
                ],
            )
        )

        # Allow access to Secrets Manager for RDS credentials
        knowledge_base_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue",
                ],
                resources=[
                    f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:*"
                ],
            )
        )

        # Allow S3 access for knowledge base data sources and supplemental data
        knowledge_base_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetObject",
                    "s3:ListBucket",
                ],
                resources=[
                    f"arn:aws:s3:::*",
                    f"arn:aws:s3:::*/*",
                ],
            )
        )

        return knowledge_base_role.role_arn
