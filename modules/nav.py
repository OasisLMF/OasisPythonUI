from modules.config import retrieve_ui_config
from modules.authorisation import logout, get_auth_type
import streamlit as st

ui_config = retrieve_ui_config()


def SidebarNav(no_client=False):

    with st.sidebar:
        if "client_interface" in st.session_state or no_client:
            for page_config in ui_config.pages:
                st.page_link(page_config['path'], label=page_config['label'])
            if "client_interface" in st.session_state:
                if get_auth_type() != 'simple':
                    id_token = st.session_state.get("id_token", "")
                    st.html(f'<form action="/api/oidc/logout/" style="margin:0">'
                            f'<input type="hidden" name="id_token_hint" value="{id_token}">'
                            '<button type="submit" style="width:100%">Logout</button></form>')
                else:
                    if st.button("Logout", width='stretch'):
                        logout()
        else:
            st.page_link('app.py', label="Login")
    # Add logo
    st.logo(image="images/oasis_logo_bg.png",
            size="large")
