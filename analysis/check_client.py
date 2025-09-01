#!/usr/bin/env python3
"""
Quick script to check if specific client exists in database
"""
import sys
import os

from src.core.database.session import get_db_session
from src.features.telegram_bot.models import Client


def check_client():
    with get_db_session() as db:
        # Check for client 31004
        client = db.query(Client).filter(Client.client_id == 31004).first()
        if client:
            print(f'✅ Client 31004 found: {client.client_name or "No name"}')
        else:
            print("❌ Client 31004 not found")

        # Check total clients
        total_clients = db.query(Client).count()
        print(f"📊 Total clients in DB: {total_clients}")


if __name__ == "__main__":
    check_client()
