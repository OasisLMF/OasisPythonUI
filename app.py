from modules.config import retrieve_ui_config
from modules.authorisation import (
    get_auth_type, exchange_session_token
)
import streamlit as st
from modules.client import ClientInterface
from modules.nav import SidebarNav
from oasis_data_manager.errors import OasisException
from modules.validation import NameValidation, ValidationError, ValidationGroup
import logging

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="OasisLMF",
    layout="centered"
)

SidebarNav()

ui_config = retrieve_ui_config()
auth_type = get_auth_type()

# Handle OIDC callback: server redirects here with ?session_token=... after IdP login
if auth_type != 'simple' and "client_interface" not in st.session_state:
    session_token = st.query_params.get("session_token")
    if session_token:
        with st.spinner("Authenticating..."):
            try:
                token_data = exchange_session_token(session_token)
                access_token = token_data['access_token']
                refresh_token = token_data.get('refresh_token') or ''
                client_interface = ClientInterface(access_token=access_token, refresh_token=refresh_token)
                st.session_state["client_interface"] = client_interface
                st.session_state["client"] = client_interface.client
                id_token = token_data.get('id_token')
                if id_token:
                    st.session_state["id_token"] = id_token
                st.query_params.clear()
                st.rerun()
            except Exception as e:
                st.query_params.clear()
                logger.error(f"OIDC login failed: {e}")
                st.error(f"Login failed: {e}")

if ui_config.skip_login:
    with st.spinner("Loading platform..."):
        if auth_type != 'simple':
            client_interface = ClientInterface(auth_type="oidc", client_id=st.secrets["client_id"], client_secret=st.secrets["client_secret"])
        else:
            client_interface = ClientInterface(auth_type="simple", username=st.secrets["user"], password=st.secrets["password"])
    st.session_state["client"] = client_interface.client

cols = st.columns([0.1, 0.8, 0.1])
with cols[1]:
    st.image(image="images/oasis_logo.png")

if "client" in st.session_state:
    post_login_page = ui_config.post_login_page
    if post_login_page:
        st.switch_page(post_login_page)
elif auth_type != 'simple':
    st.html('<form action="/api/oidc/authorize/?next=/" style="margin:0">'
            '<button type="submit" style="width:100%">Login</button></form>')
else:
    with st.form("login_form"):
        user = st.text_input("Username", key="username")
        password = st.text_input("Password", key="password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        validations = ValidationGroup()
        validations.add_validation(NameValidation("Username"), user)
        validations.add_validation(NameValidation("Password"), password)

        valid = True
        msg = None
        try:
            validations.validate()
        except ValidationError as e:
            valid = False
            msg = e.message
            logger.error(e)

        if valid:
            try:
                client_interface = ClientInterface(username=user, password=password)
                st.session_state["client"] = client_interface.client
                st.session_state["client_interface"] = client_interface
                st.rerun()
            except OasisException as e:
                st.error("Authentication Failed")
                logger.error(e)
        else:
            st.error(msg)
