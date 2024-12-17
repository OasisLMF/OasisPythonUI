import streamlit as st
from modules.nav import SidebarNav
from modules.client import get_client
import pandas as pd
import altair as alt

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

"## Input Summary"
if analysis:
    inputs_dict = client.analyses.input_file.get_dataframe(analysis["id"])
    input_summary = summarise_inputs(inputs_dict)
    st.dataframe(input_summary, hide_index=True)

"## Model Summary"
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



if analysis:
    settings = get_analysis_settings(analysis["id"])
    model_summary = summarise_model(settings)
    settings_summary = summarise_model_settings(settings)

    "Basic Info"
    st.dataframe(model_summary, hide_index=True)

    "Model Settings"
    st.dataframe(settings_summary, hide_index=True)

"## Ouput Summary"

@st.cache_data
def summarise_outputs(outputs_dict):
    aalcalc_keys = [k for k in outputs_dict.keys() if 'S1_aalcalc' in k]

    output_summary = {"component": [], "perspective": [], "type": [],  "value": []}

    component = "AAL"
    types = [1, 2]

    for aal_key in aalcalc_keys:
        curr_summary = outputs_dict[aal_key].groupby(["type"])["mean"].sum()
        for t in types:
            output_summary["component"].append(component)
            output_summary["perspective"].append(aal_key.split('_')[0])
            output_summary["type"].append(t)
            output_summary["value"].append(curr_summary.loc[t])

    return pd.DataFrame(output_summary)

@st.cache_data
def view_output_summary(output_summary):
    type_dict = {1: "(Analytical)", 2: "(Sample)"}
    def combine_cols(row):
        return f'{row["component"]} {row["perspective"]} {type_dict[row["type"]]}'

    output_summary['specification'] = output_summary.apply(combine_cols, axis=1)
    return output_summary[['specification', 'value']]


@st.cache_data
def get_outputs(id):
    return client.analyses.output_file.get_dataframe(id)

if analysis:
    outputs_dict = get_outputs(analysis["id"])
    output_summary = summarise_outputs(outputs_dict)
    output_view = view_output_summary(output_summary)
    st.dataframe(output_view.style.format(precision=0, thousands=','),
                 hide_index=True)

"## AAL Summary"

if analysis:
    bar_data = output_summary[['perspective', 'type', 'value']]
    type_dict = {1: "Analytical", 2: "Sample"}
    bar_data['type'] = bar_data['type'].apply(lambda x: type_dict[x])
    bar_chart = alt.Chart(bar_data).mark_bar().encode(x=alt.X('perspective:N'),
                                                      xOffset="type:N",
                                                      y=alt.Y('value'),
                                                      color='type:N')

    st.altair_chart(bar_chart)
