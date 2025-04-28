"""
Date and time utility functions.
"""
from datetime import datetime, date, time, timedelta
from typing import Optional, Union, Tuple

import pytz


def now() -> datetime:
    """
    Get current UTC datetime.
    
    Returns:
        datetime: Current UTC datetime
    """
    return datetime.now(pytz.UTC)


def today() -> date:
    """
    Get current UTC date.
    
    Returns:
        date: Current UTC date
    """
    return now().date()


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime object to string.
    
    Args:
        dt: Datetime object
        fmt: Format string
    
    Returns:
        str: Formatted datetime string
    """
    return dt.strftime(fmt)


def parse_datetime(dt_str: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """
    Parse string to datetime object.
    
    Args:
        dt_str: Datetime string
        fmt: Format string
    
    Returns:
        datetime: Parsed datetime object
    """
    return datetime.strptime(dt_str, fmt)


def add_timezone(dt: datetime, tz: str = "UTC") -> datetime:
    """
    Add timezone to datetime object.
    
    Args:
        dt: Datetime object
        tz: Timezone name
    
    Returns:
        datetime: Datetime object with timezone
    """
    timezone = pytz.timezone(tz)
    return dt.replace(tzinfo=timezone)


def convert_timezone(dt: datetime, tz: str) -> datetime:
    """
    Convert datetime to another timezone.
    
    Args:
        dt: Datetime object
        tz: Target timezone name
    
    Returns:
        datetime: Datetime object with new timezone
    """
    if dt.tzinfo is None:
        dt = add_timezone(dt)
    
    target_tz = pytz.timezone(tz)
    return dt.astimezone(target_tz)


def get_date_range(
    start_date: Union[date, datetime, str], 
    end_date: Union[date, datetime, str], 
    as_string: bool = False,
    fmt: str = "%Y-%m-%d"
) -> Union[list[date], list[str]]:
    """
    Get list of dates between start_date and end_date (inclusive).
    
    Args:
        start_date: Start date
        end_date: End date
        as_string: Return dates as strings
        fmt: Format string for date strings
    
    Returns:
        list[date] or list[str]: List of dates or date strings
    """
    # Convert to date objects if needed
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, fmt).date()
    elif isinstance(start_date, datetime):
        start_date = start_date.date()
    
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, fmt).date()
    elif isinstance(end_date, datetime):
        end_date = end_date.date()
    
    # Generate date range
    delta = end_date - start_date
    dates = [start_date + timedelta(days=i) for i in range(delta.days + 1)]
    
    # Convert to strings if needed
    if as_string:
        return [d.strftime(fmt) for d in dates]
    
    return dates


def get_month_start_end(
    year: int, 
    month: int
) -> Tuple[datetime, datetime]:
    """
    Get start and end datetime for given month.
    
    Args:
        year: Year
        month: Month
    
    Returns:
        Tuple[datetime, datetime]: Start and end of month
    """
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year
    
    start = datetime(year, month, 1, 0, 0, 0)
    end = datetime(next_year, next_month, 1, 0, 0, 0) - timedelta(seconds=1)
    
    return start, end