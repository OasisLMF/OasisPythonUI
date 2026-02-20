'''
Module to handle authorisation.
'''
import os
import requests
from requests.exceptions import HTTPError
from modules.config import retrieve_ui_config
import streamlit as st
from modules.client import ClientInterface
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

    Parameters:
        skip_login (bool): If True, login user
    """
    if "client_interface" in st.session_state:
        return

    if skip_login:
        with st.spinner("Loading platform..."):
            try:
                auth_type = get_auth_type()
                if auth_type != 'simple':
                    st.session_state["client_interface"] = ClientInterface(
                        auth_type="oidc", client_id=st.secrets["client_id"], client_secret=st.secrets["client_secret"])
                else:
                    st.session_state["client_interface"] = ClientInterface(
                        auth_type="simple", username=st.secrets["user"], password=st.secrets["password"])
            except HTTPError as e:
                logger.error(e)
                st.error("Loading platform failed.")
        return

    # Go to login page
    st.switch_page("app.py")


def quiet_login():
    if "client_interface" in st.session_state:
        return

    auth_type = get_auth_type()
    try:
        if auth_type != 'simple':
            if "client_id" in st.secrets and "client_secret" in st.secrets:
                st.session_state["client_interface"] = ClientInterface(
                    auth_type="oidc", client_id=st.secrets["client_id"], client_secret=st.secrets["client_secret"])
        elif "user" in st.secrets and "password" in st.secrets:
            st.session_state["client_interface"] = ClientInterface(auth_type="simple", username=st.secrets["user"], password=st.secrets["password"])
    except HTTPError as e:
        logger.error(e)
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
