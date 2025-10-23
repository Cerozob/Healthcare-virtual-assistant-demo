"""
Datetime utilities for Lambda functions.
"""

from datetime import datetime, timezone


def get_current_iso8601() -> str:
    """
    Get current UTC timestamp in ISO 8601 format.
    
    Returns:
        Current datetime in ISO 8601 format (e.g., "2023-10-22T15:30:45.123456Z")
    """
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def get_current_timestamp() -> datetime:
    """
    Get current UTC timestamp.
    
    Returns:
        Current datetime in UTC
    """
    return datetime.now(timezone.utc)
