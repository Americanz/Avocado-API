"""
Test script for Poster API with products sync
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.features.telegram_bot.poster.service import get_poster_service


async def test_sync():
    """Test sync with products"""
    service = await get_poster_service()

    if not service:
        print("❌ Poster service not configured")
        return

    print("🔄 Testing Poster API sync...")

    # Sync last 1 day transactions
    try:
        stats = await service.sync_recent_transactions(days_back=1)
        print(f"✅ Sync completed: {stats}")

        if stats.get("products_synced", 0) > 0:
            print(f"🛍️ Products synced: {stats['products_synced']}")
        else:
            print("⚠️ No products were synced")

    except Exception as e:
        print(f"❌ Error during sync: {e}")


if __name__ == "__main__":
    asyncio.run(test_sync())
