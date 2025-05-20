from requests.models import HTTPError
from modules.client import ClientInterface
from modules.nav import SidebarNav
from pages.components.create import ViewSummarySettings, create_analysis_settings
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
    st.write(analysis)
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

    # Try and retrieve oed group fields from model settings
    oed_fields = model_settings.get('data_settings', {}).get('damage_group_fields', [])
    oed_fields.extend(model_settings.get('data_settings', {}).get('hazard_group_fields', []))
    oed_fields = list(set(oed_fields))

    st.write(oed_fields)

    output = create_analysis_settings(model, model_settings, oed_fields, initial_settings=analysis_settings)

    st.write("Form Output")
    st.write(output)

    ViewSummarySettings(analysis_settings['gul_summaries'])
page()
