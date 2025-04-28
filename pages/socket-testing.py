import logging
import json
from os.path import isfile
import streamlit as st
from modules.nav import SidebarNav
from oasislmf.platform_api.client import APIClient
import websocket
from urllib.parse import urljoin
import os

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

placeholder = st.empty()

def on_open(ws):
    st.write('Websocket connection openend')

def on_message(ws, message):
    data = json.loads(message)
    placeholder.write(f"Time: {data['time']}, Type: {data['type']}")
    logger.debug(data)

def connect_to_websocket(token):
    placeholder.write("Starting websocket")
    ws = websocket.WebSocketApp(
            uri,
            header=[
                f"AUTHORIZATION: Bearer {token}"
            ],
            on_message=on_message,
            on_open=on_open
    )
    ws.run_forever()

if st.button("Start Websocket"):
    placeholder.write("Testing button")
    connect_to_websocket(client.api.tkn_access)
