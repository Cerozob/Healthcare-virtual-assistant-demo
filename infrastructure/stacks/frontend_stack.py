"""
Frontend Stack for Healthcare Workflow System.
"""

from aws_cdk import Stack
from constructs import Construct

# this contains the whole frontend, up to the api gateway (excluding)


class FrontendStack(Stack):
    """
    Stack for React frontend deployment and authentication.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # TODO: Implement frontend functionality
        pass
