import asyncio
from websockets.sync.client import connect
from oasislmf.platform_api.client import APIClient


def hello():
    ws_path = 'ws://localhost:8001/ws/v2/queue-status/'
    oasis_client = APIClient()
    headers = {'AUTHORIZATION': f'Bearer {oasis_client.api.tkn_access}'}
    with connect(ws_path, additional_headers=headers, ping_interval=None) as ws:
        message = ws.recv()
        print(message)
