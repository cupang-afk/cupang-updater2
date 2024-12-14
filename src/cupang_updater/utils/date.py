from datetime import UTC, datetime

import dateutil.parser

_current_tzinfo = datetime.now().astimezone().tzinfo


def parse_date_string(date_string: str, tz_info=_current_tzinfo) -> datetime:
    """
    Parse a date string into a datetime object,
    and set the timezone to tz_info if given.

    Args:
        date_string (str): The date string to parse.
        tz_info (datetime.tzinfo): The timezone to set in the datetime object
            (default is the current system timezone).

    Returns:
        datetime: The parsed datetime object in the specified timezone.
    """
    return dateutil.parser.parse(date_string).astimezone(tz_info)


def parse_date_timestamp(timestamp: int, tz_info=_current_tzinfo) -> datetime:
    """
    Parse a timestamp into a datetime object, and set the timezone to tz_info if given.

    Args:
        timestamp (int): The timestamp to parse.
        tz_info (datetime.tzinfo): The timezone to set in the datetime object
            (default is the current system timezone).

    Returns:
        datetime: The parsed datetime object in the specified timezone.
    """
    return datetime.fromtimestamp(timestamp, tz_info)


def parse_date_datetime(date: datetime, tz_info=_current_tzinfo) -> datetime:
    """
    Parse a datetime object into another datetime object in a different timezone.

    Args:
        date (datetime): The datetime object to parse.
        tz_info (datetime.tzinfo): The timezone to set in the datetime object
            (default is the current system timezone).

    Returns:
        datetime: The parsed datetime object in the specified timezone.
    """
    return date.astimezone(tz_info)


def parse_date_utc(date: datetime) -> datetime:
    """
    Parse a datetime object into another datetime object in the UTC timezone.

    Args:
        date (datetime): The datetime object to parse.

    Returns:
        datetime: The parsed datetime object in the UTC timezone.
    """
    return date.astimezone(UTC)
