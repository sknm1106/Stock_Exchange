from datetime import datetime
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

def get_korea_now() -> datetime:
    """Returns current datetime in Asia/Seoul timezone."""
    return datetime.now(KST)

def get_korea_now_str(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Returns formatted current datetime string in Asia/Seoul timezone."""
    return get_korea_now().strftime(fmt)
