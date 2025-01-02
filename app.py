import streamlit as st
from modules.nav import SidebarNav
from oasislmf.platform_api.client import APIClient
from oasis_data_manager.errors import OasisException

st.set_page_config(
        page_title = "OasisLMF",
        layout="centered"
)

SidebarNav()

"# OasisLMF UI"

if "client" in st.session_state:
    st.write("## Server Info")
    st.write(st.session_state.client.server_info().json())
else:
    st.write("## Login")
    with st.form("login_form"):
        user = st.text_input("Username", key="username")
        password = st.text_input("Password", key="password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        try:
            st.session_state["client"] = APIClient(username=user, password=password)
            st.rerun()
        except OasisException as _:
            st.error("Authentication Error")
