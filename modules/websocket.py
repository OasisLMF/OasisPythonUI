import asyncio
from oasislmf.platform_api.client import APIClient
import websockets

async def listen_to_websocket(uri, headers):
    async with websockets.connect(uri, additional_headers=headers, ping_interval=None) as websocket:
        print(f"Connected to {uri}")
        try:
            while True:
                message = await websocket.recv()
                print(f"Received: {message}")
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed")

if __name__ == "__main__":
    uri = 'ws://localhost:8001/ws/v2/queue-status/'
    oasis_client = APIClient()
    headers = {'AUTHORIZATION': f'Bearer {oasis_client.api.tkn_access}'}
    asyncio.run(listen_to_websocket(uri, headers))
