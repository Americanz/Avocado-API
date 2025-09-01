import asyncio
from src.features.telegram_bot.poster.poster_service import PosterService


async def test_full_client_sync():
    service = PosterService()

    # Симулюємо sync з початку (offset=0, перших 10 клієнтів)
    print("=== Testing offset-based client sync ===")

    offset = 0
    batch_size = 10
    total_synced = 0

    while True:
        clients = await service.get_clients(
            offset=offset, num=batch_size, order_by="id", sort="asc"
        )

        if not clients:
            print(f"No more clients at offset={offset}")
            break

        client_ids = [int(c["client_id"]) for c in clients]
        print(
            f"Offset {offset}: Got {len(clients)} clients, IDs: {min(client_ids)}-{max(client_ids)}"
        )

        total_synced += len(clients)

        # Simulated sync to DB would happen here
        # client_stats = service.sync_clients_to_db(clients)

        if len(clients) < batch_size:
            print(f"Reached end of data (got {len(clients)} < {batch_size})")
            break

        offset += len(clients)

        # Only do first few batches for testing
        if offset >= 50:
            print("Stopping test after 50 clients")
            break

    print(f"Total clients that would be synced: {total_synced}")


if __name__ == "__main__":
    asyncio.run(test_full_client_sync())
