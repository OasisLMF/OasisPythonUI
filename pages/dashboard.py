import streamlit as st
from modules.nav import SidebarNav
from modules.client import get_client
import pandas as pd
import altair as alt

st.set_page_config(
    page_title = "Dashboard",
    layout = "centered"
)

SidebarNav()

client = get_client()

"# OasisLMF UI"

@st.cache_data
def search_client_endpoint(endpoint, metadata={}):
    analyses = getattr(client, endpoint).search(metadata).json()
    return analyses

def format_analysis(analysis):
    return f'{analysis["id"]}: {analysis["name"]}'

analyses = search_client_endpoint('analyses', metadata={"status":"RUN_COMPLETED"})
analysis = st.selectbox("Select Analysis", options=analyses, format_func=format_analysis, index=None)

@st.cache_data
def summarise_inputs(inputs_dict):
    input_summary = {'Specification': [],
                     'Value': []}
    # Locations
    input_summary['Specification'].append('Location count')
    input_summary['Value'].append(len(inputs_dict["keys.csv"]["LocID"].unique()))

    # Total TIV
    input_summary['Specification'].append('total TIV')
    input_summary['Value'].append(inputs_dict['coverages.csv']['tiv'].sum())

    return pd.DataFrame(input_summary)

def add_info_summary(df, spec, value):
    df["Specification"].append(spec)
    df["Value"].append(value)
    return df

@st.cache_data
def get_analysis_settings(id):
    return client.analyses.settings.get(id).json()

@st.cache_data
def summarise_model(settings):
    model_summary = {"Specification": [], "Value": []}

    model_summary = add_info_summary(model_summary, "Model Name", settings["model_name_id"])
    model_summary = add_info_summary(model_summary, "Model Supplier", settings["model_supplier_id"])

    return pd.DataFrame(model_summary)

@st.cache_data
def summarise_model_settings(settings):
    settings_summary = {"Specification": [], "Value": []}

    model_settings = settings.get("model_settings", None)

    if model_settings is None:
        return None

    for k, v in model_settings.items():
        k = k.replace('_', ' ').title()
        settings_summary = add_info_summary(settings_summary, k, v)
    return settings_summary
type_dict = {1: "Analytical", 2: "Sample"}

@st.cache_data
def summarise_outputs(outputs_dict):
    aalcalc_keys = [k for k in outputs_dict.keys() if 'S1_aalcalc' in k]

    output_summary = {"component": [], "perspective": [], "type": [],  "value": []}

    component = "AAL"

    for aal_key in aalcalc_keys:
        curr_summary = outputs_dict[aal_key].groupby(["type"])["mean"].sum()
        for t in type_dict:
            output_summary["component"].append(component)
            output_summary["perspective"].append(aal_key.split('_')[0])
            output_summary["type"].append(type_dict[t])
            output_summary["value"].append(curr_summary.loc[t])

    return pd.DataFrame(output_summary)

@st.cache_data
def view_output_summary(output_summary):
    def combine_cols(row):
        return f'{row["component"]} {row["perspective"]} ({row["type"]})'

    output_summary['specification'] = output_summary.apply(combine_cols, axis=1)
    return output_summary[['specification', 'value']]

@st.cache_data
def get_outputs(id):
    return client.analyses.output_file.get_dataframe(id)

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if analysis:
        "### Input Summary"
        inputs_dict = client.analyses.input_file.get_dataframe(analysis["id"])
        input_summary = summarise_inputs(inputs_dict)
        st.dataframe(input_summary, hide_index=True, use_container_width=True)

with col2:
    if analysis:
        "### Model Summary"
        settings = get_analysis_settings(analysis["id"])
        model_summary = summarise_model(settings)
        settings_summary = summarise_model_settings(settings)

        "Basic Info"
        st.dataframe(model_summary, hide_index=True, use_container_width=True)

        "Model Settings"
        st.dataframe(settings_summary, hide_index=True, use_container_width=True)

with col3:
    if analysis:
        "### Ouput Summary"
        outputs_dict = get_outputs(analysis["id"])
        output_summary = summarise_outputs(outputs_dict)
        output_view = view_output_summary(output_summary)
        st.dataframe(output_view.style.format(precision=0, thousands=','),
                     hide_index=True, use_container_width=True)


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

if analysis:
    '## Graphs'
    "### AAL Plots"
    outputs_dict = get_outputs(analysis["id"])
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

    gul_oep_df = outputs_dict[leccalc_dict['gul']['oep']]
    gul_aep_df = outputs_dict[leccalc_dict['gul']['aep']]
    gul_data = leccalc_plot_data(gul_oep_df, gul_aep_df)

    il_oep_df = outputs_dict[leccalc_dict['il']['oep']]
    il_aep_df = outputs_dict[leccalc_dict['il']['aep']]
    il_data = leccalc_plot_data(il_oep_df, il_aep_df)

    ri_oep_df = outputs_dict[leccalc_dict['ri']['oep']]
    ri_aep_df = outputs_dict[leccalc_dict['ri']['aep']]
    ri_data = leccalc_plot_data(ri_oep_df, ri_aep_df)

    gul_chart = alt.Chart(gul_data, title='GUL EP Sample').mark_line(point=True)
    gul_chart = gul_chart.encode(x=alt.X('return_period').scale(type="log"),
                                 y='loss', color='ep_type')
    st.altair_chart(gul_chart, use_container_width=True)

    il_chart = alt.Chart(il_data, title='IL EP Sample').mark_line(point=True)
    il_chart = il_chart.encode(x=alt.X('return_period').scale(type="log"),
                               y='loss', color='ep_type')
    st.altair_chart(il_chart, use_container_width=True)

    ri_chart = alt.Chart(ri_data, title='RI EP Sample').mark_line(point=True)
    ri_chart = ri_chart.encode(x=alt.X('return_period').scale(type="log"),
                               y='loss', color='ep_type')
    st.altair_chart(ri_chart, use_container_width=True)
