from aws_cdk import (
    Stack,
    CfnOutput,
    aws_iam as iam,
    SecretValue,
    aws_amplify as amplify
)
from constructs import Construct

class FrontendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str,
                 agentcore_runtime_id: str,
                 raw_s3_bucket_name: str,
                 processed_s3_bucket_name: str,
                 api_base_url: str,
                 db_cluster_identifier: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Service role for AWS Amplify
        amplify_service_role = iam.Role(
            self, "AmplifyServiceRole",
            assumed_by=iam.ServicePrincipal("amplify.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess-Amplify")
            ]
        )

        app = amplify.CfnApp(
            self, "AmplifyApp",
            name="HealthCareAssistantDemo",
            iam_service_role=amplify_service_role.role_arn,
            platform="WEB",
            repository="https://github.com/Cerozob/Healthcare-virtual-assistant-demo.git",
            access_token= SecretValue.secrets_manager("github_access_token_demo").unsafe_unwrap(),
            auto_branch_creation_config=
                amplify.CfnApp.AutoBranchCreationConfigProperty(
                    enable_auto_branch_creation=True,
                    enable_auto_build=True,
                    framework="REACT",
                    auto_branch_creation_patterns=["main"],

                    environment_variables=[
                amplify.CfnApp.EnvironmentVariableProperty(
                    name="VITE_AGENTCORE_RUNTIME_ID",
                value=agentcore_runtime_id),
                amplify.CfnApp.EnvironmentVariableProperty(
                    name="VITE_AWS_REGION",
                value=f"{self.region}"),
                amplify.CfnApp.EnvironmentVariableProperty(
                    name="VITE_API_BASE_URL",
                value=api_base_url),
                amplify.CfnApp.EnvironmentVariableProperty(
                    name="VITE_S3_BUCKET_NAME",
                value=raw_s3_bucket_name),
                amplify.CfnApp.EnvironmentVariableProperty(
                    name="VITE_S3_PROCESSED_BUCKET_NAME",
                value=processed_s3_bucket_name),
                amplify.CfnApp.EnvironmentVariableProperty(
                    name="AMPLIFY_MONOREPO_APP_ROOT",
                value="apps/frontend"),
                amplify.CfnApp.EnvironmentVariableProperty(
                    name="VITE_DB_CLUSTER_IDENTIFIER",
                value=db_cluster_identifier)
            ]
                ),
        )

        branch = amplify.CfnBranch(
            self, "MainBranch",
            app_id=app.attr_app_id,
            branch_name="prod",
            
            environment_variables=[
                amplify.CfnBranch.EnvironmentVariableProperty(
                    name="VITE_AGENTCORE_RUNTIME_ID",
                value=agentcore_runtime_id),
                amplify.CfnBranch.EnvironmentVariableProperty(
                    name="VITE_AWS_REGION",
                value=f"{self.region}"),
                amplify.CfnBranch.EnvironmentVariableProperty(
                    name="VITE_API_BASE_URL",
                value=api_base_url),
                amplify.CfnBranch.EnvironmentVariableProperty(
                    name="VITE_S3_BUCKET_NAME",
                value=raw_s3_bucket_name),
                amplify.CfnBranch.EnvironmentVariableProperty(
                    name="VITE_S3_PROCESSED_BUCKET_NAME",
                value=processed_s3_bucket_name),
            ],
            framework="REACT"
        )

        CfnOutput(
            self, "AmplifyServiceRoleArn",
            value=amplify_service_role.role_arn,
            export_name="AmplifyServiceRoleArn"

        )

        CfnOutput(
            self, "AmplifyAppId",
            value=app.attr_app_id,
            export_name="AmplifyAppId"
        )


        
