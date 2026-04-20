import uuid
from datetime import datetime, timedelta, timezone


def generate_uuid() -> str:
    """Generate unique identifier."""
    return str(uuid.uuid4())


def get_current_timestamp() -> datetime:
    """Get current IST timestamp."""
    IST = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(IST)


def format_datetime(dt: datetime) -> str:
    """Format datetime to ISO string."""
    return dt.isoformat() if dt else None


def parse_datetime(dt_str: str) -> datetime:
    """Parse ISO datetime string."""
    return datetime.fromisoformat(dt_str) if dt_str else None
