# Module to display ui components for running analyses
import streamlit as st
from modules.validation import NameValidation, NotNoneValidation, ValidationError, ValidationGroup

def create_analysis_form(portfolios, models):
    """Analysis creation form ui component."""

    def list_empty(lst):
        if len(lst) == 0:
            return True
        if all(e is None for e in lst):
            return True
        return False

    if list_empty(portfolios) or list_empty(models):
        st.write("Ensure portfolios and models are loaded")
        return None

    def format_portfolio(portfolio):
        return f"{portfolio['name']}"

    def format_model(model):
        return f"{model['model_id']} {model['run_mode']} {model['supplier_id']}"

    with st.form("create_analysis_form", clear_on_submit=True, enter_to_submit=False):
        name = st.text_input("Analysis Name")

        selected_port = 0 if len(portfolios) == 1 else None
        portfolio = st.selectbox('Select Portfolio', options=portfolios,
                                 index=selected_port, format_func=format_portfolio)

        selected_model = 0 if len(models) == 1 else None
        model = st.selectbox('Select Model', options=models,
                             index=selected_port, format_func=format_model)

        submitted = st.form_submit_button("Create Analysis")

    if submitted:
        val_group = ValidationGroup()
        val_group.add_validation(NameValidation('Name'), name)
        val_group.add_validation(NotNoneValidation('Portfolio'), portfolio)
        val_group.add_validation(NotNoneValidation('Model'), model)

        try:
            val_group.validate()
            return {'name': name, 'model_id': int(model['id']), 'portfolio_id': int(portfolio['id'])}
        except ValidationError as e:
            st.error(e)
    return None
