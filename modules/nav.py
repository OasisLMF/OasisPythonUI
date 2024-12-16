import streamlit as st

def SidebarNav():
    with st.sidebar:
        st.page_link('app.py', label="Home")
        st.page_link('pages/analyses.py', label="Analyses")
        st.page_link('pages/dashboard.py', label="Dashboard")
