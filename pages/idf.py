from oasis_data_manager.errors import OasisException
import streamlit as st
from modules.nav import SidebarNav
from modules.client import ClientInterface
from pages.components.display import DataframeView
from pages.components.create import create_analysis_form
from modules.validation import NotNoneValidation, ValidationError, ValidationGroup
import time

st.set_page_config(
    page_title = "IDF Demo",
    layout = "centered"
)

SidebarNav()

"# OasisLMF UI - IDF Demo"

if "client" in st.session_state:
    client = st.session_state.client
    client_interface = ClientInterface(client)
else:
    st.switch_page("app.py")

'## Create Analysis'
'#### Portfolio Selection'

datetime_cols = ['created', 'modified']
display_cols = [ 'id', 'name', 'created', 'modified', ]

portfolios = client_interface.portfolios.get(df=True)
portfolio_view = DataframeView(portfolios, display_cols=display_cols, selectable=True)
portfolio_view.convert_datetime_cols(datetime_cols)
selected_portfolio = portfolio_view.display()

'#### Model Selection'
models = client_interface.models.get(df=True)
display_cols = ['id', 'supplier_id', 'model_id', 'version_id', 'created', 'modified']
datetime_cols = ['created', 'modified']

model_view = DataframeView(models, selectable=True, display_cols=display_cols)
model_view.convert_datetime_cols(datetime_cols)
selected_model = model_view.display()

validations = ValidationGroup()
validations = validations.add_validation(NotNoneValidation("Portfolio"), selected_portfolio)
validations = validations.add_validation(NotNoneValidation("Model"), selected_model)

enable_popover = True
msg = None
try:
    validations.validate()
except ValidationError as e:
    msg = e.message
    enable_popover = False

with st.popover("Create Analysis", disabled=not enable_popover, help=msg):
    resp = create_analysis_form(portfolios=[selected_portfolio], models=[selected_model])
    if resp:
        try:
            client_interface.create_analysis(resp['portfolio_id'], resp['model_id'], resp['name'])
            st.success('Created analysis')
            time.sleep(0.5)
            st.rerun()
        except OasisException as e:
            st.error(e)


'## Run Analysis'
analyses = client_interface.analyses.get(df=True)
display_cols = [ 'id', 'name', 'portfolio', 'model', 'created', 'modified',
                'status' ]
datetime_cols = ['created', 'modified']

analyses_view = DataframeView(analyses, display_cols=display_cols)
analyses_view.convert_datetime_cols(datetime_cols)
analyses_view.display()
