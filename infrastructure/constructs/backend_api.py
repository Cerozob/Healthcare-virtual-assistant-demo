"""
Backend API Construct for core application APIs.
"""

from constructs import Construct


class BackendAPI(Construct):
    """
    Construct for core backend API Gateway and Lambda functions.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # TODO: Implement backend API functionality
        pass
