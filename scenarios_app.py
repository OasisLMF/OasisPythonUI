"""Public, credential-free Scenarios app.

Run with `streamlit run scenarios_app.py`. Visitors can explore pre-loaded
disaster scenarios against pre-loaded exposure, run them (within limits),
and view results; they cannot upload data. Only the pages registered below
exist in this app: `st.navigation` replaces the `pages/` directory used by
the standard UI, so none of its pages (uploads, deletes, ...) are reachable.
"""
import logging

import streamlit as st
from requests.exceptions import HTTPError

from modules.authorisation import quiet_login
from modules.config import retrieve_ui_config
from modules.scenarios import VISITOR_PARAM, visitor_id

logger = logging.getLogger(__name__)

st.set_page_config(page_title='Oasis Scenarios', page_icon='images/oasis_logo.png', layout='wide')

ui_config = retrieve_ui_config()

# Credential free: the app uses its service account for every visitor
try:
    quiet_login()
except HTTPError as e:
    logger.error(f'Scenarios login failed: {e}')
if 'client_interface' not in st.session_state:
    st.error('The scenarios service is unavailable right now. Please try again later.')
    st.stop()

vid = visitor_id()

st.logo('images/oasis_logo_bg.png', size='large')
st.html('''<style>
    [data-testid="stSidebarLogo"], [data-testid="stHeaderLogo"] { height: 3rem; max-width: 100%; }
</style>''')

pages = [
    st.Page('scenarios_ui/explore.py', title='Run a scenario', icon=':material/play_circle:', default=True),
    st.Page('scenarios_ui/showcase.py', title='Showcase', icon=':material/auto_awesome:'),
    st.Page('scenarios_ui/compare.py', title='Compare', icon=':material/compare_arrows:'),
    st.Page('scenarios_ui/guide.py', title='Guide', icon=':material/menu_book:'),
]
# Links drawn explicitly: the shared Streamlit config hides the built-in page menu
page = st.navigation(pages, position='hidden')
with st.sidebar:
    for p in pages:
        # Carry the visitor id so a reload on any page keeps the visitor's runs
        st.page_link(p, query_params={VISITOR_PARAM: vid})
page.run()
