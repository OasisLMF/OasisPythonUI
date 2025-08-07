from modules.config import retrieve_ui_config
import streamlit as st
from modules.client import ClientInterface
from modules.nav import SidebarNav
from modules.authorisation import validate_page
import pandas as pd
import altair as alt

from pages.components.footer import generate_footer
from pages.components.output import generate_alt_fragment, generate_eltcalc_fragment, generate_qplt_fragment
from pages.components.output import generate_leccalc_fragment, generate_melt_fragment, generate_mplt_fragment
from pages.components.output import generate_pltcalc_fragment, generate_qelt_fragment, summarise_inputs
from pages.components.output import generate_aalcalc_fragment, generate_ept_fragment
from modules.visualisation import OutputInterface

st.set_page_config(
    page_title = "Dashboard",
    layout = "centered"
)

validate_page("Dashboard")

ui_config = retrieve_ui_config()
handle_login(ui_config.skip_login)

client_interface = st.session_state["client_interface"]
client = client_interface.client

SidebarNav()

# Embed Logo
cols = st.columns([0.1, 0.8, 0.1])
with cols[1]:
    st.image("images/oasis_logo.png")

analyses = sorted(client_interface.analyses.search(metadata={'status': 'RUN_COMPLETED'}), key=lambda x: x['id'], reverse=True)
selected_analysis = st.selectbox("Select Analysis", options=analyses,
                        format_func= lambda x : x['name'], index=None)

if selected_analysis is None:
    generate_footer(ui_config)
    st.stop()

analysis_id = selected_analysis['id']

@st.cache_data
def get_analysis_inputs(ID):
    return client_interface.analyses.get_file(ID, 'input_file', df=True)

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
vis = OutputInterface(outputs)
perspectives = ['gul', 'il', 'ri']
for p in perspectives:
    p_oed_fields = settings.get(f'{p}_summaries', [{}])[0].get('oed_fields', None)
    if p_oed_fields:
        vis.set_oed_fields(p, p_oed_fields)

st.write("# Output")
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

        # Handle ORD outputs

        ord_settings = summaries_settings.get("ord_output", {})

        if ord_settings.get("elt_moment", False):
            expander = st.expander("MELT Output")
            with expander:
                locations = None
                if inputs:
                    locations = inputs.get('location.csv')
                generate_melt_fragment(p, vis, locations=locations)

        if ord_settings.get('elt_quantile', False):
            expander = st.expander("QELT Output")
            with expander:
                generate_qelt_fragment(p, vis, locations=locations)

        if ord_settings.get("plt_moment", False):
            expander = st.expander("MPLT Output")
            with expander:
                generate_mplt_fragment(p, vis)

        if ord_settings.get("plt_quantile", False):
            expander = st.expander("QPLT Output")
            with expander:
                generate_qplt_fragment(p, vis)

        if ord_settings.get("alt_meanonly", False):
            expander = st.expander("ALT MeanOnly")
            with expander:
                generate_alt_fragment(p, vis, 'alt_meanonly')

        if ord_settings.get("alt_period", False):
            expander = st.expander("PALT")
            with expander:
                generate_alt_fragment(p, vis, 'alt_period')

        ept_settings = [
            'ept_full_uncertainty_aep',
            'ept_full_uncertainty_oep',
            'ept_mean_sample_aep',
            'ept_mean_sample_oep',
            'ept_per_sample_mean_aep',
            'ept_per_sample_mean_oep'
        ]

        ept_outputs = [e for e in ept_settings if ord_settings.get(e, False)]

        if any([ord_settings.get(e, False) for e in ept_settings]):
            expander = st.expander("EPT Output")
            with expander:
                generate_ept_fragment(p, vis)

generate_footer(ui_config)
