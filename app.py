import streamlit as st
from modules.client import ClientInterface
from modules.nav import SidebarNav
from oasis_data_manager.errors import OasisException
from modules.validation import NameValidation, ValidationError, ValidationGroup
import json

st.set_page_config(
        page_title = "OasisLMF",
        layout="centered"
)

SidebarNav()

cols = st.columns([0.1, 0.8, 0.1])
with cols[1]:
    st.image(image="images/oasis_logo.png")

if "client" in st.session_state:
    with open("ui-config.json", "r") as f:
        config = json.load(f)
    st.write("Logged in")
    post_login_page = config.get("post_login_page", None)
    if post_login_page:
        st.switch_page(post_login_page)
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

        if valid:
            try:
                client_interface = ClientInterface(username=user, password=password)
                st.session_state["client"] = client_interface.client
                st.session_state["client_interface"] = client_interface
                st.rerun()
            except OasisException as _:
                st.error("Authentication Failed")
        else:
            st.error(msg)
