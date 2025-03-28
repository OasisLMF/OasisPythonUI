import streamlit as st
import pandas as pd
from modules.nav import SidebarNav
from modules.client import ClientInterface
from modules.validation import LenValidation, NotNoneValidation, ValidationGroup
from pages.components.display import DataframeView

st.set_page_config(
    page_title = "Comparison",
    layout = "centered"
)

SidebarNav()

##########################################################################################
# Header
##########################################################################################

cols = st.columns([0.1, 0.8, 0.1])
with cols[1]:
    st.image("images/oasis_logo.png")

# Retrieve client
if "client" in st.session_state:
    client = st.session_state.client
    client_interface = ClientInterface(client)
else:
    st.switch_page("app.py")

analyses = sorted(client_interface.analyses.search(metadata={'status': 'RUN_COMPLETED'}), key=lambda x: x['id'], reverse=True)

analyses = pd.DataFrame(analyses)
analyses = analyses[['name', 'id', 'portfolio', 'model']]
analyses = analyses.rename(columns={'id':'analysis_id'})

portfolios = client_interface.portfolios.get()
portfolios = pd.DataFrame(portfolios)[['id', 'name']]
portfolios = portfolios.rename(columns={'name': 'portfolio_name'})

models = client_interface.models.get()
models = pd.DataFrame(models)[['id', 'supplier_id', 'model_id']]

analyses = pd.merge(left=analyses, right=portfolios, how='left', left_on='portfolio', right_on='id')
analyses = pd.merge(left=analyses, right=models, how='left', left_on='model', right_on='id')
analyses = analyses[['analysis_id', 'name', 'portfolio_name', 'model_id', 'supplier_id']]

analyses_view = DataframeView(analyses, selectable='multi',
                              display_cols=['name', 'portfolio_name', 'model_id', 'supplier_id'])
selected = analyses_view.display()

validations = ValidationGroup()
none_validation = NotNoneValidation()
none_validation.message = 'Select 2 analyses.'
validations.add_validation(none_validation, selected)
len_validation = LenValidation()
len_validation.message = 'Select 2 analyses.'
validations.add_validation(len_validation, selected, 2)

if not validations.is_valid():
    st.info(validations.message)
    st.stop()

