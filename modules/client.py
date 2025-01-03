import streamlit as st
from oasislmf.platform_api.client import APIClient

@st.cache_resource
def get_client(username="admin", password="password"):
    return APIClient(username=username, password=password)

def check_analysis_status(client, id, required_status):
    curr_status = client.analyses.get(id).json()['status']
    return curr_status == required_status
