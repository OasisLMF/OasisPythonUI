import streamlit as st
from oasislmf.platform_api.client import APIClient

@st.cache_resource
def get_client():
    return APIClient()
