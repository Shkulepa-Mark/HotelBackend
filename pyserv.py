import asyncio
import websockets

connected_clients = set()

async def handler(ws):
    print("🔌 Клиент подключился:", ws.remote_address)
    connected_clients.add(ws)
    try:
        async for msg in ws:
            print("📩 Получено сообщение от клиента:", msg)
            await ws.send("✅ Сервер получил: " + msg)
    except websockets.exceptions.ConnectionClosed:
        print("❌ Клиент отключился:", ws.remote_address)
    finally:
        connected_clients.remove(ws)

async def main():
    print("🚀 Сервер слушает на порту 8765...")
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()  # keep running

asyncio.run(main())