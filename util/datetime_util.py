from datetime import datetime, timedelta
from dateutil import parser


def convert_string_to_local_time(timestamp: str) -> datetime:
    """
    Convert a timestamp to the system's local timezone.
    """
    utc_time = parser.isoparse(timestamp)
    local_timezone = datetime.now().astimezone().tzinfo
    local_time = utc_time.astimezone(local_timezone)
    return local_time


def convert_to_local_time(timestamp: datetime) -> datetime:
    """
    Convert a timestamp to the system's local timezone.
    """
    local_timezone = datetime.now().astimezone().tzinfo
    local_time = timestamp.astimezone(local_timezone)
    return local_time


def get_current_local_time() -> datetime:
    """
    Get the current local time.
    """
    local_timezone = datetime.now().astimezone().tzinfo
    local_time = datetime.now().astimezone(local_timezone)
    return local_time


def add_seconds_to_timestamp(timestamp: datetime, seconds: int) -> datetime:
    """
    Add seconds to timestamp
    """
    return timestamp + timedelta(seconds=seconds)
