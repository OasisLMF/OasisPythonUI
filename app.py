import streamlit as st
from oasislmf.platform_api.client import APIClient
import pandas as pd

"# OasisLMF UI"

@st.cache_resource
def get_client():
    return APIClient()

client = get_client()

"## Portfolios"

@st.cache_data
def convert_datetime_cols(df, cols):
    for c in cols:
        df[c] = pd.to_datetime(df[c])
    return df

portfolios = client.portfolios.get().json()
portfolios =  pd.json_normalize(portfolios)

date_time_cols = ['created', 'modified']
portfolios = convert_datetime_cols(portfolios, date_time_cols)

@st.cache_data
def generate_column_config(col_names, display_cols, date_time_cols=None):
    config = {name: None for name in col_names}
    for c in display_cols:
        config[c] = c.replace('_', ' ').title()

    if date_time_cols is None:
        return config

    for c in date_time_cols:
        config[c] = st.column_config.DatetimeColumn(config[c],
                                                    format="DD/MM/YY HH:mm:ss")

    return config

display_cols = [
    'id',
    'name',
    'created',
    'modified',
    'storage_links',
]
column_config = generate_column_config(portfolios.columns.values, display_cols,
                                       date_time_cols=date_time_cols)

st.dataframe(portfolios, hide_index=True, column_config=column_config, column_order=display_cols)

"## Analyses"

analyses = client.analyses.get().json()
analyses = pd.json_normalize(analyses)
analyses = convert_datetime_cols(analyses, date_time_cols)

# Following need to be combined with other df
# - Portfolio Name
# - Model Version
# - Supplier
# - Created
# - Modified
# - Status Details
# - Status

display_cols = [
    'id', 'name', 'portfolio', 'model', 'created', 'modified', 'status'
]

column_config = generate_column_config(analyses.columns.values, display_cols,
                                       date_time_cols=date_time_cols)

st.dataframe(analyses, hide_index=True, column_config=column_config, column_order=display_cols)
