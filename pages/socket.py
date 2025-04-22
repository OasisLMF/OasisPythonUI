import logging
import json
from os.path import isfile
import streamlit as st
from modules.nav import SidebarNav
from oasislmf.platform_api.client import APIClient
import websockets
import asyncio
from urllib.parse import urljoin
import os
import time

logger = logging.getLogger(__name__)

if isfile("ui-config.json"):
    with open("ui-config.json") as f:
        ui_config = json.load(f)
else:
    ui_config = {}

st.set_page_config(
    page_title = "Socket",
    layout = "centered"
)

SidebarNav()

agree = st.checkbox("I agree")

if agree:
    st.write("Great!")

'## Testing Socket'

api_url = os.environ.get('API_URL', 'http://localhost:8000')
ws_url = os.environ.get('WS_URL', 'ws://localhost:8001/ws/')
uri = urljoin(ws_url, 'v2/queue-status/')

if 'client' not in st.session_state:
    client = APIClient(api_url=api_url)
    st.session_state['client'] = client
else:
    client = st.session_state['client']

st.write(f'Loaded client from {api_url}')
st.write(f'Connecting to websocket at: {uri}')
headers = {'AUTHORIZATION': f'Bearer {client.api.tkn_access}'}

placeholder = st.empty()


async def listen_to_websocket(uri, headers):
    async with websockets.connect(uri, additional_headers=headers, ping_interval=None) as websocket:
        with placeholder.container():
            st.write(f"Connected to {uri}")
        try:
            while True:
                message = await websocket.recv()
                message = json.loads(message)
                with placeholder.container():
                    st.write(f'Message time: {message["time"]}')
                    st.write(message)
        except websockets.exceptions.ConnectionClosed:
            with placeholder:
                st.write("WebSocket connection closed")
try:
    loop = asyncio.get_running_loop()
    st.info('Found running loop')
except RuntimeError:
    st.error('Creating new event loop')
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

st.write(loop.is_running())
st.write('Creating task')
task = loop.create_task(listen_to_websocket(uri, headers))
st.write('Running loop')
loop.run_until_complete(task)
st.write(loop.is_running())

