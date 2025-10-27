"""
Backend Stack for Healthcare Management System.
Manages only the Aurora PostgreSQL database and related infrastructure.
"""

from aws_cdk import Stack, Duration, RemovalPolicy, CfnOutput, CustomResource
from aws_cdk import aws_rds as rds
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ssm as ssm
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_assets as s3_assets
from aws_cdk import aws_s3_deployment as s3_deployment
from aws_cdk import aws_secretsmanager as secretsmanager
from aws_cdk import aws_logs as logs
from aws_cdk import custom_resources as cr
from constructs import Construct
import uuid


class BackendStack(Stack):
    """
    Backend stack managing only the Aurora PostgreSQL database.
    All other components (API Gateway, Lambda functions, S3) are managed in separate stacks.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create sample data bucket and upload assets
        self.sample_data_bucket, self.sample_data_deployment = self._create_sample_data_bucket()

        # Create VPC with private subnets
        self.vpc = self._create_vpc()

        # Create Aurora Postgres cluster
        self.db_cluster = self._create_database()

        # Initialize database with schema only (no sample data)
        self.db_init_resource = self._create_database_initialization()

        # Create separate data loading function
        self.data_loader_function = self._create_data_loader_function()

        # Create Lambda functions for API
        self._create_lambda_functions()

        # Create SSM parameters for database configuration
        self._create_ssm_parameters()

        # Create outputs
        self._create_outputs()

    def _create_vpc(self) -> ec2.Vpc:
        """Create VPC with public and private subnets for the healthcare system."""
        return ec2.Vpc(
            self,
            "HealthcareVPC",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=2,  # Use 2 AZs for high availability
            subnet_configuration=[
                # Public subnets for NAT gateways and load balancers
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                # Private subnets for databases and Lambda functions
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
            ],
            nat_gateways=1,  # One NAT gateway for cost optimization
            enable_dns_hostnames=True,
            enable_dns_support=True,
        )

    def _create_database(self) -> rds.ServerlessCluster:
        """Create Aurora PostgreSQL Serverless v2 cluster."""

        # Security group for Aurora
        self.db_security_group = ec2.SecurityGroup(
            self,
            "DatabaseSecurityGroup",
            vpc=self.vpc,
            description="Security group for Aurora PostgreSQL cluster",
            allow_all_outbound=False,
        )

        # Allow inbound connections from VPC (for Lambda functions and other services)
        self.db_security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(self.vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(5432),
            description="Allow PostgreSQL access from VPC CIDR",
        )

        # Create a security group for Lambda functions and other services
        self.lambda_security_group = ec2.SecurityGroup(
            self,
            "LambdaSecurityGroup",
            vpc=self.vpc,
            description="Security group for Lambda functions accessing the database",
            allow_all_outbound=True,
        )

        # Allow Lambda security group to access database
        self.db_security_group.add_ingress_rule(
            peer=self.lambda_security_group,
            connection=ec2.Port.tcp(5432),
            description="Allow Lambda functions to access PostgreSQL",
        )

        cluster = rds.DatabaseCluster(self, "HealthcareDatabase",
                                      engine=rds.DatabaseClusterEngine.aurora_postgres(
                                          version=rds.AuroraPostgresEngineVersion.VER_17_5
                                      ),
                                      vpc=self.vpc,
                                      # Use private subnets for database
                                      vpc_subnets=ec2.SubnetSelection(
                                          subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                                      ),
                                      security_groups=[self.db_security_group],
                                      default_database_name="healthcare",
                                      writer=rds.ClusterInstance.serverless_v2(id="AuroraWriter",
                                                                               instance_identifier="HealthcareDatabase-writer",
                                                                               auto_minor_version_upgrade=True,
                                                                               allow_major_version_upgrade=True,
                                                                               publicly_accessible=False,
                                                                               ),
                                      readers=[rds.ClusterInstance.serverless_v2(id="reader",
                                                                                 instance_identifier="HealthcareDatabase-readers",
                                                                                 auto_minor_version_upgrade=True,
                                                                                 allow_major_version_upgrade=True,
                                                                                 publicly_accessible=False,
                                                                                 scale_with_writer=True
                                                                                 )
                                               ],
                                      enable_data_api=True,
                                      backup=rds.BackupProps(
                                          retention=Duration.days(7)),
                                      removal_policy=RemovalPolicy.DESTROY,
                                      deletion_protection=False,
                                      serverless_v2_auto_pause_duration=Duration.minutes(
                                          5),
                                      serverless_v2_min_capacity=0,
                                      serverless_v2_max_capacity=40,
                                      storage_encrypted=True,
                                      iam_authentication=True
                                      )

        # Create a dedicated secret for bedrock_user following AWS best practices
        self.bedrock_user_secret = secretsmanager.Secret(
            self,
            "BedrockUserSecret",
            description="Credentials for bedrock_user in Aurora PostgreSQL cluster",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"username": "bedrock_user"}',
                generate_string_key="password",
                exclude_characters=" %+~`#$&*()|[]{}:;<>?!'/\"\\",
                password_length=32
            )
        )

        # Add resource policy to allow RDS Data API to access the secret
        # This is required for Bedrock Knowledge Base to work with RDS
        # Following AWS documentation pattern for cross-service access
        self.bedrock_user_secret.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[
                    # Allow service principals for RDS and Bedrock
                    iam.ServicePrincipal("rds.amazonaws.com"),
                    iam.ServicePrincipal("bedrock.amazonaws.com"),
                    # Allow any role in this account (for Knowledge Base role)
                    iam.AccountPrincipal(self.account)
                ],
                actions=[
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret"
                ],
                resources=["*"],
                conditions={
                    "StringEquals": {
                        "secretsmanager:ResourceAccount": self.account
                    }
                }
            )
        )

        return cluster

    def _create_sample_data_bucket(self) -> tuple[s3.Bucket, s3_deployment.BucketDeployment]:
        """Create S3 bucket for sample data and upload sample files using S3 Assets."""

        # Create the sample data bucket
        sample_bucket = s3.Bucket(
            self,
            "SampleDataBucket",
            bucket_name="ab2-cerozob-sampledata-us-east-1",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # Create S3 Asset for the sample data directory
        sample_data_asset = s3_assets.Asset(
            self,
            "SampleDataAsset",
            path="apps/SampleFileGeneration/output",
            # Exclude all non-JSON files at asset level to prevent bundling
            exclude=[
                ".DS_Store",
                "**/.DS_Store",
                "**/*.pdf",
                "**/*.png",
                "**/*.jpg",
                "**/*.jpeg",
                "**/*.gif",
                "**/*.bmp",
                "**/*.tiff",
                "**/*.svg"
            ]
        )

        # Deploy the asset to the sample data bucket
        sample_data_deployment = s3_deployment.BucketDeployment(
            self,
            "SampleDataDeployment",
            sources=[s3_deployment.Source.bucket(
                sample_data_asset.bucket, sample_data_asset.s3_object_key)],
            destination_bucket=sample_bucket,
            destination_key_prefix="output/",
            # Only include JSON profile files - this is the most restrictive approach
            include=["**/*_profile.json"],
            retain_on_delete=False
        )

        return sample_bucket, sample_data_deployment

    def _create_ssm_parameters(self) -> None:
        """Create SSM parameters for database and VPC configuration."""

        # Store database configuration
        self.db_cluster_arn_param = ssm.StringParameter(
            self,
            "DatabaseClusterArnParam",
            parameter_name="/healthcare/database/cluster-arn",
            string_value=self.db_cluster.cluster_arn,
            description="RDS Aurora Cluster ARN for healthcare system",
            tier=ssm.ParameterTier.STANDARD
        )

        self.db_secret_arn_param = ssm.StringParameter(
            self,
            "DatabaseSecretArnParam",
            parameter_name="/healthcare/database/secret-arn",
            string_value=self.db_cluster.secret.secret_arn,
            description="RDS Aurora Secret ARN for healthcare system",
            tier=ssm.ParameterTier.STANDARD
        )

        self.db_name_param = ssm.StringParameter(
            self,
            "DatabaseNameParam",
            parameter_name="/healthcare/database/name",
            string_value="healthcare",
            description="Database name for healthcare system",
            tier=ssm.ParameterTier.STANDARD
        )

        self.bedrock_user_secret_arn_param = ssm.StringParameter(
            self,
            "BedrockUserSecretArnParam",
            parameter_name="/healthcare/database/bedrock-user-secret-arn",
            string_value=self.bedrock_user_secret.secret_arn,
            description="Bedrock user secret ARN for Knowledge Base",
            tier=ssm.ParameterTier.STANDARD
        )

        # Store VPC and security group information
        self.vpc_id_param = ssm.StringParameter(
            self,
            "VpcIdParam",
            parameter_name="/healthcare/vpc/id",
            string_value=self.vpc.vpc_id,
            description="VPC ID for healthcare system",
            tier=ssm.ParameterTier.STANDARD
        )

        self.lambda_security_group_param = ssm.StringParameter(
            self,
            "LambdaSecurityGroupParam",
            parameter_name="/healthcare/vpc/lambda-security-group-id",
            string_value=self.lambda_security_group.security_group_id,
            description="Security group ID for Lambda functions",
            tier=ssm.ParameterTier.STANDARD
        )

        self.db_security_group_param = ssm.StringParameter(
            self,
            "DatabaseSecurityGroupParam",
            parameter_name="/healthcare/vpc/database-security-group-id",
            string_value=self.db_security_group.security_group_id,
            description="Security group ID for database",
            tier=ssm.ParameterTier.STANDARD
        )

        # Store private subnet IDs for Lambda functions
        private_subnet_ids = [
            subnet.subnet_id for subnet in self.vpc.private_subnets]
        self.private_subnets_param = ssm.StringListParameter(
            self,
            "PrivateSubnetsParam",
            parameter_name="/healthcare/vpc/private-subnet-ids",
            string_list_value=private_subnet_ids,
            description="Private subnet IDs for Lambda functions",
            tier=ssm.ParameterTier.STANDARD
        )

    def _create_database_initialization(self) -> CustomResource:
        """
        Create a Lambda function to initialize the database with schema and sample data.
        """
        # Lambda function to initialize the database
        db_init_lambda = lambda_.Function(
            self,
            "DatabaseInitializationFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            # Reduced timeout since no data loading
            timeout=Duration.minutes(5),
            memory_size=256,  # Reduced memory since no data processing
            code=lambda_.Code.from_asset(
                "lambdas", exclude=["**/__pycache__/**"]),
            handler="db_initialization.handler.lambda_handler",

            environment={
                'LOG_LEVEL': 'INFO',
                'BEDROCK_USER_SECRET_ARN': self.bedrock_user_secret.secret_arn
            }
        )

        # Grant Lambda permissions to access RDS and Secrets Manager
        db_init_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "rds-data:ExecuteStatement",
                    "rds-data:BatchExecuteStatement",
                    "rds-data:BeginTransaction",
                    "rds-data:CommitTransaction",
                    "rds:DescribeDBClusters"
                ],
                resources=[self.db_cluster.cluster_arn]
            )
        )

        db_init_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue"
                ],
                resources=[
                    self.db_cluster.secret.secret_arn,
                    self.bedrock_user_secret.secret_arn
                ]
            )
        )

        # Create custom resource to trigger the Lambda
        db_init_provider = cr.Provider(
            self,
            "DatabaseInitProvider",
            on_event_handler=db_init_lambda
        )

        custom_resource = CustomResource(
            self,
            "DatabaseInitialization",
            service_token=db_init_provider.service_token,
            properties={
                'SecretArn': self.db_cluster.secret.secret_arn,
                'ClusterArn': self.db_cluster.cluster_arn,
                'DatabaseName': 'healthcare',
                'TableName': 'ab2_knowledge_base',
                # Forces re-execution on each deployment
                'TriggerUpdate': str(uuid.uuid4())
            }
        )

        # Ensure database initialization waits for sample data to be uploaded
        custom_resource.node.add_dependency(self.sample_data_deployment)

        return custom_resource

    def _create_data_loader_function(self) -> lambda_.Function:
        """
        Create a separate Lambda function to load sample data from S3 into the database
        and upload PDFs/images to the raw bucket for document workflow processing.
        """
        # Lambda function to load sample data
        data_loader_lambda = lambda_.Function(
            self,
            "DataLoaderFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            timeout=Duration.minutes(15),  # Longer timeout for data loading
            memory_size=1024,  # More memory for processing files
            code=lambda_.Code.from_asset(
                "lambdas", exclude=["**/__pycache__/**"]),
            handler="data_loader.handler.lambda_handler",
            environment={
                'LOG_LEVEL': 'INFO',
                'SAMPLE_DATA_BUCKET': self.sample_data_bucket.bucket_name,
                'DATABASE_CLUSTER_ARN': self.db_cluster.cluster_arn,
                'DATABASE_SECRET_ARN': self.db_cluster.secret.secret_arn,
                'DATABASE_NAME': 'healthcare'
            }
        )

        # Grant Lambda permissions to access RDS and Secrets Manager
        data_loader_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "rds-data:ExecuteStatement",
                    "rds-data:BatchExecuteStatement",
                    "rds-data:BeginTransaction",
                    "rds-data:CommitTransaction",
                    "rds:DescribeDBClusters"
                ],
                resources=[self.db_cluster.cluster_arn]
            )
        )

        data_loader_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue"
                ],
                resources=[
                    self.db_cluster.secret.secret_arn
                ]
            )
        )

        # Grant permissions to read from sample data bucket
        self.sample_data_bucket.grant_read(data_loader_lambda)

        return data_loader_lambda

    def _create_lambda_functions(self) -> None:
        """Create all Lambda functions for the healthcare API."""

        # Common Lambda configuration for Python functions
        lambda_config = {
            "runtime": lambda_.Runtime.PYTHON_3_13,
            "timeout": Duration.seconds(30),
            "memory_size": 256,
        }

        # SSM policy for healthcare configuration
        ssm_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "ssm:GetParameter",
                "ssm:GetParameters",
                "ssm:GetParametersByPath"
            ],
            resources=[
                f"arn:aws:ssm:{self.region}:{self.account}:parameter/healthcare/*"
            ]
        )

        # RDS Data API policy
        rds_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "rds-data:ExecuteStatement",
                "rds-data:BatchExecuteStatement"
            ],
            resources=[
                f"arn:aws:rds:{self.region}:{self.account}:cluster:*"
            ]
        )

        # Secrets Manager policy
        secrets_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "secretsmanager:GetSecretValue"
            ],
            resources=[
                f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:*"
            ]
        )

        # Bedrock policy for agent functions
        bedrock_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "bedrock:InvokeAgent",
                "bedrock:InvokeModel"
            ],
            resources=["*"]
        )

        # Patients Function
        self.patients_function = lambda_.Function(
            self,
            "PatientsFunction",
            function_name="healthcare-patients",
            code=lambda_.Code.from_asset(
                "lambdas", exclude=["**/__pycache__/**"]),
            handler="api.patients.handler.lambda_handler",
            **lambda_config
        )
        self.patients_function.add_to_role_policy(ssm_policy)
        self.patients_function.add_to_role_policy(rds_policy)
        self.patients_function.add_to_role_policy(secrets_policy)

        # Medics Function
        self.medics_function = lambda_.Function(
            self,
            "MedicsFunction",
            function_name="healthcare-medics",
            code=lambda_.Code.from_asset(
                "lambdas", exclude=["**/__pycache__/**"]),
            handler="api.medics.handler.lambda_handler",
            **lambda_config
        )
        self.medics_function.add_to_role_policy(ssm_policy)
        self.medics_function.add_to_role_policy(rds_policy)
        self.medics_function.add_to_role_policy(secrets_policy)

        # Exams Function
        self.exams_function = lambda_.Function(
            self,
            "ExamsFunction",
            function_name="healthcare-exams",
            code=lambda_.Code.from_asset(
                "lambdas", exclude=["**/__pycache__/**"]),
            handler="api.exams.handler.lambda_handler",
            **lambda_config
        )
        self.exams_function.add_to_role_policy(ssm_policy)
        self.exams_function.add_to_role_policy(rds_policy)
        self.exams_function.add_to_role_policy(secrets_policy)

        # Reservations Function
        self.reservations_function = lambda_.Function(
            self,
            "ReservationsFunction",
            function_name="healthcare-reservations",
            code=lambda_.Code.from_asset(
                "lambdas", exclude=["**/__pycache__/**"]),
            handler="api.reservations.handler.lambda_handler",
            **lambda_config
        )
        self.reservations_function.add_to_role_policy(ssm_policy)
        self.reservations_function.add_to_role_policy(rds_policy)
        self.reservations_function.add_to_role_policy(secrets_policy)

        # Files Function
        self.files_function = lambda_.Function(
            self,
            "FilesFunction",
            function_name="healthcare-files",
            code=lambda_.Code.from_asset(
                "lambdas", exclude=["**/__pycache__/**"]),
            handler="api.files.handler.lambda_handler",
            environment={
                "CLASSIFICATION_CONFIDENCE_THRESHOLD": "80",
                "KNOWLEDGE_BASE_ID": "healthcare-kb"
            },
            **lambda_config
        )
        self.files_function.add_to_role_policy(ssm_policy)
        self.files_function.add_to_role_policy(rds_policy)
        self.files_function.add_to_role_policy(secrets_policy)

        # Add S3 permissions for file operations
        s3_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            resources=[
                f"arn:aws:s3:::*/*"  # Allow access to all S3 objects
            ]
        )
        self.files_function.add_to_role_policy(s3_policy)

        # Add Bedrock permissions for Knowledge Base queries
        bedrock_kb_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "bedrock:Retrieve",
                "bedrock:RetrieveAndGenerate"
            ],
            resources=[
                f"arn:aws:bedrock:{self.region}:{self.account}:knowledge-base/*"
            ]
        )
        self.files_function.add_to_role_policy(bedrock_kb_policy)

        # Agent Integration Function
        self.agent_integration_function = lambda_.Function(
            self,
            "AgentIntegrationFunction",
            function_name="healthcare-agent-integration",
            code=lambda_.Code.from_asset(
                "lambdas", exclude=["**/__pycache__/**"]),
            handler="api.agent_integration.handler.lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            timeout=Duration.seconds(60),
            memory_size=512,
            environment={
                # AgentCore endpoint will be set via SSM parameter
                "AGENTCORE_ENDPOINT_PARAMETER": "/healthcare/agentcore/endpoint-url"
            }
        )
        self.agent_integration_function.add_to_role_policy(ssm_policy)
        self.agent_integration_function.add_to_role_policy(rds_policy)
        self.agent_integration_function.add_to_role_policy(secrets_policy)
        self.agent_integration_function.add_to_role_policy(bedrock_policy)

        # Add CloudWatch permissions for metrics
        cloudwatch_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "cloudwatch:PutMetricData",
                "cloudwatch:GetMetricStatistics"
            ],
            resources=["*"]
        )
        self.agent_integration_function.add_to_role_policy(cloudwatch_policy)

    def _create_outputs(self) -> None:
        """Create CloudFormation outputs."""

        CfnOutput(
            self,
            "DatabaseClusterArn",
            value=self.db_cluster.cluster_arn,
            description="Aurora PostgreSQL Cluster ARN",
            export_name="HealthcareDatabaseClusterArn"
        )

        CfnOutput(
            self,
            "DatabaseSecretArn",
            value=self.db_cluster.secret.secret_arn,
            description="Aurora PostgreSQL Secret ARN",
            export_name="HealthcareDatabaseSecretArn"
        )

        CfnOutput(
            self,
            "BedrockUserSecretArn",
            value=self.bedrock_user_secret.secret_arn,
            description="Bedrock User Secret ARN for Knowledge Base",
            export_name="HealthcareBedrockUserSecretArn"
        )

        CfnOutput(
            self,
            "DatabaseEndpoint",
            value=self.db_cluster.cluster_endpoint.hostname,
            description="Aurora PostgreSQL Cluster Endpoint",
            export_name="HealthcareDatabaseEndpoint"
        )

        CfnOutput(
            self,
            "VpcId",
            value=self.vpc.vpc_id,
            description="VPC ID for healthcare infrastructure",
            export_name="HealthcareVpcId"
        )

        CfnOutput(
            self,
            "LambdaSecurityGroupId",
            value=self.lambda_security_group.security_group_id,
            description="Security Group ID for Lambda functions",
            export_name="HealthcareLambdaSecurityGroupId"
        )

        CfnOutput(
            self,
            "DatabaseSecurityGroupId",
            value=self.db_security_group.security_group_id,
            description="Security Group ID for database",
            export_name="HealthcareDatabaseSecurityGroupId"
        )

        CfnOutput(
            self,
            "PrivateSubnetIds",
            value=",".join(
                [subnet.subnet_id for subnet in self.vpc.private_subnets]),
            description="Private subnet IDs for Lambda functions",
            export_name="HealthcarePrivateSubnetIds"
        )

        CfnOutput(
            self,
            "SampleDataBucketName",
            value=self.sample_data_bucket.bucket_name,
            description="S3 bucket containing sample data for database initialization",
            export_name="HealthcareSampleDataBucketName"
        )

        CfnOutput(
            self,
            "DataLoaderFunctionName",
            value=self.data_loader_function.function_name,
            description="Lambda function for loading sample data into database and raw bucket",
            export_name="HealthcareDataLoaderFunctionName"
        )
