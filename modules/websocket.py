import asyncio
from urllib.parse import urljoin
from oasislmf.platform_api.client import APIClient
import websockets
import os

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
    api_url = os.environ.get('API_URL', 'http://localhost:8000')
    ws_url = os.environ.get('WS_URL', 'ws://localhost:8001/ws/')
    uri = urljoin(ws_url, 'v2/queue-status/')
    oasis_client = APIClient(api_url=api_url)
    print('Loaded client..')
    headers = {'AUTHORIZATION': f'Bearer {oasis_client.api.tkn_access}'}
    print(f'Loading socket from: {uri}')
    asyncio.run(listen_to_websocket(uri, headers))
