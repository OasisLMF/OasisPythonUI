import streamlit as st
from modules.nav import SidebarNav
from modules.client import get_portfolios, get_analyses, get_models
from pages.components.display import DataframeView
from pages.components.create import create_analysis_form
from modules.validation import process_validations, validate_not_none

st.set_page_config(
    page_title = "IDF Demo",
    layout = "centered"
)

SidebarNav()

"# OasisLMF UI - IDF Demo"

if "client" in st.session_state:
    client = st.session_state.client
else:
    st.switch_page("app.py")

'## Portfolios'

datetime_cols = ['created', 'modified']
display_cols = [ 'id', 'name', 'created', 'modified', ]

portfolios = get_portfolios(client)
portfolio_view = DataframeView(portfolios, display_cols=display_cols, selectable=True)
portfolio_view.convert_datetime_cols(datetime_cols)
selected_portfolio = portfolio_view.display()

'## Models'
models = get_models(client)
display_cols = ['id', 'supplier_id', 'model_id', 'version_id', 'created', 'modified']
datetime_cols = ['created', 'modified']

model_view = DataframeView(models, selectable=True, display_cols=display_cols)
model_view.convert_datetime_cols(datetime_cols)
selected_model = model_view.display()

validations_list = [(validate_not_none, [selected_portfolio, 'Portfolio']),
                    (validate_not_none, [selected_model, 'Model'])]
enable_popover, msg = process_validations(validations_list)

with st.popover("Create Analysis", disabled=not enable_popover, help=msg):
    create_analysis_form(portfolios=[selected_portfolio], models=[selected_model], client=client)


'## Analyses'
analyses = get_analyses(client)
display_cols = [ 'id', 'name', 'portfolio', 'model', 'created', 'modified',
                'status' ]
datetime_cols = ['created', 'modified']

analyses_view = DataframeView(analyses, display_cols=display_cols)
analyses_view.convert_datetime_cols(datetime_cols)
analyses_view.display()
