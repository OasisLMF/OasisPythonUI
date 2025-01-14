import streamlit as st
import pandas as pd
from oasislmf.platform_api.client import APIClient

@st.cache_resource
def get_client(username="admin", password="password"):
    return APIClient(username=username, password=password)

def check_analysis_status(client, id, required_status):
    curr_status = client.analyses.get(id).json()['status']
    return curr_status == required_status

def get_portfolios(client):
    resp = client.portfolios.get().json()
    return pd.json_normalize(resp)

def get_analyses(client):
    analyses = client.analyses.get().json()
    return pd.json_normalize(analyses)
