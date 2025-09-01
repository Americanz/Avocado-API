import asyncio
from src.features.telegram_bot.poster.poster_service import PosterService


async def test_clients_api():
    service = PosterService()
    # Тест без offset (перші 5 клієнтів)
    clients = await service.get_clients(offset=0, num=5)
    print(f"Clients without offset (first 5): {len(clients)}")
    if clients:
        print(f"First client example: {clients[0]}")
        client_ids = [int(c["client_id"]) for c in clients]
        print(f"Client ID range: {min(client_ids)} - {max(client_ids)}")

    # Тест з offset
    clients_with_offset = await service.get_clients(offset=31000, num=10)
    print(f"Clients with offset=31000 (max 10): {len(clients_with_offset)}")
    if clients_with_offset:
        offset_ids = [int(c["client_id"]) for c in clients_with_offset]
        print(f"Client ID range with offset: {min(offset_ids)} - {max(offset_ids)}")


if __name__ == "__main__":
    asyncio.run(test_clients_api())
