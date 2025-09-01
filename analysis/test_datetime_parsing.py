"""
Test script for Poster datetime parsing
"""

import sys
import os
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.features.telegram_bot.poster.service import PosterAPIService

# Test the datetime parsing
service = PosterAPIService("test_token", "test_account")

# Test cases
test_timestamps = [
    "1756482781621",  # From your logs
    "1756482923786",
    "1756482761656",
    "2024-08-30 14:30:00",  # Standard format
    "30.08.2024 14:30:00",  # Alternative format
    "",  # Empty
    None,  # None
]

print("Testing Poster datetime parsing:")
print("=" * 50)

for ts in test_timestamps:
    result = service._parse_poster_datetime(ts)
    print(f"Input: {ts}")
    print(f"Output: {result}")
    if result:
        print(f"Formatted: {result.strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 30)
