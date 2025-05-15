"""
This file allows for creating a sidebar based on UI config.
"""

import streamlit as st
import json

def SidebarNav():
    """Generate the sidebar as configured by the `ui-config.json`."""
    with st.sidebar:
        if "client" in st.session_state:
            with open("ui-config.json", "r") as f:
                config = json.load(f)

            pages_config = config['pages']

            for page_config in pages_config:
                st.page_link(page_config['path'], label=page_config['label'])
        else:
            st.page_link('app.py', label="Login")
    # Add logo
    st.logo(image="images/oasis_logo_bg.png",
            size="large")

