'''
Module to handle authorisation.
'''
from requests.exceptions import HTTPError
from modules.config import retrieve_ui_config
import streamlit as st
from modules.client import ClientInterface
import logging

logger = logging.getLogger(__name__)

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
                st.session_state["client_interface"] = ClientInterface(username=st.secrets["user"], password=st.secrets["password"])
            except HTTPError as e:
                logger.error(e)
                st.error("Loading platform failed.")
        return

    # Go to login page
    st.switch_page("app.py")

def quiet_login():
    if "client_interface" in st.session_state:
        return

    if "user" in st.secrets and "password" in st.secrets:
        st.write("Logging in quietly")
        try:
            st.session_state["client_interface"] = ClientInterface(username=st.secrets["user"], password=st.secrets["password"])
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
