"""
Validation utility functions.
"""
import re
from typing import Any, Dict, List, Optional, Union

from pydantic import EmailStr, validator


def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email to validate
    
    Returns:
        bool: True if email is valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number to validate
    
    Returns:
        bool: True if phone number is valid, False otherwise
    """
    # Remove any non-digit characters
    phone = re.sub(r'\D', '', phone)
    
    # Check if phone number has valid length (10-15 digits)
    return 10 <= len(phone) <= 15


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
    
    Returns:
        tuple[bool, str]: (True if password is valid, message)
    """
    # Check if password is at least 8 characters long
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    # Check if password contains at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    # Check if password contains at least one lowercase letter
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    # Check if password contains at least one digit
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    # Check if password contains at least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"


def validate_uuid(uuid: str) -> bool:
    """
    Validate UUID format.
    
    Args:
        uuid: UUID to validate
    
    Returns:
        bool: True if UUID is valid, False otherwise
    """
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(pattern, uuid, re.IGNORECASE))


def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
    
    Returns:
        bool: True if URL is valid, False otherwise
    """
    pattern = r'^(https?|ftp)://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))


def validate_date(date: str, fmt: str = "%Y-%m-%d") -> bool:
    """
    Validate date format.
    
    Args:
        date: Date to validate
        fmt: Expected date format
    
    Returns:
        bool: True if date is valid, False otherwise
    """
    from datetime import datetime
    
    try:
        datetime.strptime(date, fmt)
        return True
    except ValueError:
        return False