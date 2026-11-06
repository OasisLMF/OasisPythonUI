"""Module to handle authorisation."""
import os
import requests
from oasis_data_manager.errors import OasisException
from requests.exceptions import HTTPError
from modules.config import retrieve_ui_config
import streamlit as st
from modules.client import ClientInterface
from modules.credentials import service_client_kwargs
import logging

logger = logging.getLogger(__name__)


def get_auth_type():
    return os.environ.get('API_AUTH_TYPE', 'simple')


def exchange_session_token(session_token):
    """Exchange a session_token (from OIDC callback) for access/refresh tokens.

    The session_token is a short-lived JWT created by the server after
    successful OIDC authentication. POST it to the server's session_token
    endpoint to retrieve the actual tokens.
    """
    api_url = os.environ.get('API_URL', 'http://localhost:8000')
    response = requests.post(
        f"{api_url}/oidc/session_token/",
        json={"session_token": session_token},
    )
    response.raise_for_status()
    return response.json()


def logout():
    """Clear session state and rerun (simple auth logout)."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def handle_login(skip_login=False):
    """Handle the redirect behaviour for login or initalise if login skipped.

    Args:
        skip_login (bool): If True, log in with the service credentials instead of
            redirecting to the login page.
    """
    if "client_interface" in st.session_state:
        return

    if skip_login:
        with st.spinner("Loading platform..."):
            try:
                st.session_state["client_interface"] = ClientInterface(**service_client_kwargs())
            except HTTPError as e:
                logger.error(e)
                st.error("Loading platform failed.")
        return

    # Go to login page
    st.switch_page("app.py")


def quiet_login():
    if "client_interface" in st.session_state:
        return

    try:
        st.session_state["client_interface"] = ClientInterface(**service_client_kwargs())
    except (HTTPError, OasisException) as e:
        logger.error(f'Service login failed: {e}')
    return


def validate_page(page_path):
    ui_config = retrieve_ui_config()

    if page_path in [p['label'] for p in ui_config.pages]:
        return

    logger.warn(f"Page {page_path} not found. Redirecting to {ui_config.post_login_page}")
    redirect_page = ui_config.post_login_page
    if redirect_page is None:
        redirect_page = "app.py"
    st.switch_page(redirect_page)
