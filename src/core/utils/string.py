"""
String utility functions.
"""
import re
import string
import random
import unicodedata
from typing import Any, List, Optional, Tuple, Union


def slugify(value: str, allow_unicode: bool = False) -> str:
    """
    Convert text to slug.
    
    Args:
        value: String to convert
        allow_unicode: Whether to allow unicode characters
    
    Returns:
        str: Slugified string
    """
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    
    value = re.sub(r'[^\w\s-]', '', value.lower())
    value = re.sub(r'[-\s]+', '-', value).strip('-_')
    
    return value


def camel_to_snake(name: str) -> str:
    """
    Convert camelCase string to snake_case.
    
    Args:
        name: CamelCase string
    
    Returns:
        str: snake_case string
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def snake_to_camel(name: str) -> str:
    """
    Convert snake_case string to camelCase.
    
    Args:
        name: snake_case string
    
    Returns:
        str: camelCase string
    """
    components = name.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def snake_to_pascal(name: str) -> str:
    """
    Convert snake_case string to PascalCase.
    
    Args:
        name: snake_case string
    
    Returns:
        str: PascalCase string
    """
    components = name.split('_')
    return ''.join(x.title() for x in components)


def generate_random_string(length: int = 10, include_digits: bool = True, include_special: bool = False) -> str:
    """
    Generate random string.
    
    Args:
        length: Length of string
        include_digits: Whether to include digits
        include_special: Whether to include special characters
    
    Returns:
        str: Random string
    """
    # Define character sets
    chars = string.ascii_letters
    if include_digits:
        chars += string.digits
    if include_special:
        chars += string.punctuation
    
    # Generate random string
    return ''.join(random.choice(chars) for _ in range(length))


def truncate(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    Truncate text to max_length characters.
    
    Args:
        text: Text to truncate
        max_length: Maximum length of truncated text
        suffix: Suffix to add to truncated text
    
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length-len(suffix)] + suffix


def extract_numbers(text: str) -> List[int]:
    """
    Extract numbers from text.
    
    Args:
        text: Text to extract numbers from
    
    Returns:
        List[int]: List of numbers
    """
    return [int(n) for n in re.findall(r'\d+', text)]


def to_boolean(value: Union[str, int, bool]) -> bool:
    """
    Convert value to boolean.
    
    Args:
        value: Value to convert
    
    Returns:
        bool: Converted boolean value
    
    Raises:
        ValueError: If value cannot be converted to boolean
    """
    if isinstance(value, bool):
        return value
    
    if isinstance(value, int):
        return bool(value)
    
    true_values = ('yes', 'true', 't', 'y', '1', 'on')
    false_values = ('no', 'false', 'f', 'n', '0', 'off')
    
    if isinstance(value, str):
        value = value.lower()
        if value in true_values:
            return True
        if value in false_values:
            return False
    
    raise ValueError(f"Cannot convert {value} to boolean")