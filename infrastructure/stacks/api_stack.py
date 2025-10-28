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
from aws_cdk import aws_cloudwatch as cloudwatch
from aws_cdk import aws_cloudwatch_actions as cw_actions
from aws_cdk import aws_sns as sns

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
        lambda_functions: dict = None,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Store Lambda functions reference
        self.lambda_functions = lambda_functions or {}

        # Create API Gateway (Lambda functions will be passed from backend stack)
        self._create_api_gateway()

        # Store API endpoint in SSM Parameter Store
        self._create_ssm_parameters()

        # Create outputs
        self._create_outputs()

    @property
    def api_endpoint_url(self) -> str:
        """Get the API Gateway endpoint URL with /v1 path."""
        return f"{self.api.api_endpoint}/v1"

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
                    "X-Amz-Security-Token",
                    "X-Requested-With"
                ],
                max_age=Duration.days(1),
                expose_headers=[
                    "Access-Control-Allow-Origin",
                    "Access-Control-Allow-Methods",
                    "Access-Control-Allow-Headers"
                ]
            )
        )

        # Debug information
        print(
            f"API Stack received functions: {list(self.lambda_functions.keys())}")
        for func_name, func_obj in self.lambda_functions.items():
            print(f"Function {func_name}: {func_obj}")

        # Validate that all required Lambda functions are provided
        required_functions = ["patients", "medics", "exams",
                              "reservations", "files", "agent_integration"]
        missing_functions = []
        for func_name in required_functions:
            if not self.lambda_functions.get(func_name):
                missing_functions.append(func_name)

        if missing_functions:
            raise ValueError(
                f"Required Lambda functions not provided to API stack: {missing_functions}")

        # Create Lambda integrations from passed functions
        patients_integration = HttpLambdaIntegration(
            "PatientsIntegration", self.lambda_functions["patients"])
        medics_integration = HttpLambdaIntegration(
            "MedicsIntegration", self.lambda_functions["medics"])
        exams_integration = HttpLambdaIntegration(
            "ExamsIntegration", self.lambda_functions["exams"])
        reservations_integration = HttpLambdaIntegration(
            "ReservationsIntegration", self.lambda_functions["reservations"])
        files_integration = HttpLambdaIntegration(
            "FilesIntegration", self.lambda_functions["files"])

        # chat_integration removed - using AgentCore instead
        agent_integration = HttpLambdaIntegration(
            "AgentIntegration", self.lambda_functions["agent_integration"])

        # Helper function to create CRUD routes with throttling
        def create_crud_routes(path: str, integration: HttpLambdaIntegration, throttle_settings=None):
            # Collection routes
            self.api.add_routes(
                path=path,
                methods=[apigwv2.HttpMethod.GET, apigwv2.HttpMethod.POST],
                integration=integration
            )

            # Item routes
            self.api.add_routes(
                path=f"{path}/{{id}}",
                methods=[apigwv2.HttpMethod.GET,
                         apigwv2.HttpMethod.PUT, apigwv2.HttpMethod.DELETE],
                integration=integration
            )

        # Create CRUD routes for each resource
        create_crud_routes("/patients", patients_integration)
        create_crud_routes("/medics", medics_integration)
        create_crud_routes("/exams", exams_integration)
        create_crud_routes("/reservations", reservations_integration)

        # Additional reservations routes
        self.api.add_routes(
            path="/reservations/availability",
            methods=[apigwv2.HttpMethod.POST],
            integration=reservations_integration
        )

        # Files routes (custom routes for file operations)
        self.api.add_routes(
            path="/files",
            methods=[apigwv2.HttpMethod.GET],
            integration=files_integration
        )

        self.api.add_routes(
            path="/files/upload",
            methods=[apigwv2.HttpMethod.POST],
            integration=files_integration
        )

        self.api.add_routes(
            path="/files/{id}",
            methods=[apigwv2.HttpMethod.DELETE],
            integration=files_integration
        )

        self.api.add_routes(
            path="/files/{id}/classification",
            methods=[apigwv2.HttpMethod.PUT],
            integration=files_integration
        )

        # AgentCore routes only
        self.api.add_routes(
            path="/agentcore/chat",
            methods=[apigwv2.HttpMethod.POST],
            integration=agent_integration
        )

        self.api.add_routes(
            path="/agentcore/health",
            methods=[apigwv2.HttpMethod.GET],
            integration=agent_integration
        )

        # Create a production stage with throttling
        self.stage = apigwv2.HttpStage(
            self,
            "ProdStage",
            http_api=self.api,
            stage_name="v1",
            auto_deploy=True,
            description="Production stage for healthcare API",
            throttle=apigwv2.ThrottleSettings(
                rate_limit=100,  # requests per second
                burst_limit=200  # burst capacity
            )
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

    @property
    def api_gateway_construct(self) -> apigwv2.HttpApi:
        """Get the API Gateway construct for use in other stacks."""
        return self.api
