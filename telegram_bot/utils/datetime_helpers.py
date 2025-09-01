"""
DateTime helper utilities for telegram bot
"""

from datetime import datetime
from typing import Union, Optional


def format_date(dt: Union[datetime, str, None], format_str: str = "%Y-%m-%d") -> str:
    """
    Format datetime object or string to human readable date format
    
    Args:
        dt: datetime object, string or None
        format_str: strftime format string
    
    Returns:
        Formatted date string or "N/A" for None values
    """
    if dt is None:
        return "N/A"
    
    if hasattr(dt, 'strftime'):
        # It's a datetime object
        return dt.strftime(format_str)
    
    # It's a string, try to extract date part
    dt_str = str(dt)
    if len(dt_str) >= 10:
        return dt_str[:10]  # Extract YYYY-MM-DD part
    
    return dt_str or "N/A"


def format_datetime(dt: Union[datetime, str, None], format_str: str = "%Y-%m-%d %H:%M") -> str:
    """
    Format datetime object or string to human readable datetime format
    
    Args:
        dt: datetime object, string or None  
        format_str: strftime format string
    
    Returns:
        Formatted datetime string or "N/A" for None values
    """
    if dt is None:
        return "N/A"
    
    if hasattr(dt, 'strftime'):
        # It's a datetime object
        return dt.strftime(format_str)
    
    # It's a string, try to extract datetime part
    dt_str = str(dt)
    if len(dt_str) >= 16:
        return dt_str[:16]  # Extract YYYY-MM-DD HH:MM part
    elif len(dt_str) >= 10:
        return dt_str[:10]  # At least get the date
    
    return dt_str or "N/A"


__all__ = ["format_date", "format_datetime"]