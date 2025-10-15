"""
Frontend Stack for Healthcare Workflow System.
"""

from aws_cdk import Stack
from aws_cdk import aws_s3_assets as s3_assets
from aws_cdk import aws_amplify_alpha as amplify
from aws_cdk import CfnOutput
from pathlib import Path
from constructs import Construct

# this contains the whole frontend, up to the api gateway (excluding)


class FrontendStack(Stack):
    """
    Stack for React frontend deployment and authentication.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Path to the built frontend dist folder
        dist_dir = str(Path(__file__).parent.parent.parent /
                       "apps" / "frontend" / "dist")

        source_code_asset = s3_assets.Asset(
            self,
            "FrontendSourceCodeAsset",
            path=dist_dir,
        )

        # Create Amplify app first to get the domain
        app = amplify.App(
            self,
            "AnyHealthcareFrontend",
            app_name=f"AB2-AnyHealthcare-Frontend",
            auto_branch_deletion=True,
        )

        # Construct the Amplify URL
        amplify_url = f"https://prod.{app.default_domain}"

        # Add Amplify branch (no environment variables needed)
        prod_branch = app.add_branch(
            "prod",
            auto_build=False,  # No build needed since we're deploying pre-built files
            asset=source_code_asset,
            branch_name="prod",
        )

        # Output the Amplify app URL
        CfnOutput(
            self,
            "AmplifyAppUrl",
            value=amplify_url,
            description="Amplify Frontend Application URL"
        )
