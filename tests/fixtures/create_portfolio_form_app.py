'''
Standalone script for AppTest coverage of `create_portfolio_form`.

On the Analyses page the form lives inside an `st.dialog`, which AppTest
closes on every full rerun, so the form is exercised on its own here. The
returned form data is stored in `session_state['form_data']`.
'''
import streamlit as st

from pages.components.create import create_portfolio_form

form_data = create_portfolio_form()
if form_data is not None:
    st.session_state['form_data'] = form_data
