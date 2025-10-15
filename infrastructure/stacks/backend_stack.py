"""
Backend Stack for Healthcare Management System.
Manages only the Aurora PostgreSQL database and related infrastructure.
"""

from aws_cdk import Stack, Duration, RemovalPolicy, CfnOutput
from aws_cdk import aws_rds as rds
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ssm as ssm
from constructs import Construct


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

        # Create VPC with private subnets
        self.vpc = self._create_vpc()

        # Create Aurora Postgres cluster
        self.db_cluster = self._create_database()

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
                                    #   serverless_v2_auto_pause_duration=Duration.minutes(
                                    #       30),
                                      serverless_v2_min_capacity=0.5,
                                      serverless_v2_max_capacity=40,
                                      storage_encrypted=True,
                                      iam_authentication=True
                                      )

        return cluster

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
