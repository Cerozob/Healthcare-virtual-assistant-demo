"""
Patient Data Construct for Aurora PostgreSQL with vector extension.
"""

from constructs import Construct


class AuroraDatabase(Construct):
    """
    Construct for Aurora PostgreSQL cluster with vector extension.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # TODO: Implement patient data storage functionality
        pass
