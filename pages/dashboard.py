import streamlit as st
from modules.client import ClientInterface
from modules.nav import SidebarNav
import pandas as pd
import altair as alt

from pages.components.output import generate_eltcalc_fragment, summarise_inputs
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
summarise_inputs(inputs.get('location.csv', None), settings)

@st.cache_data
def leccalc_plot_data(oep_df, aep_df):
    oep_df['ep_type'] = 'oep'
    aep_df['ep_type'] = 'aep'

    # Filter only sampled
    oep_df = oep_df[oep_df['type'] == 2]
    aep_df = aep_df[aep_df['type'] == 2]

    # Extract relevent columns
    oep_df = oep_df[['return_period', 'loss', 'ep_type']]
    aep_df = aep_df[['return_period', 'loss', 'ep_type']]
    return pd.concat([oep_df, aep_df], axis=0)

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
st.write("## eltcalc output")
for p in perspectives:
    if not settings.get(f'{p}_output', False):
        continue
    summaries_settings = settings.get(f'{p}_summaries', [{}])[0]
    if summaries_settings.get('eltcalc', False):
        st.write(f'### {p.upper()}')
        locations = None
        if inputs:
            locations = inputs.get('location.csv')
        generate_eltcalc_fragment(p, vis, locations=locations, map=True)

st.stop()
if selected_analysis:
    '## Graphs'
    "### AAL Plots"
    outputs_dict = get_outputs(selected_analysis["id"])
    output_summary = summarise_outputs(outputs_dict)
    bar_data = output_summary[['perspective', 'type', 'value']]
    bar_chart = alt.Chart(bar_data).mark_bar().encode(x=alt.X('perspective:N'),
                                                      xOffset="type:N",
                                                      y=alt.Y('value'),
                                                      color='type:N')

    st.altair_chart(bar_chart, use_container_width=True)


    "### EP Sample Plots"

    leccalc_dict = {'gul': {'aep': None, 'oep': None},
                    'ri': {'aep': None, 'oep': None},
                    'il': {'aep': None, 'oep': None}}
    for k in outputs_dict.keys():
        if 'S1_leccalc_full_uncertainty' in k:
            k_split = k.split('.')[0].split('_')
            leccalc_dict[k_split[0]][k_split[-1]] = k


    @st.cache_data
    def plot_output(outputs_dict, perspective):
        oep_key = leccalc_dict[perspective]['oep']
        aep_key = leccalc_dict[perspective]['aep']
        if oep_key is not None and aep_key is not None:
            oep_df = outputs_dict[oep_key]
            aep_df = outputs_dict[aep_key]
            data = leccalc_plot_data(oep_df, aep_df)

            chart = alt.Chart(data, title=f'{perspective.upper()} EP Sample').mark_line(point=True)
            chart = chart.encode(x=alt.X('return_period').scale(type="log"),
                                 y='loss', color='ep_type')
            return chart
        return None


    gul_chart = plot_output(outputs_dict, 'gul')
    if gul_chart:
        st.altair_chart(gul_chart, use_container_width=True)

    il_chart = plot_output(outputs_dict, 'il')
    if il_chart:
        st.altair_chart(il_chart, use_container_width=True)

    ri_chart = plot_output(outputs_dict, 'ri')
    if ri_chart:
        st.altair_chart(ri_chart, use_container_width=True)
