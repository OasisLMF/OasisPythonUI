"""
This file allows for creating a sidebar based on UI config.
"""
from modules.config import retrieve_ui_config
import streamlit as st

ui_config = retrieve_ui_config()

def SidebarNav():
    """Generate the sidebar as configured by the `ui-config.json`."""
    with st.sidebar:
        if "client_interface" in st.session_state:
            for page_config in ui_config.pages:
                st.page_link(page_config['path'], label=page_config['label'])
        else:
            st.page_link('app.py', label="Login")
    # Add logo
    st.logo(image="images/oasis_logo_bg.png",
            size="large")


