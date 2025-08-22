"""
Document Workflow Stack for Healthcare Workflow System.
"""

from aws_cdk import Stack, Duration, RemovalPolicy
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from constructs import Construct
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda
from aws_cdk import aws_ssm as ssm
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as sfn_tasks
from aws_cdk import aws_logs as logs
from infrastructure import custom_steps as sfn_custom

# this contains the document workflow, starting from the eventbridge events
# the workflow itself, and the raw + processed buckets


class DocumentWorkflowStack(Stack):
    """
    Stack for document processing and medical workflow orchestration.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # * EventBridge Role - only for triggering workflows

        self.eventbridge_role = iam.Role(
            self,
            "EventBridgeRole",
            assumed_by=iam.ServicePrincipal("events.amazonaws.com"),
            description="Role for EventBridge to trigger Step Functions workflows",
        )

        # * Step Functions Workflow Role - for executing the workflow

        self.workflow_role = iam.Role(
            self,
            "WorkflowRole",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com"),
            description="Role for Step Functions workflow execution",
        )

        # * S3 Buckets

        self.raw_bucket = s3.Bucket(
            self,
            "RawBucket",
            bucket_name=f"ab2-cerozob-rawdata-{self.region}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            event_bridge_enabled=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        self.processed_bucket = s3.Bucket(
            self,
            "ProcessedBucket",
            bucket_name=f"ab2-cerozob-processeddata-{self.region}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # Create SSM parameters for the processed data bucket
        self.processed_bucket_param = ssm.StringParameter(
            self,
            "ProcessedBucketParameter",
            parameter_name="/healthcare/document-workflow/processed-bucket",
            string_value=self.processed_bucket.bucket_name,
            description="Processed data bucket name for document workflow",
        )

        # * Delete outputs if original data is deleted

        # Create deletion lambda function
        self.deletion_lambda = aws_lambda.Function(
            self,
            "DeletionLambda",
            function_name=f"AB2-AnyHealthcare-DeletionLambda",
            runtime=aws_lambda.Runtime.PYTHON_3_13,
            handler="index.lambda_handler",
            code=aws_lambda.Code.from_asset("lambdas/delete_documents"),
            log_group=logs.LogGroup(
                self,
                "DeletionLambdaLogGroup",
                log_group_name=f"/aws/lambda/AB2-AnyHealthcare-DeletionLambda",
                removal_policy=RemovalPolicy.DESTROY,
            ),
        )

        # Create version for deletion lambda
        self.deletion_lambda_version = aws_lambda.Version(
            self,
            "DeletionLambdaVersion",
            lambda_=self.deletion_lambda,
        )

        # Create alias pointing to latest version
        self.deletion_lambda_alias = aws_lambda.Alias(
            self,
            "DeletionLambdaAlias",
            alias_name="LATEST",
            version=self.deletion_lambda_version,
        )
        # Grant permissions to the deletion lambda
        self.processed_bucket.grant_read_write(self.deletion_lambda)
        self.raw_bucket.grant_read(self.deletion_lambda)

        # Grant SSM parameter access
        self.processed_bucket_param.grant_read(self.deletion_lambda)

        # Eventbridge rule2, on deletion, remove the outputs from the workflow

        self.event_rule_deletion = events.Rule(
            self,
            "EventRuleDeletion",
            rule_name=f"AB2-AnyHealthcare-EventRule-DeletedDocument",
            event_pattern=events.EventPattern(
                source=["aws.s3"],
                detail_type=["Object Deleted"],
                detail={"bucket": {"name": [self.raw_bucket.bucket_name]}},
            ),
            role=self.eventbridge_role,
            targets=[
                targets.LambdaFunction(self.deletion_lambda_alias, retry_attempts=1)
            ],
            enabled=True,
        )

        # * Use a lambda to decide which processing to make

        self.entrypoint_lambda = aws_lambda.Function(
            self,
            "EntrypointLambda",
            function_name=f"DocumentTypeIdentifier",
            runtime=aws_lambda.Runtime.PYTHON_3_13,
            handler="index.lambda_handler",
            code=aws_lambda.Code.from_asset("lambdas/workflow_entrypoint"),
            log_group=logs.LogGroup(
                self,
                "EntrypointLambdaLogGroup",
                log_group_name=f"/aws/lambda/AB2-AnyHealthcare-EntrypointLambda",
                removal_policy=RemovalPolicy.DESTROY,
            ),
        )

        # Create version for entrypoint lambda
        self.entrypoint_lambda_version = aws_lambda.Version(
            self,
            "EntrypointLambdaVersion",
            lambda_=self.entrypoint_lambda,
        )

        # Create alias pointing to latest version
        self.entrypoint_lambda_alias = aws_lambda.Alias(
            self,
            "EntrypointLambdaAlias",
            alias_name="LATEST",
            version=self.entrypoint_lambda_version,
        )

        # Grant permissions to the entrypoint lambda
        self.raw_bucket.grant_read(self.entrypoint_lambda)

        # * First step: lambda invocation
        # Step Functions workflow definition
        lambda_step = sfn_tasks.LambdaInvoke(
            self,
            "StartStep",
            lambda_function=self.entrypoint_lambda_alias,
            assign={
                "processing_branch": "{% $states.result.Payload.processing_branch %}",
                "bucket": "{% $states.result.Payload.bucket %}",
                "key": "{% $states.result.Payload.key %}",
                "patient_id": "{% $states.result.Payload.patient_id %}",
                "unique_id": "{% $uuid() %}",
            },
        )

        # Define processing branches

        # * HealthScribe Data Access Role
        self.healthscribe_role = iam.Role(
            self,
            "HealthScribeDataAccessRole",
            assumed_by=iam.ServicePrincipal("transcribe.amazonaws.com"),
            description="Role for HealthScribe to access S3 buckets",
        )

        # Grant HealthScribe role permissions to read from raw bucket and write to processed bucket
        self.raw_bucket.grant_read(self.healthscribe_role)
        self.processed_bucket.grant_read_write(self.healthscribe_role)

        # * HealthScribe workflow: Complete chain with file processing and cleanup
        healthscribe_step = sfn_custom.HealthScribe.buildStepChain(
            self,
            "HealthScribeWorkflow",
            output_bucket=self.processed_bucket,
            healthscribe_role=self.healthscribe_role,
        )

        # * Bedrock Data Automation Step: File processing and data storage
        # TODO implement
        # TODO use a custom construct for the BDA Configuration
        bda_step = sfn.Succeed(
            self,
            "BDAStepFunctions",
            comment="Placeholder step for Bedrock Data Automation",
        )

        # * Comprehend Medical workflow: Complete chain with file processing and cleanup
        # TODO do this
        comprehendmedical_step = sfn.Succeed(
            self,
            "ComprehendMedicalStep",
            comment="Placeholder step for Amazon Comprehend Medical",
        )

        # Choice logic based on processing_branch variable
        exec_branch_choice = (
            sfn.Choice(self, "ExecutionBranchChoice")
            .when(
                sfn.Condition.jsonata('{% $processing_branch = "audio" %}'),
                healthscribe_step,
            )
            .when(
                sfn.Condition.jsonata('{% $processing_branch = "document" %}'),
                bda_step,
            )
            .when(
                sfn.Condition.jsonata('{% $processing_branch = "passthrough" %}'),
                comprehendmedical_step,
            )
            .otherwise(
                # fail if the file did not match anything or if the lambda errored
                sfn.Fail(
                    self, "InvalidProcessingBranch", error="InvalidProcessingBranch"
                )
            )
        )  # Default fallback

        workflow_definition = lambda_step.next(exec_branch_choice)

        # Define the workflow
        chainable_definition = sfn.DefinitionBody.from_chainable(
            chainable=workflow_definition
        )

        # Create the Step Functions state machine
        self.workflow = sfn.StateMachine(
            self,
            "DocumentWorkflow",
            state_machine_name=f"AB2-AnyHealthcare-DocumentWorkflowV6",
            definition_body=chainable_definition,
            query_language=sfn.QueryLanguage.JSONATA,
            logs=sfn.LogOptions(
                destination=logs.LogGroup(
                    self,
                    "WorkflowLogGroup",
                    log_group_name=f"/aws/stepfunctions/AB2-AnyHealthcare-DocumentWorkflow",
                    retention=logs.RetentionDays.ONE_WEEK,
                    removal_policy=RemovalPolicy.DESTROY,
                ),
                level=sfn.LogLevel.ALL,
            ),
            tracing_enabled=True,
            removal_policy=RemovalPolicy.DESTROY,
            role=self.workflow_role,
        )

        # Grant permissions to the workflow role

        # Grant S3 permissions for both buckets
        self.raw_bucket.grant_read(self.workflow_role)
        self.processed_bucket.grant_read_write(self.workflow_role)

        # Grant permission to pass the HealthScribe role
        self.healthscribe_role.grant_pass_role(self.workflow_role)

        # Grant HealthScribe permissions to workflow role
        self.workflow_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "transcribe:StartMedicalScribeJob",
                    "transcribe:GetMedicalScribeJob",
                    "transcribe:ListMedicalScribeJobs",
                ],
                resources=["*"],
            )
        )

        # Grant EventBridge permission to execute the state machine
        self.workflow.grant_start_execution(self.eventbridge_role)

        # Eventbridge rule1, on creation, launch the workflow
        self.event_rule_input = events.Rule(
            self,
            "EventRule",
            rule_name=f"AB2-AnyHealthcare-EventRule-ReceivedDocumentInput",
            event_pattern=events.EventPattern(
                source=["aws.s3"],
                detail_type=["Object Created"],
                detail={
                    "bucket": {"name": [self.raw_bucket.bucket_name]},
                    "object": {"key": [{"exists": True}]},
                },
            ),
            targets=[
                targets.SfnStateMachine(self.workflow, role=self.eventbridge_role)
            ],
            enabled=True,
        )
