from requests.models import HTTPError
from modules.client import ClientInterface
from modules.nav import SidebarNav
import streamlit as st

st.set_page_config(
    page_title = "Summary Levels",
    layout = "centered"
)

SidebarNav()

def page():
    if "client" in st.session_state:
        client = st.session_state.client
        ci = ClientInterface(client)
    else:
        st.switch_page("app.py")
        return

    analysis = ci.analyses.get()[0]
    model_id = analysis['model']

    model = ci.models.get(model_id)

    try:
        model_settings = ci.models.settings.get(model_id)
    except HTTPError as e:
        st.write("Could not load model settings")
        st.error(e)
        model_settings = None

    st.write(model_settings)

    try:
        analysis_settings = ci.analyses.settings.get(analysis['id'])
    except HTTPError as e:
        st.write("Could not load analysis settings")
        st.error(e)
        analysis_settings = None

    st.write(analysis_settings)


page()
