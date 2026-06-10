"""Timestamp utilities for consistent date formatting across Unimem."""

from datetime import datetime, timezone

def get_utc_now() -> datetime:
    """Get current datetime in UTC timezone."""
    return datetime.now(timezone.utc)

def get_local_now() -> datetime:
    """Get current datetime in local timezone."""
    return datetime.now().astimezone()

def format_timestamp(dt: datetime) -> str:
    """Format datetime as ISO 8601 string."""
    return dt.isoformat()

def get_timestamp_str() -> str:
    """Get the current local time as an ISO 8601 formatted string."""
    return format_timestamp(get_local_now())
