"""
API Stack for Healthcare System.
Contains API Gateway and Lambda functions for the healthcare management system.
"""

from aws_cdk import Stack, Duration, CfnOutput
from aws_cdk import aws_apigatewayv2 as apigwv2
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from aws_cdk import aws_ssm as ssm

from constructs import Construct
import os


class ApiStack(Stack):
    """
    Stack for API Gateway and Lambda functions.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Lambda functions
        self._create_lambda_functions()
        
        # Create API Gateway
        self._create_api_gateway()
        

        
        # Store API endpoint in SSM Parameter Store
        self._create_ssm_parameters()
        
        # Create outputs
        self._create_outputs()

    @property
    def api_endpoint_url(self) -> str:
        """Get the API Gateway endpoint URL with /v1 path."""
        return f"{self.api.api_endpoint}/v1"

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
        
        # EventBridge policy for document functions
        eventbridge_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["events:PutEvents"],
            resources=[
                f"arn:aws:events:{self.region}:{self.account}:event-bus/default"
            ]
        )

        # Patients Function
        self.patients_function = lambda_.Function(
            self,
            "PatientsFunction",
            function_name="healthcare-patients",
            code=lambda_.Code.from_asset("lambdas/api/patients"),
            handler="handler.lambda_handler",
            log_group=logs.LogGroup(
                self,
                "PatientsLogGroup",
                log_group_name="/aws/lambda/healthcare-patients",
                retention=logs.RetentionDays.ONE_WEEK
            ),
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
            code=lambda_.Code.from_asset("lambdas/api/medics"),
            handler="handler.lambda_handler",
            log_group=logs.LogGroup(
                self,
                "MedicsLogGroup",
                log_group_name="/aws/lambda/healthcare-medics",
                retention=logs.RetentionDays.ONE_WEEK
            ),
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
            code=lambda_.Code.from_asset("lambdas/api/exams"),
            handler="handler.lambda_handler",
            log_group=logs.LogGroup(
                self,
                "ExamsLogGroup",
                log_group_name="/aws/lambda/healthcare-exams",
                retention=logs.RetentionDays.ONE_WEEK
            ),
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
            code=lambda_.Code.from_asset("lambdas/api/reservations"),
            handler="handler.lambda_handler",
            log_group=logs.LogGroup(
                self,
                "ReservationsLogGroup",
                log_group_name="/aws/lambda/healthcare-reservations",
                retention=logs.RetentionDays.ONE_WEEK
            ),
            **lambda_config
        )
        self.reservations_function.add_to_role_policy(ssm_policy)
        self.reservations_function.add_to_role_policy(rds_policy)
        self.reservations_function.add_to_role_policy(secrets_policy)



        # Chat Function (higher memory and timeout)
        self.chat_function = lambda_.Function(
            self,
            "ChatFunction",
            function_name="healthcare-chat",
            code=lambda_.Code.from_asset("lambdas/api/chat"),
            handler="handler.lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            timeout=Duration.seconds(60),
            memory_size=512,
            log_group=logs.LogGroup(
                self,
                "ChatLogGroup",
                log_group_name="/aws/lambda/healthcare-chat",
                retention=logs.RetentionDays.ONE_WEEK
            )
        )
        self.chat_function.add_to_role_policy(ssm_policy)
        self.chat_function.add_to_role_policy(rds_policy)
        self.chat_function.add_to_role_policy(secrets_policy)
        self.chat_function.add_to_role_policy(bedrock_policy)

        # Agent Integration Function
        self.agent_integration_function = lambda_.Function(
            self,
            "AgentIntegrationFunction",
            function_name="healthcare-agent-integration",
            code=lambda_.Code.from_asset("lambdas/api/agent-integration"),
            handler="handler.lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            timeout=Duration.seconds(60),
            memory_size=512,
            log_group=logs.LogGroup(
                self,
                "AgentIntegrationLogGroup",
                log_group_name="/aws/lambda/healthcare-agent-integration",
                retention=logs.RetentionDays.ONE_WEEK
            )
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

        # Document Upload Function
        self.document_upload_function = lambda_.Function(
            self,
            "DocumentUploadFunction",
            function_name="healthcare-document-upload",
            code=lambda_.Code.from_asset("lambdas/api/document-upload"),
            handler="handler.lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_13,
            timeout=Duration.seconds(30),
            memory_size=512,
            log_group=logs.LogGroup(
                self,
                "DocumentUploadLogGroup",
                log_group_name="/aws/lambda/healthcare-document-upload",
                retention=logs.RetentionDays.ONE_WEEK
            )
        )
        self.document_upload_function.add_to_role_policy(ssm_policy)
        self.document_upload_function.add_to_role_policy(rds_policy)
        self.document_upload_function.add_to_role_policy(secrets_policy)
        self.document_upload_function.add_to_role_policy(eventbridge_policy)




    def _create_api_gateway(self) -> None:
        """Create HTTP API Gateway v2 with all endpoints."""
        
        # Create HTTP API with CORS configuration
        self.api = apigwv2.HttpApi(
            self,
            "HealthcareAPI",
            api_name="Healthcare Management API",
            description="HTTP API for healthcare management system",
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_origins=["*"],
                allow_methods=[
                    apigwv2.CorsHttpMethod.GET,
                    apigwv2.CorsHttpMethod.POST,
                    apigwv2.CorsHttpMethod.PUT,
                    apigwv2.CorsHttpMethod.DELETE,
                    apigwv2.CorsHttpMethod.OPTIONS
                ],
                allow_headers=[
                    "Content-Type",
                    "X-Amz-Date", 
                    "Authorization",
                    "X-Api-Key",
                    "X-Amz-Security-Token"
                ],
                max_age=Duration.days(1)
            )
        )

        # Create Lambda integrations
        patients_integration = HttpLambdaIntegration("PatientsIntegration", self.patients_function)
        medics_integration = HttpLambdaIntegration("MedicsIntegration", self.medics_function)
        exams_integration = HttpLambdaIntegration("ExamsIntegration", self.exams_function)
        reservations_integration = HttpLambdaIntegration("ReservationsIntegration", self.reservations_function)

        chat_integration = HttpLambdaIntegration("ChatIntegration", self.chat_function)
        agent_integration = HttpLambdaIntegration("AgentIntegration", self.agent_integration_function)
        document_integration = HttpLambdaIntegration("DocumentIntegration", self.document_upload_function)

        # Helper function to create CRUD routes
        def create_crud_routes(path: str, integration: HttpLambdaIntegration):
            # Collection routes
            self.api.add_routes(
                path=path,
                methods=[apigwv2.HttpMethod.GET, apigwv2.HttpMethod.POST],
                integration=integration
            )
            
            # Item routes
            self.api.add_routes(
                path=f"{path}/{{id}}",
                methods=[apigwv2.HttpMethod.GET, apigwv2.HttpMethod.PUT, apigwv2.HttpMethod.DELETE],
                integration=integration
            )

        # Create CRUD routes for each resource
        create_crud_routes("/patients", patients_integration)
        create_crud_routes("/medics", medics_integration)
        create_crud_routes("/exams", exams_integration)
        create_crud_routes("/reservations", reservations_integration)



        # Chat routes
        self.api.add_routes(
            path="/chat/message",
            methods=[apigwv2.HttpMethod.POST],
            integration=chat_integration
        )
        
        self.api.add_routes(
            path="/chat/sessions",
            methods=[apigwv2.HttpMethod.GET, apigwv2.HttpMethod.POST],
            integration=chat_integration
        )
        
        self.api.add_routes(
            path="/chat/sessions/{id}/messages",
            methods=[apigwv2.HttpMethod.GET],
            integration=chat_integration
        )

        # Agent routes
        self.api.add_routes(
            path="/agent",
            methods=[apigwv2.HttpMethod.GET, apigwv2.HttpMethod.POST],
            integration=agent_integration
        )

        # Document routes
        self.api.add_routes(
            path="/documents/upload",
            methods=[apigwv2.HttpMethod.POST],
            integration=document_integration
        )
        
        self.api.add_routes(
            path="/documents/status/{id}",
            methods=[apigwv2.HttpMethod.GET],
            integration=document_integration
        )


        # Create a production stage
        self.stage = apigwv2.HttpStage(
            self,
            "ProdStage",
            http_api=self.api,
            stage_name="v1",
            auto_deploy=True,
            description="Production stage for healthcare API"
        )



    def _create_ssm_parameters(self) -> None:
        """Store API configuration in SSM Parameter Store."""
        
        # Store the API endpoint URL
        self.api_endpoint_parameter = ssm.StringParameter(
            self,
            "ApiEndpointParameter",
            parameter_name="/healthcare/api/endpoint",
            string_value=f"{self.api.api_endpoint}/v1",
            description="Healthcare API Gateway endpoint URL",
            tier=ssm.ParameterTier.STANDARD
        )

    def _create_outputs(self) -> None:
        """Create CloudFormation outputs."""
        
        CfnOutput(
            self,
            "ApiEndpoint",
            value=f"{self.api.api_endpoint}/v1",
            description="Healthcare HTTP API Gateway endpoint URL"
        )
        
        CfnOutput(
            self,
            "ApiEndpointParameterName",
            value=self.api_endpoint_parameter.parameter_name,
            description="SSM Parameter name for API endpoint"
        )
        
        CfnOutput(
            self,
            "ApiId",
            value=self.api.api_id,
            description="Healthcare HTTP API Gateway ID"
        )
        
        CfnOutput(
            self,
            "ApiDomainName",
            value=self.api.api_endpoint,
            description="Healthcare HTTP API Gateway domain name"
        )
