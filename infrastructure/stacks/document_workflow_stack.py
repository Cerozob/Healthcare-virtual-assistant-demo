"""
Document Workflow Stack for Healthcare Workflow System.
"""

from aws_cdk import Stack, Duration, RemovalPolicy, CfnOutput
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from constructs import Construct
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda
from aws_cdk import aws_ssm as ssm
from aws_cdk import aws_logs as logs
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_cloudtrail as cloudtrail
from infrastructure.constructs.bda_blueprints_construct import BDABlueprintsConstruct

# this contains the document workflow, starting from the eventbridge events
# the workflow itself, and the raw + processed buckets


class DocumentWorkflowStack(Stack):
    """
    Stack for document processing and medical workflow orchestration.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create BDA blueprints construct
        self.data_automation = BDABlueprintsConstruct(
            self,
            "BDABlueprints"
        )

        # Create BDA project
        self.bda_project = self.data_automation.project
        self.bda_profile_arn = f'arn:aws:bedrock:{self.region}:{self.account}:data-automation-profile/us.data-automation-v1'

        # Simplified architecture - no Step Functions roles needed

        # * S3 Buckets

        # S3 buckets without access logging

        self.raw_bucket = s3.Bucket(
            self,
            "RawBucket",
            bucket_name=f"demo-healthcareva-dfx5-rawdata-{self.region}",
            versioned=False,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            event_bridge_enabled=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            cors=[
                s3.CorsRule(
                    allowed_headers=["*"],
                    allowed_methods=[
                        s3.HttpMethods.GET,
                        s3.HttpMethods.PUT,
                        s3.HttpMethods.POST,
                        s3.HttpMethods.DELETE,
                        s3.HttpMethods.HEAD
                    ],
                    allowed_origins=[
                        "http://localhost:3000",
                        "http://localhost:5173",
                        "https://*.amplifyapp.com",
                        "https://*.cloudfront.net"
                    ],
                    exposed_headers=[
                        "ETag",
                        "x-amz-server-side-encryption",
                        "x-amz-request-id",
                        "x-amz-id-2",
                        # Raw bucket metadata headers
                        "x-amz-meta-auto-classification-enabled",
                        "x-amz-meta-auto-classified",
                        "x-amz-meta-classification-confidence",
                        "x-amz-meta-classification-timestamp",
                        "x-amz-meta-document-category",
                        "x-amz-meta-patient-id",
                        "x-amz-meta-workflow-stage"
                    ],
                    max_age=3000
                )
            ]
        )

        self.processed_bucket = s3.Bucket(
            self,
            "ProcessedBucket",
            bucket_name=f"demo-healthcareva-dfx5-processeddata-{self.region}",
            versioned=False,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            event_bridge_enabled=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            cors=[
                s3.CorsRule(
                    allowed_headers=["*"],
                    allowed_methods=[
                        s3.HttpMethods.GET,
                        s3.HttpMethods.PUT,
                        s3.HttpMethods.POST,
                        s3.HttpMethods.DELETE,
                        s3.HttpMethods.HEAD
                    ],
                    allowed_origins=[
                        "http://localhost:3000",
                        "http://localhost:5173",
                        "https://*.amplifyapp.com",
                        "https://*.cloudfront.net"
                    ],
                    exposed_headers=[
                        "ETag",
                        "x-amz-server-side-encryption",
                        "x-amz-request-id",
                        "x-amz-id-2",
                        # Processed bucket metadata headers
                        "x-amz-meta-auto-classified",
                        "x-amz-meta-classification-confidence",
                        "x-amz-meta-document-category",
                        "x-amz-meta-document-id",
                        "x-amz-meta-patient-id",
                        "x-amz-meta-processing-timestamp",
                        "x-amz-meta-workflow-stage"
                    ],
                    max_age=3000
                )
            ]
        )

        # Create CloudWatch Log Group for CloudTrail S3 API logging
        self.s3_api_log_group = logs.LogGroup(
            self,
            "S3ApiLogGroup",
            log_group_name="/aws/cloudtrail/s3-api-calls",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Create CloudTrail for S3 API logging
        self.s3_cloudtrail = cloudtrail.Trail(
            self,
            "S3ApiCloudTrail",
            trail_name="healthcare-s3-api-trail",
            send_to_cloud_watch_logs=True,
            cloud_watch_log_group=self.s3_api_log_group,
            include_global_service_events=False,
            is_multi_region_trail=False,
            enable_file_validation=True,
        )

        # Add S3 data events for both buckets
        self.s3_cloudtrail.add_s3_event_selector(
            read_write_type=cloudtrail.ReadWriteType.ALL,
            include_management_events=True,
            s3_selector=[
                cloudtrail.S3EventSelector(bucket=self.raw_bucket),
                cloudtrail.S3EventSelector(bucket=self.processed_bucket)

            ]
        )

        # Create SSM parameters for the buckets
        self.processed_bucket_param = ssm.StringParameter(
            self,
            "ProcessedBucketParameter",
            parameter_name="/healthcare/document-workflow/processed-bucket",
            string_value=self.processed_bucket.bucket_name,
            description="Processed data bucket name for document workflow",
        )

        self.raw_bucket_param = ssm.StringParameter(
            self,
            "RawBucketParameter",
            parameter_name="/healthcare/document-workflow/raw-bucket",
            string_value=self.raw_bucket.bucket_name,
            description="Raw data bucket name for document workflow",
        )

        self.bda_trigger_lambda = aws_lambda.Function(
            self,
            "BDATriggerLambda",
            function_name="healthcare-bda-trigger",
            runtime=aws_lambda.Runtime.PYTHON_3_13,
            handler="index.lambda_handler",
            code=aws_lambda.Code.from_asset(
                "lambdas/document_workflow/bda_trigger"),
            timeout=Duration.minutes(2),
            memory_size=128,  # Optimized based on actual usage metrics (max 8.6MB observed)
            environment={
                "PROCESSED_BUCKET_NAME": self.processed_bucket.bucket_name,
                "BDA_PROJECT_ARN": self.bda_project.attr_project_arn,
                "BDA_PROFILE_ARN": self.bda_profile_arn,
                "MEDICAL_RECORD_BLUEPRINT_ARN": self.data_automation.blueprints["document"].attr_blueprint_arn,
                "MEDICAL_IMAGE_BLUEPRINT_ARN": self.data_automation.blueprints["image"].attr_blueprint_arn,
                "MEDICAL_AUDIO_BLUEPRINT_ARN": self.data_automation.blueprints["audio"].attr_blueprint_arn,
                "MEDICAL_VIDEO_BLUEPRINT_ARN": self.data_automation.blueprints["video"].attr_blueprint_arn
            },
            log_group=logs.LogGroup(
                self,
                "BDATriggerLambdaLogGroup",
                log_group_name="/aws/lambda/healthcare-bda-trigger",
                retention=logs.RetentionDays.ONE_WEEK,
                removal_policy=RemovalPolicy.DESTROY,
            )
        )

        # Grant permissions to BDA trigger lambda
        self.raw_bucket.grant_read(self.bda_trigger_lambda)
        self.processed_bucket.grant_write(self.bda_trigger_lambda)

        # Grant Bedrock Data Automation permissions
        self.bda_trigger_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeDataAutomationAsync",
                    "bedrock:GetDataAutomationStatus",
                    "bedrock:ListDataAutomationProjects",
                    "bedrock:GetDataAutomationProject"
                ],
                resources=[
                    self.bda_project.attr_project_arn,
                    self.data_automation.blueprints["document"].attr_blueprint_arn,
                    self.data_automation.blueprints["image"].attr_blueprint_arn,
                    self.data_automation.blueprints["audio"].attr_blueprint_arn,
                    self.data_automation.blueprints["video"].attr_blueprint_arn,
                    f"arn:aws:bedrock:{self.region}:{self.account}:data-automation-project/*",
                    f"arn:aws:bedrock:{self.region}:{self.account}:blueprint/*",
                    f"arn:aws:bedrock:us-east-1:{self.account}:data-automation-profile/us.data-automation-v1",
                    f"arn:aws:bedrock:us-east-2:{self.account}:data-automation-profile/us.data-automation-v1",
                    f"arn:aws:bedrock:us-west-1:{self.account}:data-automation-profile/us.data-automation-v1",
                    f"arn:aws:bedrock:us-west-2:{self.account}:data-automation-profile/us.data-automation-v1"
                ]
            )
        )

        # EventBridge Rule for S3 Object Created events
        # This triggers BDA processing for any file uploaded to the raw bucket
        self.s3_upload_rule = events.Rule(
            self,
            "S3UploadEventRule",
            rule_name="healthcare-s3-upload-trigger",
            description="Trigger BDA processing when files are uploaded to raw bucket",
            event_pattern=events.EventPattern(
                source=["aws.s3"],
                detail_type=["Object Created"],
                detail={
                    "bucket": {
                        "name": [self.raw_bucket.bucket_name]
                    }
                }
            ),
            targets=[
                targets.LambdaFunction(
                    self.bda_trigger_lambda,
                    retry_attempts=2,
                    max_event_age=Duration.hours(2)
                )
            ],
            enabled=True
        )

        # * Data Extraction Lambda Function (Knowledge Base Integration)
        self.extraction_lambda = aws_lambda.Function(
            self,
            "DataExtractionLambda",
            function_name="healthcare-data-extraction",
            runtime=aws_lambda.Runtime.PYTHON_3_13,
            handler="document_workflow.extraction.index.lambda_handler",
            code=aws_lambda.Code.from_asset(
                "lambdas", exclude=["**/__pycache__/**"]),
            timeout=Duration.minutes(10),
            memory_size=256,  # Optimized based on actual usage metrics (max 112MB observed)
            environment={
                "SOURCE_BUCKET_NAME": self.raw_bucket.bucket_name,
                "PROCESSED_BUCKET_NAME": self.processed_bucket.bucket_name,
                "CLASSIFICATION_CONFIDENCE_THRESHOLD": "80"
                # Knowledge Base ID and database configuration will come from SSM parameters
            },
            log_group=logs.LogGroup(
                self,
                "DataExtractionLambdaLogGroup",
                log_group_name="/aws/lambda/healthcare-data-extraction",
                retention=logs.RetentionDays.ONE_WEEK,
                removal_policy=RemovalPolicy.DESTROY,
            ),
        )

        # Grant permissions to extraction lambda
        # For updating original document metadata
        self.raw_bucket.grant_read_write(self.extraction_lambda)
        self.processed_bucket.grant_read_write(self.extraction_lambda)

        # Grant permissions to delete from processed bucket for cleanup operations
        self.extraction_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:DeleteObject",
                    "s3:DeleteObjectVersion"
                ],
                resources=[
                    f"{self.processed_bucket.bucket_arn}/*"
                ]
            )
        )

        # Grant SSM permissions for database and knowledge base configuration
        self.extraction_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ssm:GetParameter",
                    "ssm:GetParameters"
                ],
                resources=[
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/healthcare/database/*",
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/healthcare/knowledge-base/*"
                ]
            )
        )

        # Grant Bedrock Agent permissions for Knowledge Base
        self.extraction_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:StartIngestionJob",
                    "bedrock:GetIngestionJob",
                    "bedrock:ListIngestionJobs",
                    "bedrock:GetKnowledgeBase",
                    "bedrock:ListKnowledgeBases",
                    "bedrock:GetDataSource",
                    "bedrock:ListDataSources"
                ],
                resources=[
                    f"arn:aws:bedrock:{self.region}:{self.account}:knowledge-base/*",
                    f"arn:aws:bedrock:{self.region}:{self.account}:data-source/*"
                ]
            )
        )

        # Grant RDS Data API permissions
        self.extraction_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "rds-data:ExecuteStatement",
                    "rds-data:BatchExecuteStatement"
                ],
                resources=[
                    f"arn:aws:rds:{self.region}:{self.account}:cluster:*"
                ]
            )
        )

        # Grant Secrets Manager permissions
        self.extraction_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "secretsmanager:GetSecretValue"
                ],
                resources=[
                    f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:*"
                ]
            )
        )

        # * EventBridge Rule for BDA Completion Events - Direct to Knowledge Base
        self.bda_completion_rule = events.Rule(
            self,
            "BDACompletionEventRule",
            rule_name="healthcare-bda-completion",
            description="Trigger knowledge base ingestion when BDA processing completes",
            event_pattern=events.EventPattern(
                source=["aws.bedrock"],
                detail_type=["Bedrock Data Automation Job Succeeded"]
            ),
            targets=[
                targets.LambdaFunction(
                    self.extraction_lambda,
                    retry_attempts=2,
                    max_event_age=Duration.hours(2)
                )
            ],
            enabled=True
        )

        # * Data Cleanup Lambda Function
        self.cleanup_lambda = aws_lambda.Function(
            self,
            "DataCleanupLambda",
            function_name="healthcare-data-cleanup",
            runtime=aws_lambda.Runtime.PYTHON_3_13,
            handler="document_workflow.cleanup.index.lambda_handler",
            code=aws_lambda.Code.from_asset(
                "lambdas", exclude=["**/__pycache__/**"]),
            timeout=Duration.minutes(5),
            memory_size=128,  # Optimized based on actual usage metrics
            environment={
                "RAW_BUCKET_NAME": self.raw_bucket.bucket_name,
                "PROCESSED_BUCKET_NAME": self.processed_bucket.bucket_name
            },
            log_group=logs.LogGroup(
                self,
                "DataCleanupLambdaLogGroup",
                log_group_name="/aws/lambda/healthcare-data-cleanup",
                retention=logs.RetentionDays.ONE_WEEK,
                removal_policy=RemovalPolicy.DESTROY,
            ),
        )

        # Grant S3 permissions to cleanup lambda
        self.raw_bucket.grant_read_write(self.cleanup_lambda)
        self.processed_bucket.grant_read_write(self.cleanup_lambda)

        # * EventBridge Rules for S3 Object Deletion Events

        # Rule for raw bucket deletions
        self.raw_bucket_deletion_rule = events.Rule(
            self,
            "RawBucketDeletionRule",
            rule_name="healthcare-raw-bucket-deletion",
            description="Trigger cleanup when files are deleted from raw bucket",
            event_pattern=events.EventPattern(
                source=["aws.s3"],
                detail_type=["Object Deleted"],
                detail={
                    "bucket": {
                        "name": [self.raw_bucket.bucket_name]
                    }
                }
            ),
            targets=[
                targets.LambdaFunction(
                    self.cleanup_lambda,
                    retry_attempts=2,
                    max_event_age=Duration.hours(1)
                )
            ],
            enabled=True
        )

        # Rule for processed bucket deletions
        self.processed_bucket_deletion_rule = events.Rule(
            self,
            "ProcessedBucketDeletionRule",
            rule_name="healthcare-processed-bucket-deletion",
            description="Trigger cleanup when files are deleted from processed bucket",
            event_pattern=events.EventPattern(
                source=["aws.s3"],
                detail_type=["Object Deleted"],
                detail={
                    "bucket": {
                        "name": [self.processed_bucket.bucket_name]
                    }
                }
            ),
            targets=[
                targets.LambdaFunction(
                    self.cleanup_lambda,
                    retry_attempts=2,
                    max_event_age=Duration.hours(1)
                )
            ],
            enabled=True
        )

        CfnOutput(
            self,
            "RawBucketName",
            value=self.raw_bucket.bucket_name,
            description="Name of the S3 bucket for raw data",
        )

        CfnOutput(
            self,
            "ProcessedBucketName",
            value=self.processed_bucket.bucket_name,
            description="Name of the S3 bucket for processed data",
        )

        CfnOutput(
            self,
            "S3ApiLogGroupName",
            value=self.s3_api_log_group.log_group_name,
            description="CloudWatch Log Group for S3 API calls",
        )

        CfnOutput(
            self,
            "S3CloudTrailArn",
            value=self.s3_cloudtrail.trail_arn,
            description="CloudTrail for S3 API logging",
        )

        CfnOutput(
            self,
            "CleanupLambdaName",
            value=self.cleanup_lambda.function_name,
            description="Name of the cleanup Lambda function",
        )
