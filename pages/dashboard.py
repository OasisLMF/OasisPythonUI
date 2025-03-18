import streamlit as st
from modules.client import ClientInterface
from modules.nav import SidebarNav
import pandas as pd
import altair as alt

from pages.components.output import generate_eltcalc_fragment, generate_leccalc_fragment, generate_pltcalc_fragment, summarise_inputs, generate_aalcalc_fragment
from modules.visualisation import OutputVisualisationInterface

st.set_page_config(
    page_title = "Dashboard",
    layout = "centered"
)

SidebarNav()

# Embed Logo
cols = st.columns([0.1, 0.8, 0.1])
with cols[1]:
    st.image("images/oasis_logo.png")

# Retrieve client
if "client" in st.session_state:
    client = st.session_state.client
    client_interface = ClientInterface(client)
else:
    st.switch_page("app.py")

analyses = sorted(client_interface.analyses.search(metadata={'status': 'RUN_COMPLETED'}), key=lambda x: x['id'], reverse=True)
selected_analysis = st.selectbox("Select Analysis", options=analyses,
                        format_func= lambda x : x['name'], index=None)

if selected_analysis is None:
    st.stop()

analysis_id = selected_analysis['id']

@st.cache_data
def get_analysis_inputs(ID):
    return client_interface.analyses.get_file(analysis_id, 'input_file', df=True)

with st.spinner("Loading data..."):
    inputs = get_analysis_inputs(analysis_id)
    settings = client.analyses.settings.get(analysis_id).json()

st.write("# Analysis Summary")
with st.spinner('Loading analysis summary...'):
    summarise_inputs(inputs.get('location.csv', None), settings)

@st.cache_data
def get_analysis_outputs(ID):
    return client_interface.analyses.get_file(ID, 'output_file', df=True)

with st.spinner("Loading data..."):
    outputs = get_analysis_outputs(analysis_id)

# Set up visualisation interface
vis = OutputVisualisationInterface(outputs)
perspectives = ['gul', 'il', 'ri']
for p in perspectives:
    p_oed_fields = settings.get(f'{p}_summaries', [{}])[0].get('oed_fields', None)
    if p_oed_fields:
        vis.set_oed_fields(p, p_oed_fields)

st.write("# Output Visualisation")
with st.spinner("Loading visualisations..."):
    for p in perspectives:
        if not settings.get(f'{p}_output', False):
            continue

        st.write(f'## {p.upper()}')

        summaries_settings = settings.get(f'{p}_summaries', [{}])[0]

        if summaries_settings.get('eltcalc', False):
            elt_expander = st.expander("ELT Output")
            with elt_expander:
                locations = None
                if inputs:
                    locations = inputs.get('location.csv')
                generate_eltcalc_fragment(p, vis, locations=locations, map=True)

        if summaries_settings.get('aalcalc', False):
            aal_expander = st.expander("AAL Output")
            with aal_expander:
                generate_aalcalc_fragment(p, vis)

        if summaries_settings.get('lec_output', False):
            lec_expander = st.expander("LEC Output")
            with lec_expander:
                lec_options = summaries_settings.get('leccalc')
                generate_leccalc_fragment(p, vis, lec_options)

        if summaries_settings.get("pltcalc", False):
            plt_expander = st.expander("PLT Output")
            with plt_expander:
                generate_pltcalc_fragment(p, vis)
