import streamlit as st
from modules.nav import SidebarNav
from modules.client import APIClient
from oasis_data_manager.errors import OasisException
from modules.validation import validate_name, process_validations
import json

st.set_page_config(
        page_title = "OasisLMF",
        layout="centered"
)

SidebarNav()

"# OasisLMF UI"

if "client" in st.session_state:
    with open("ui-config.json", "r") as f:
        config = json.load(f)
    st.write("Logged in")
    post_login_page = config.get("post_login_page", None)
    if post_login_page:
        st.switch_page(post_login_page)
else:
    st.write("## Login")
    with st.form("login_form"):
        user = st.text_input("Username", key="username")
        password = st.text_input("Password", key="password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        validations = [[validate_name, (user, "Username")],
                       [validate_name, (password, "Password")]]

        valid, msg = process_validations(validations)

        if valid:
            try:
                st.session_state["client"] = APIClient(username=user, password=password)
                st.rerun()
            except OasisException as _:
                st.error("Authentication Failed")
        else:
            st.error(msg)
