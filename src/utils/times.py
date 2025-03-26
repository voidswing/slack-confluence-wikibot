# built-in
from datetime import datetime, timezone


def ensure_timezone_aware(dt: datetime) -> datetime:
    """
    datetime 객체를 timezone-aware로 만듭니다.
    이미 timezone-aware라면 그대로 반환하고, 
    naive datetime이라면 UTC로 간주합니다.
    
    Args:
        dt (datetime): 입력 datetime 객체
    
    Returns:
        timezone-aware datetime 객체
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt