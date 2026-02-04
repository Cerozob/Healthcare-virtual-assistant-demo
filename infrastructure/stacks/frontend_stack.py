from aws_cdk import (
    Stack,
    CfnOutput,
    aws_iam as iam,
)
from constructs import Construct

class FrontendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Service role for AWS Amplify
        amplify_service_role = iam.Role(
            self, "AmplifyServiceRole",
            assumed_by=iam.ServicePrincipal("amplify.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess-Amplify")
            ]
        )

        CfnOutput(
            self, "AmplifyServiceRoleArn",
            value=amplify_service_role.role_arn,
            export_name="AmplifyServiceRoleArn"
        )

        
