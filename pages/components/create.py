# Module to display ui components for running analyses
from oasis_data_manager.errors import OasisException
import streamlit as st
from modules.validation import validate_name, validate_not_none
import time

def create_analysis_form(portfolios, models, client):
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
            # todo: add validation requiring name
            validations = []
            validations.append(validate_name(name))
            validations.append(validate_not_none(portfolio, 'Porfolio'))
            validations.append(validate_not_none(model, 'Model'))

            if all([v[0] for v  in validations]):
                try:
                    client.create_analysis(portfolio_id=int(portfolio["id"]), model_id=int(model["id"]),
                                           analysis_name=name)
                    st.success("Analysis created")
                    time.sleep(0.5) # Briefly display the message
                    st.rerun()
                except OasisException as e:
                    st.error(e)
            else:
                for v in validations:
                    if v[0] is False:
                        st.error(v[1])
                submitted = False
