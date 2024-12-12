import streamlit as st
from oasislmf.platform_api.client import APIClient
import pandas as pd

st.markdown("# OasisLMF UI")

@st.cache_resource
def get_client():
    return APIClient()

client = get_client()

st.markdown("## Portfolios")

portfolios = client.portfolios.get().json()
portfolios =  pd.json_normalize(portfolios)
portfolios['created'] = pd.to_datetime(portfolios['created'])
portfolios['modified'] = pd.to_datetime(portfolios['modified'])

@st.cache_data
def generate_column_config(col_names):
    columns = [
        'id',
        'name',
        'created',
        'modified',
        'storage_links',
    ]

    config = {name: None for name in col_names}
    for c in columns:
        config[c] = c.replace('_', ' ').title()
    return config

column_config = generate_column_config(portfolios.columns.values)
column_config['created'] = st.column_config.DatetimeColumn(column_config['created'],
                                                           format="DD/MM/YY HH:mm:ss")
column_config['modified'] = st.column_config.DatetimeColumn(column_config['modified'],
                                                           format="DD/MM/YY HH:mm:ss")

st.dataframe(portfolios, hide_index=True, column_config=column_config)
