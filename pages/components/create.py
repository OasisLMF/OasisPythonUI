# Module to display ui components for running analyses
import streamlit as st
from modules.validation import NameValidation, NotNoneValidation, ValidationError, ValidationGroup

def create_analysis_form(portfolios, models):
    """Analysis creation form ui component."""

    def format_portfolio(portfolio):
        return f"{portfolio['id']}: {portfolio['name']}"

    def format_model(model):
        return f"{model['id']}: {model['model_id']}{model['version_id']} {model['supplier_id']}"

    with st.form("create_analysis_form", clear_on_submit=True, enter_to_submit=False):
        name = st.text_input("Analysis Name")

        if len(portfolios) > 1:
            portfolio = st.selectbox('Select Portfolio', options=portfolios,
                                     index=None, format_func=format_portfolio)
        else:
            portfolio = portfolios[0]

        if len(models) > 1:
            # model = display_select_models(models)
            model = st.selectbox('Select Model', options=models,
                                 index=None, format_func=format_model)
        else:
            model = models[0]

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
